"""
iv_vs_realized_directional.py

Extension of IV spike scanner:
 - Separates put vs call implied volatility.
 - Detects which side spiked more.
 - Evaluates whether call-IV spikes precede upward moves
   and put-IV spikes precede downward moves.
"""

from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import zscore
import matplotlib.pyplot as plt
from tqdm import tqdm

# ---------------- SETTINGS ----------------
TICKER = "AAPL"
START_DATE = "2025-09-10"
END_DATE = None
NEAR_ATM_STRIKE_WIDTH = 0.05
IV_HISTORY_WINDOW = 30
Z_SCORE_THRESHOLD = 2.0
FUTURE_WINDOW_DAYS = 5
MIN_OPTIONS_PER_DAY = 3
PLOT = True

# -------------- HELPERS -------------------
def fetch_underlying_history(ticker, start, end):
    t = yf.Ticker(ticker)
    hist = t.history(start=start, end=end, auto_adjust=False)
    hist = hist[['Close']].rename(columns={'Close': 'close'})
    hist.index = pd.to_datetime(hist.index)
    return hist

def snapshot_put_call_iv(ticker_obj, spot_price, width_pct=NEAR_ATM_STRIKE_WIDTH):
    """Return near-ATM median call IV and put IV."""
    try:
        exps = ticker_obj.options
    except Exception:
        return np.nan, np.nan
    call_ivs, put_ivs = [], []
    for exp in exps:
        try:
            chain = ticker_obj.option_chain(exp)
        except Exception:
            continue
        for side_df, side in [(chain.calls, "call"), (chain.puts, "put")]:
            if side_df is None or side_df.empty:
                continue
            df = side_df.copy()
            df["strike"] = pd.to_numeric(df["strike"], errors="coerce")
            if df["strike"].isnull().all():
                continue
            df["moneyness"] = (spot_price - df["strike"]) / spot_price
            df_sel = df[np.abs(df["moneyness"]) <= width_pct]
            if df_sel.empty:
                continue
            iv_col = "impliedVolatility" if "impliedVolatility" in df_sel.columns else None
            if not iv_col:
                continue
            iv_values = pd.to_numeric(df_sel[iv_col], errors="coerce").dropna().tolist()
            if side == "call":
                call_ivs.extend(iv_values)
            else:
                put_ivs.extend(iv_values)
    call_iv = np.median(call_ivs) if len(call_ivs) >= MIN_OPTIONS_PER_DAY else np.nan
    put_iv = np.median(put_ivs) if len(put_ivs) >= MIN_OPTIONS_PER_DAY else np.nan
    return call_iv, put_iv

def realized_return(price_series, start_idx, window_days):
    """Compute signed return over next N trading days."""
    idxs = price_series.index
    try:
        pos = idxs.get_loc(start_idx)
    except KeyError:
        return np.nan
    target_pos = pos + window_days
    if target_pos >= len(idxs):
        return np.nan
    start_price = price_series.iloc[pos]
    end_price = price_series.iloc[target_pos]
    return (end_price / start_price - 1.0)

# -------------- MAIN -------------------
def analyze_iv_directional(ticker=TICKER, start=START_DATE, end=END_DATE):
    # 1) prices
    price_df = fetch_underlying_history(ticker, start, end)
    t = yf.Ticker(ticker)

    # 2) build daily series of call IV & put IV
    records = {}
    for dt, row in tqdm(price_df.iterrows(), total=len(price_df), desc="Fetching IV"):
        spot = row["close"]
        call_iv, put_iv = snapshot_put_call_iv(t, spot)
        records[pd.Timestamp(dt).normalize()] = {"call_iv": call_iv, "put_iv": put_iv}
    iv_df = pd.DataFrame(records).T.sort_index()

    # 3) merge
    combined = price_df.join(iv_df)
    combined["iv_diff"] = combined["call_iv"] - combined["put_iv"]

    # 4) z-scores
    # rolling z-score = (x - mean) / std
    combined["call_iv_z"] = (
            (combined["call_iv"] - combined["call_iv"].rolling(IV_HISTORY_WINDOW).mean())
            / combined["call_iv"].rolling(IV_HISTORY_WINDOW).std()
    )

    combined["put_iv_z"] = (
            (combined["put_iv"] - combined["put_iv"].rolling(IV_HISTORY_WINDOW).mean())
            / combined["put_iv"].rolling(IV_HISTORY_WINDOW).std()
    )
    # 5) spikes
    combined["call_spike"] = combined["call_iv_z"] >= Z_SCORE_THRESHOLD
    combined["put_spike"]  = combined["put_iv_z"]  >= Z_SCORE_THRESHOLD

    # 6) future returns
    combined["future_return"] = [realized_return(combined["close"], dt, FUTURE_WINDOW_DAYS) for dt in combined.index]

    # 7) evaluate
    results = {}
    call_spikes = combined[combined["call_spike"]].dropna(subset=["future_return"])
    put_spikes  = combined[combined["put_spike"]].dropna(subset=["future_return"])

    if not call_spikes.empty:
        results["call_spike_count"] = len(call_spikes)
        results["avg_return_after_call_spike"] = call_spikes["future_return"].mean()
        results["pct_up_after_call_spike"] = (call_spikes["future_return"] > 0).mean()
    if not put_spikes.empty:
        results["put_spike_count"] = len(put_spikes)
        results["avg_return_after_put_spike"] = put_spikes["future_return"].mean()
        results["pct_down_after_put_spike"] = (put_spikes["future_return"] < 0).mean()

    # 8) plot
    if PLOT:
        fig, ax1 = plt.subplots(figsize=(12,5))
        ax1.plot(combined.index, combined["close"], label="Price", color="black")
        ax2 = ax1.twinx()
        ax2.plot(combined.index, combined["call_iv"], label="Call IV", color="blue", alpha=0.6)
        ax2.plot(combined.index, combined["put_iv"], label="Put IV", color="red", alpha=0.6)
        for dt in combined[combined["call_spike"]].index:
            ax1.axvline(dt, color="blue", alpha=0.2)
        for dt in combined[combined["put_spike"]].index:
            ax1.axvline(dt, color="red", alpha=0.2)
        ax1.legend(loc="upper left")
        ax2.legend(loc="upper right")
        plt.title(f"{ticker} - Price and IV (blue=call, red=put, vertical lines=spikes)")
        plt.show()

    print("=== Directional IV Spike Analysis ===")
    for k, v in results.items():
        print(f"{k}: {v}")
    return combined, results

if __name__ == "__main__":
    combined, results = analyze_iv_directional()
    # combined.to_csv(f"{TICKER}_iv_directional.csv")
    # print("Saved to CSV.")
    print(combined.tail(10))