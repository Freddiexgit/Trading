import yfinance as yf
import pandas as pd
import numpy as np
from tenacity import wait_chain


# ----------------- Core logic -----------------

def detect_consolidation_window(df, end_idx, min_days=90, atr_window=20,
                                drift_threshold=0.002, volatility_factor=1.5):
    """
    Check if the window ending at end_idx is a consolidation.
    Uses data up to end_idx (inclusive).
    """
    if end_idx < min_days + atr_window:
        return False, None

    window = df.iloc[end_idx - min_days + 1:end_idx + 1].copy()
    if window["ATR"].isna().any():
        return False, None

    box_high = window["High"].max()
    box_low = window["Low"].min()
    box_range = box_high - box_low
    atr = window["ATR"].iloc[-1]

    if atr == 0 or np.isnan(atr):
        return False, None

    # 1. Volatility-adjusted tightness
    volatility_tight = box_range / atr < volatility_factor

    # 2. Flat trend (low drift)
    x = np.arange(len(window))
    slope = np.polyfit(x, window["Close"], 1)[0] / window["Close"].mean()
    flat_trend = abs(slope) < drift_threshold

    # 3. % of candles inside box
    inside_pct = (
        (window["Low"] >= box_low) &
        (window["High"] <= box_high)
    ).mean()
    stays_inside = inside_pct > 0.8

    # 4. Touches
    upper_zone = box_high * 0.8
    lower_zone = box_low * 1.2
    touches_top = (window["High"] >= upper_zone).sum()
    touches_bottom = (window["Low"] <= lower_zone).sum()
    touches_ok = touches_top >= 2 and touches_bottom >= 2

    is_consolidating = volatility_tight and flat_trend and stays_inside and touches_ok

    stats = {
        "Box_High": box_high,
        "Box_Low": box_low,
        "Range_ATR_Ratio": box_range / atr,
        "Slope": slope,
        "Inside_Pct": inside_pct,
        "Touches_Top": touches_top,
        "Touches_Bottom": touches_bottom
    }

    return is_consolidating, stats


def detect_breakout_bar(df, idx, box_high, box_low,
                        atr_window=20, vol_mult=1.3, range_mult=1.2):
    """
    Detect breakout on a single bar at index idx.
    """
    if idx < atr_window or idx >= len(df):
        return None, None

    row = df.iloc[idx]
    close = row["Close"]
    high = row["High"]
    low = row["Low"]
    atr = row["ATR"]
    vol20 = row["VOL20"]
    volume = row["Volume"]
    opn = row["Open"]

    if np.isnan(atr) or np.isnan(vol20):
        return None, None

    candle_range = high - low
    upper_wick = high - max(close, opn)
    lower_wick = min(close, opn) - low

    bullish = (
        close > box_high and
        candle_range > range_mult * atr and
        volume > vol20 * vol_mult and
        upper_wick < candle_range * 0.4
    )

    bearish = (
        close < box_low and
        candle_range > range_mult * atr and
        volume > vol20 * vol_mult and
        lower_wick < candle_range * 0.4
    )

    if bullish:
        breakout_type = "bullish"
    elif bearish:
        breakout_type = "bearish"
    else:
        breakout_type = None

    stats = {
        "Breakout_Type": breakout_type,
        "Close": close,
        "High": high,
        "Low": low,
        "ATR": atr,
        "Volume": volume,
        "VOL20": vol20,
        "Candle_Range": candle_range,
        "Upper_Wick": upper_wick,
        "Lower_Wick": lower_wick,
        "Date": row.name
    }

    return breakout_type, stats


# ----------------- Backtest & Screener -----------------

def backtest_breakout_strategy(
    ticker,
    period="2y",
    min_days=20,
    atr_window=20
):
    """
    For a single ticker:
    - download data
    - compute ATR & VOL20
    - scan for consolidations + breakouts
    - buy 1 share on each breakout at breakout close
    - exit all at most recent close
    """
    df = yf.download(ticker, interval="1d",start="2025-06-01",end="2025-12-31",
                     progress=False, auto_adjust=True)
    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    if df.empty or len(df) < min_days + atr_window + 5:
        return {
            "Ticker": ticker,
            "Trades": 0,
            "PnL": 0.0,
            "Last_Price": np.nan
        }

    df["ATR"] = (df["High"] - df["Low"]).rolling(atr_window).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    last_close = df["Close"].iloc[-1]
    trades = []
    i = min_days + atr_window

    while i < len(df) - 1:
        # 1) Check consolidation ending at i-1
        is_cons, cons_stats = detect_consolidation_window(
            df, end_idx=i - 1,
            min_days=min_days,
            atr_window=atr_window
        )

        if not is_cons:
            i += 1
            continue

        box_high = cons_stats["Box_High"]
        box_low = cons_stats["Box_Low"]
        print(ticker,box_low,box_high)
        # 2) Check breakout at bar i
        breakout_type, bstats = detect_breakout_bar(
            df, idx=i,
            box_high=box_high,
            box_low=box_low
        )

        if breakout_type is not None:
            entry_price = bstats["Close"]
            trades.append({
                "Entry_Date": bstats["Date"],
                "Entry_Price": entry_price,
                "Breakout_Type": breakout_type
            })
            # Skip ahead a bit to avoid overlapping consolidations
            i += min_days
        else:
            i += 1

    # Exit all trades at last close
    pnl = 0.0
    for t in trades:
        pnl += last_close - t["Entry_Price"]  # 1 share

    return {
        "Ticker": ticker,
        "Trades": len(trades),
        "PnL": round(pnl, 2),
        "Last_Price": round(last_close, 2)
    }


def run_screener(tickers, period="2y"):
    results = []
    for t in tickers:
        print(f"Running backtest for {t}...")
        res = backtest_breakout_strategy(t, period=period)
        results.append(res)

    df_res = pd.DataFrame(results)
    df_res["PnL"] = df_res["PnL"].astype(float)
    total_pnl = df_res["PnL"].sum()

    print("\n=== Screener Results ===")
    print(df_res.sort_values("PnL", ascending=False).to_string(index=False))
    print(f"\nTOTAL PnL (1 share per breakout, exit at latest close): {round(total_pnl, 2)}")

    return df_res


# ----------------- Example run -----------------

if __name__ == "__main__":
    # Example: 100+ tickers (replace with your universe)
    watchlist = pd.read_csv("resource/my_vip.csv")["symbol"].dropna().tolist()
    run_screener(watchlist, period="2y")
