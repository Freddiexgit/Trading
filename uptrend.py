# uptrend_scanner.py
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import  data_downloader as dd
import traceback
# Try to import linregress; fallback to numpy.polyfit
try:
    from scipy.stats import linregress
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False

def get_history(ticker, period="180d", interval="1d"):
    """Fetch historical OHLCV for a ticker. Returns DataFrame or None."""
    try:

        df = dd.get_transaction_df(ticker, period=period, interval=interval)
        if df is None or df.empty:
            return None
        df = df.dropna(subset=["Close"])
        return df
    except Exception:
        traceback.print_exc()
        return None

def add_emas(df, ema_periods=(5,10,20,60,120,200)):
    for p in ema_periods:
        df[f"EMA{p}"] = df["Close"].ewm(span=p, adjust=False).mean()
    return df

def slope_percent_per_day(series):
    """
    Compute slope of price series in percent per day using linear regression on log(price).
    Returns percent change per day (e.g., 0.012 = 1.2%/day).
    """
    y = np.log(series.values)
    x = np.arange(len(y))
    if len(y) < 2:
        return np.nan
    if _HAS_SCIPY:
        res = linregress(x, y)
        slope = res.slope
    else:
        slope, _ = np.polyfit(x, y, 1)
    # slope is per index; convert to percent/day
    return float(np.expm1(slope))  # approximate daily percent (e^slope - 1)

def volume_trend(df, lookback=20):
    """Return True if recent volume is >= historical average and trending up."""
    if "Volume" not in df.columns or len(df["Volume"].dropna()) < lookback:
        return False
    recent = df["Volume"].iloc[-lookback:]
    avg = recent.mean()
    # simple check: last 5-day avg >= 1.0 * 20-day avg and slope positive
    last5 = recent.iloc[-5:].mean()
    slope = slope_percent_per_day(recent)  # percent/day on volume
    return (last5 >= avg * 0.9) and (slope is not None and slope >= 0)

def is_ema_stacked(df):
    """Check EMA stacking on the last row: EMA5 > EMA10 > EMA20 > EMA60 > EMA120 > EMA200"""
    last = df.iloc[-1]
    try:
        return (last["EMA5"] > last["EMA10"] > last["EMA20"] >
                last["EMA60"] > last["EMA120"] > last["EMA200"])
    except Exception:
        return False

def uptrend_score(df, price_change_days=30):
    """
    Compute a composite score:
      - speed: slope %/day (primary sort)
      - recent percent change over price_change_days
      - distance above EMA20
    Returns dict with metrics.
    """
    out = {}
    close = df["Close"].iloc[-1]
    out["close"] = float(close)
    # slope over full available window
    out["slope_pct_per_day"] = slope_percent_per_day(df["Close"])
    # percent change over price_change_days
    if len(df) >= price_change_days:
        past = df["Close"].iloc[-price_change_days]
        out[f"pct_change_{price_change_days}d"] = float((close / past - 1) * 100)
    else:
        out[f"pct_change_{price_change_days}d"] = np.nan
    # distance above EMA20
    out["dist_above_ema20_pct"] = float((close / df["EMA20"].iloc[-1] - 1) * 100) if "EMA20" in df.columns else np.nan
    return out

def scan_uptrends(tickers,
                  period="180d",
                  interval="1d",
                  min_price=1.0,
                  min_avg_volume=100000,
                  price_change_days=30,
                  require_volume=True):
    """
    Scan a list of tickers and return DataFrame of those matching uptrend characteristics,
    sorted by speed (slope_pct_per_day descending).
    """
    results = []
    for tk in tickers:
        df = get_history(tk, period=period, interval=interval)
        if df is None or df.empty:
            continue
        # basic liquidity filter: average volume
        avg_vol = df["Volume"].dropna().mean() if "Volume" in df.columns else 0
        last_price = df["Close"].iloc[-1]
        if last_price < min_price or (avg_vol < min_avg_volume):
            continue
        df = add_emas(df)
        # require price above EMA20 and EMA stack
        price_above_ema20 = last_price > df["EMA20"].iloc[-1]
        ema_stack = is_ema_stacked(df)
        vol_ok = True if not require_volume else volume_trend(df)
        if price_above_ema20 and ema_stack and vol_ok:
            metrics = uptrend_score(df, price_change_days=price_change_days)
            metrics.update({
                "ticker": tk,
                "avg_volume": int(avg_vol),
                "ema_stack": ema_stack,
                "price_above_ema20": price_above_ema20
            })
            results.append(metrics)

    if not results:
        return pd.DataFrame()  # empty

    out_df = pd.DataFrame(results)
    # sort by slope (speed) descending
    out_df = out_df.sort_values(by="slope_pct_per_day", ascending=False).reset_index(drop=True)
    # convert slope to percent/day readable
    out_df["slope_pct_per_day"] = out_df["slope_pct_per_day"] * 100
    return out_df

# Example usage
if __name__ == "__main__":
    tickers = pd.read_csv("resource/my_watch_list.csv")["symbol"].dropna().tolist()
    df = scan_uptrends(tickers,
                       period="365d",
                       interval="1d",
                       min_price=5.0,
                       min_avg_volume=200000,
                       price_change_days=30,
                       require_volume=True)
    if df.empty:
        print("No tickers matched the uptrend criteria.")
    else:
        print(df[["ticker", "close", "slope_pct_per_day", "pct_change_30d", "dist_above_ema20_pct", "avg_volume"]])
