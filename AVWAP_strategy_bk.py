import pandas as pd
import numpy as np
import yfinance as yf
import data_downloader
from concurrent.futures import ThreadPoolExecutor

# ============================================================
# DATA
# ============================================================

def fetch_price_data(ticker):
    df = data_downloader.get_transaction_df(ticker)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    if df.empty:
        raise ValueError(f"No data for {ticker}")

    df.index = pd.to_datetime(df.index)
    return df


# ============================================================
# RELATIVE STRENGTH SCORE
# ============================================================

def relative_strength_score(df):
    r3 = df["Close"].pct_change(63).iloc[-1]
    r6 = df["Close"].pct_change(126).iloc[-1]
    r12 = df["Close"].pct_change(252).iloc[-1]
    return 0.5 * r3 + 0.3 * r6 + 0.2 * r12


# ============================================================
# LEADER FILTER
# ============================================================

def is_leader(df):
    ma50 = df["Close"].rolling(50).mean()
    ma150 = df["Close"].rolling(150).mean()
    trend_ok = df["Close"].iloc[-1] > ma50.iloc[-1] > ma150.iloc[-1]
    near_high = df["Close"].iloc[-1] > df["High"].rolling(60).max().iloc[-1] * 0.9
    return trend_ok and near_high


# ============================================================
# VOLATILITY CONTRACTION
# ============================================================

def volatility_contracting(df):
    ranges = (df["High"] - df["Low"]) / df["Close"]
    recent = ranges.tail(5).mean()
    past = ranges.tail(30).mean()
    return recent < past * 0.75


# ============================================================
# ANCHOR SELECTION (Luk-style)
# ============================================================

def find_luk_anchor(df):
    breakout_level = df["High"].rolling(20).max().shift(1)
    breakout_mask = df["Close"] > breakout_level
    if breakout_mask.any():
        return breakout_mask[breakout_mask].index[-1]

    gap = (df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1)
    vol_spike = df["Volume"] > df["Volume"].rolling(20).mean() * 2
    ep_mask = (gap > 0.05) & vol_spike
    if ep_mask.any():
        return ep_mask[ep_mask].index[-1]

    return df["Low"].idxmin()


# ============================================================
# AVWAP
# ============================================================

def anchored_vwap(df, anchor):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    tpv = tp * df["Volume"]
    mask = df.index >= anchor
    cum_tpv = tpv.where(mask).cumsum()
    cum_vol = df["Volume"].where(mask).cumsum()
    return cum_tpv / cum_vol


# ============================================================
# INDICATORS
# ============================================================

def atr(df, period=14):
    hl = df["High"] - df["Low"]
    hc = abs(df["High"] - df["Close"].shift())
    lc = abs(df["Low"] - df["Close"].shift())
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def compute_indicators(df):
    df = df.copy()
    df["EMA9"] = df["Close"].ewm(span=9).mean()
    df["PrevHigh"] = df["High"].rolling(20).max().shift(1)
    return df


# ============================================================
# RESONANCE (true Luk confluence)
# ============================================================

def resonance_setup(df):
    df = df.copy()
    df["Near_AVWAP"] = abs(df["Close"] - df["AVWAP"]) / df["Close"] < 0.01
    df["Near_EMA9"] = abs(df["Close"] - df["EMA9"]) / df["Close"] < 0.01
    df["Near_PrevHigh"] = abs(df["Close"] - df["PrevHigh"]) / df["Close"] < 0.01
    df["Reversal"] = df["Close"] > df["Open"]
    df["Resonance"] = df["Near_AVWAP"] & df["Near_EMA9"] & df["Near_PrevHigh"] & df["Reversal"]
    return df


# ============================================================
# POSITION SIZING (Luk-style asymmetry)
# ============================================================

def position_sizing(df, capital=100000, risk=0.005):
    df = df.copy()
    df["Entry"] = df["Close"].shift(-1).fillna(df["Close"])
    df["Stop"] = df["AVWAP"] * 0.99
    df["RiskPerShare"] = df["Entry"] - df["Stop"]
    df["Shares"] = np.floor((capital * risk) / df["RiskPerShare"])
    df.loc[~df["Resonance"], "Shares"] = 0
    return df


# ============================================================
# SINGLE STOCK PIPELINE
# ============================================================

def analyze_stock(ticker, df, capital=100000, risk=0.005):
    if df is None or len(df) < 200:
        return None
    if not is_leader(df):
        return None
    if not volatility_contracting(df):
        return None

    rs = relative_strength_score(df)
    df = compute_indicators(df)

    anchor = find_luk_anchor(df)
    df["AVWAP"] = anchored_vwap(df, anchor)
    df = resonance_setup(df)

    if not df["Resonance"].iloc[-1]:
        return None

    df = position_sizing(df, capital=capital, risk=risk)
    last = df.iloc[-1]

    if last["Shares"] <= 0 or not np.isfinite(last["Shares"]):
        return None

    return {
        "Ticker": ticker,
        "RS": rs,
        "Price": last["Close"],
        "Anchor": anchor,
        "Entry": last["Entry"],
        "Stop": last["Stop"],
        "Shares": int(last["Shares"])
    }


# ============================================================
# MARKET SCANNER
# ============================================================

def scan_market(tickers):

    results = []
    for ticker in tickers:
        try:
            df  = fetch_price_data(ticker)
            r = analyze_stock(ticker,df)
        except Exception as ase:
            print(f"Error processing {ticker}: {ase}")
            continue
        if r is not None:
            results.append(r)

    df = pd.DataFrame(results)

    if df.empty:
        return df

    df = df.sort_values("RS", ascending=False)

    # top 2%
    top_n = max(10, int(len(df) * 0.02))

    return df.head(top_n)

# ============================================================
# EXAMPLE
# ============================================================

if __name__ == "__main__":

    tickers = pd.read_csv("resource/nyse_and_nasdaq_top_500.csv")["symbol"].dropna().tolist()
    leaders = scan_market(tickers)

    print("\nTop Leaders:")
    print(leaders)