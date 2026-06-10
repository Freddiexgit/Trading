# uptrend_scanner.py
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import  data_downloader as dd
import traceback
# Try to import linregress; fallback to numpy.polyfit
import yfinance as yf
import pandas as pd
import numpy as np

# Optional: use scipy.linregress for regression stats
try:
    from scipy.stats import linregress
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False

def fetch_history(ticker, period="365d", interval="1d"):
    try:

        df = dd.get_transaction_df(ticker, period=period, interval=interval)
        if df is None or df.empty:
            return None
        df = df.dropna(subset=["Close", "High", "Low", "Volume"])
        return df
    except Exception:
        return None

def compute_log_regression_metrics(series):
    y = np.log(series.values)
    x = np.arange(len(y))
    if len(y) < 3:
        return np.nan, np.nan, np.nan
    if _HAS_SCIPY:
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        r_squared = r_value**2
    else:
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan
    return float(slope), float(intercept), float(r_squared)

def annualize_slope_pct(slope_per_day, trading_days=252):
    if np.isnan(slope_per_day):
        return np.nan
    return float((np.exp(slope_per_day * trading_days) - 1) * 100)

def add_emas(df, periods=(20,50,200)):
    for p in periods:
        df[f"EMA{p}"] = df["Close"].ewm(span=p, adjust=False).mean()
    return df

def compute_atr(df, window=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window).mean().iloc[-1]
    return float(atr) if not np.isnan(atr) else np.nan

def compute_adr(df, window=20):
    rng = (df["High"] / df["Low"] - 1) * 100
    if len(rng.dropna()) < window:
        return np.nan
    return float(rng.rolling(window).mean().iloc[-1])

def is_ema_stacked_last(df):
    last = df.iloc[-1]
    try:
        return (last["Close"] > last["EMA20"] > last["EMA50"] > last["EMA200"])
    except Exception:
        return False

def suggest_levels_for_ticker(df, ticker, lookback_high=20, atr_mult_stop=2.0, target_atr_mults=(1.0,2.0,3.0)):
    last_close = float(df["Close"].iloc[-1])
    ema20 = float(df["EMA20"].iloc[-1])
    ema50 = float(df["EMA50"].iloc[-1])
    ema200 = float(df["EMA200"].iloc[-1])
    atr = compute_atr(df, window=14)
    adr = compute_adr(df, window=20)
    # recent high for breakout
    recent_high = float(df["Close"].rolling(lookback_high).max().iloc[-1])
    # regression metrics
    slope, intercept, r2 = compute_log_regression_metrics(df["Close"])
    annual_slope_pct = annualize_slope_pct(slope)

    # Entry logic:
    # - If price is within 2% below recent high -> breakout entry slightly above recent high
    # - Else prefer pullback entry at EMA20
    breakout_threshold = recent_high * 0.98
    breakout_entry = recent_high * 1.001  # small buffer above high
    pullback_entry = ema20
    if last_close >= breakout_threshold:
        recommended_entry = round(breakout_entry, 4)
        entry_type = "breakout"
    else:
        recommended_entry = round(pullback_entry, 4)
        entry_type = "pullback"

    # Stop logic:
    # - Primary stop: below EMA50 (5% buffer) OR entry - atr_mult_stop * ATR, whichever is tighter (closer to entry)
    stop_by_ema50 = ema50 * 0.95
    stop_by_atr = recommended_entry - atr_mult_stop * atr if not np.isnan(atr) else recommended_entry * 0.95
    # choose the stop that gives smaller loss (higher price) to limit risk, but ensure stop < entry
    candidate_stop = max(stop_by_ema50, stop_by_atr)
    if candidate_stop >= recommended_entry:
        candidate_stop = recommended_entry * 0.97  # fallback 3% below entry
    recommended_stop = round(candidate_stop, 4)

    # Targets: entry + n * ATR
    targets = []
    for m in target_atr_mults:
        if not np.isnan(atr):
            tgt = recommended_entry + m * atr
        else:
            tgt = recommended_entry * (1 + 0.05 * m)  # fallback percent targets
        targets.append(round(tgt, 4))

    # Risk/Reward ratios
    rr = []
    for tgt in targets:
        rr_val = (tgt - recommended_entry) / (recommended_entry - recommended_stop) if (recommended_entry - recommended_stop) != 0 else np.nan
        rr.append(round(rr_val, 2) if not np.isnan(rr_val) else np.nan)

    return {
        "symbol": ticker,
        "price": round(last_close, 4),
        "entry_type": entry_type,
        "recommended_entry": recommended_entry,
        "recommended_stop": recommended_stop,
        "target1": targets[0],
        "target2": targets[1],
        "target3": targets[2],
        "rr1": rr[0],
        "rr2": rr[1],
        "rr3": rr[2],
        "atr": round(atr, 4) if not np.isnan(atr) else np.nan,
        "adr_pct": round(adr, 2) if not np.isnan(adr) else np.nan,
        "annualized_slope_pct": round(annualize_slope_pct(slope), 2) if not np.isnan(slope) else np.nan,
        "r_squared": round(r2, 3) if not np.isnan(r2) else np.nan,
        "dist_ema20_pct": round((last_close / ema20 - 1) * 100, 2)
    }


def scan_uptrends_with_levels(tickers,
                              period="365d",
                              interval="1d",
                              min_price=2.0,
                              min_avg_volume=50000,
                              require_volume=True,
                              lookback_days=30,
                              max_extension_pct=50.0):  # <-- Added overextended parameter
    rows = []
    for tk in tickers:
        df = fetch_history(tk, period=period, interval=interval)
        if df is None or df.empty:
            continue

        vol_series = df["Volume"].dropna()
        if len(vol_series) >= 60:
            avg_vol_60 = int(vol_series.rolling(window=60).mean().iloc[-1])
        else:
            avg_vol_60 = int(vol_series.mean()) if len(vol_series) > 0 else 0

        avg_vol = avg_vol_60
        last_price = df["Close"].iloc[-1]

        if last_price < min_price or avg_vol < min_avg_volume:
            continue

        df = add_emas(df, periods=(20, 50, 200))

        # Basic EMA stacking
        if not is_ema_stacked_last(df):
            continue

        ema20_val = df["EMA20"].iloc[-1]
        if last_price <= ema20_val:
            continue

        # --- NEW: Overextended Filter ---
        # Calculate how far price is above the EMA20.
        # If it exceeds the threshold (e.g., 15%), skip it.
        dist_ema20 = ((last_price / ema20_val) - 1) * 100
        if dist_ema20 > max_extension_pct:
            continue
        # --------------------------------

        # Simple volume check
        if require_volume:
            if len(df["Volume"].dropna()) < 20:
                continue
            recent20 = df["Volume"].iloc[-20:]
            last5 = recent20.iloc[-5:].mean()
            avg20 = recent20.mean()
            if last5 < avg20 * 0.7:
                continue

        # Compute entry/stop/target levels and regression stats
        levels = suggest_levels_for_ticker(df, tk)

        # Add lookback pct change
        pct_change_lb = np.nan
        if len(df) >= lookback_days:
            past = df["Close"].iloc[-lookback_days]
            pct_change_lb = float((last_price / past - 1) * 100)

        levels.update({
            "avg_volume": avg_vol,
            f"pct_change_{lookback_days}d": round(pct_change_lb, 2) if not np.isnan(pct_change_lb) else np.nan
        })
        rows.append(levels)

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)

    # --- NEW: Improved Sorting Logic ---
    # 1. Trend Quality: Penalize erratic stocks by weighting slope against R-squared
    out["trend_quality"] = out["annualized_slope_pct"] * out["r_squared"]

    # 2. Composite Score: Boost setups that offer a better primary Risk/Reward
    out["composite_score"] = out["trend_quality"] * (1 + (out["rr1"].fillna(0) * 0.1))

    # 3. Multi-Level Sort: Sort by composite score -> R-squared -> proximity to EMA20
    out = out.sort_values(
        by=["composite_score", "r_squared", "dist_ema20_pct"],
        ascending=[False, False, True]
    ).reset_index(drop=True)

    return out

# Example usage
if __name__ == "__main__":
    tickers = ["CRML"]  # replace with your list
    df = scan_uptrends_with_levels(tickers,
                                   period="1y",
                                   interval="1d",
                                   min_price=1.0,
                                   min_avg_volume=100000,
                                   require_volume=True,
                                   lookback_days=30)
    if df.empty:
        print("No tickers matched the uptrend criteria.")
    else:
        display_cols = ["symbol","price","entry_type","recommended_entry","recommended_stop",
                        "target1","target2","target3","rr1","rr2","rr3",
                        "annualized_slope_pct","r_squared","pct_change_30d","atr","avg_volume"]
        print(df[display_cols].to_string(index=False))

def run(input_file, output_file):
    ts = pd.read_csv(input_file)["symbol"].dropna().tolist()
    df1 = scan_uptrends_with_levels(ts)
    df1.to_csv(output_file, index=False)
