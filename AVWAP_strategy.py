import pandas as pd
import numpy as np
import yfinance as yf
from typing import Optional

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1200)


def fetch_price_data(ticker: str, start: str, end: Optional[str] = None, interval: str = "1d") -> pd.DataFrame:
    """Fetch OHLCV data and normalize columns."""
    df = yf.download(ticker, start=start, end=end, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    if df.empty:
        raise ValueError(f"No data returned for {ticker} between {start} and {end}.")
    df.index = pd.to_datetime(df.index)
    return df


def find_auto_anchor(df: pd.DataFrame, lookback_days: int = 252) -> pd.Timestamp:
    """Finds the highest volume day within the lookback period to use as the catalyst anchor."""
    recent_df = df.tail(lookback_days)
    if recent_df.empty:
        return df.index[0]
    highest_vol_idx = recent_df['Volume'].idxmax()
    return highest_vol_idx


def anchored_vwap(df: pd.DataFrame, anchor_date: pd.Timestamp, price_col: str = "Close") -> pd.Series:
    """Compute Anchored VWAP from anchor_date forward."""
    tp = (df['High'] + df['Low'] + df[price_col]) / 3.0
    tpv = tp * df['Volume']
    mask = df.index >= anchor_date
    cum_tpv = tpv.where(mask).cumsum()
    cum_vol = df['Volume'].where(mask).cumsum()
    return cum_tpv.div(cum_vol).reindex(df.index)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (ATR) using Wilder's smoothing."""
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift(1)).abs()
    low_close = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def compute_indicators(df: pd.DataFrame, anchor_date: pd.Timestamp) -> pd.DataFrame:
    """Compute EMAs, AVWAP, ATR, and helper columns."""
    df = df.copy()
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['AVWAP'] = anchored_vwap(df, anchor_date)
    df['ATR_14'] = atr(df, period=14)
    return df


def generate_signals(df: pd.DataFrame, avwap_tolerance: float = 0.02) -> pd.DataFrame:
    """Create boolean signal columns for the 'First Pullback' setup."""
    df = df.copy()
    df['Uptrend'] = df['EMA_10'] > df['EMA_20']

    mask_avwap = df['AVWAP'].notna()
    df['Pullback_Zone'] = False
    df.loc[df.index, 'Pullback_Zone'] = (
            (df['Low'] <= df['EMA_10']) |
            (mask_avwap & (df['Low'] <= df['AVWAP']))
    )

    df['Distance_to_AVWAP'] = np.where(mask_avwap, (df['Close'] - df['AVWAP']).abs() / df['AVWAP'], np.nan)
    df['Close_Coiled'] = df['Distance_to_AVWAP'] <= avwap_tolerance
    df['Setup_Signal'] = df['Uptrend'] & df['Pullback_Zone'] & df['Close_Coiled']
    return df


def position_sizing(df: pd.DataFrame, capital: float = 10000.0, risk_per_trade: float = 0.01,
                    stop_multiplier_atr: float = 1.5, fixed_stop_pct: Optional[float] = None) -> pd.DataFrame:
    """Compute entry, stop loss, and exact share sizing based on risk."""
    df = df.copy()
    dollar_risk = capital * risk_per_trade

    # Use next day's open if available, otherwise use today's close for real-time sizing
    df['Proposed_Entry'] = df['Open'].shift(-1).fillna(df['Close'])

    if fixed_stop_pct is not None:
        df['Stop_Loss'] = df['Proposed_Entry'] * (1 - fixed_stop_pct)
    else:
        # Use np.maximum to strictly enforce the tightest possible stop between ATR and a 2% hard floor
        df['ATR_Stop'] = df['Proposed_Entry'] - (df['ATR_14'] * stop_multiplier_atr)
        df['Stop_Loss'] = np.maximum(df['ATR_Stop'], df['Proposed_Entry'] * 0.98)

    df['Per_Share_Risk'] = (df['Proposed_Entry'] - df['Stop_Loss']).clip(lower=1e-6)
    df['Shares_to_Buy'] = np.floor(dollar_risk / df['Per_Share_Risk'])
    df.loc[~df['Setup_Signal'], 'Shares_to_Buy'] = 0
    return df


def run_screener(ticker: str, start_date: str, anchor_date: Optional[str] = None,
                 capital: float = 10000.0, risk_per_trade: float = 0.01) -> pd.DataFrame:
    """Main execution function to fetch data, compute strategy, and return actionable setups."""
    df = fetch_price_data(ticker, start=start_date)

    # Determine the anchor date automatically if not provided
    if anchor_date:
        anchor_ts = pd.to_datetime(anchor_date)
        if anchor_ts not in df.index:
            next_idx = df.index[df.index >= anchor_ts]
            if next_idx.empty:
                raise ValueError(f"Anchor date {anchor_date} is out of bounds for {ticker}.")
            anchor_ts = next_idx[0]
    else:
        anchor_ts = find_auto_anchor(df)
        print(f"[{ticker}] Auto-anchored VWAP to highest volume day: {anchor_ts.strftime('%Y-%m-%d')}")

    df = compute_indicators(df, anchor_ts)
    df = generate_signals(df)
    df = position_sizing(df, capital=capital, risk_per_trade=risk_per_trade)

    return df.loc[df.index >= anchor_ts].copy()


# --- Execution ---
if __name__ == "__main__":
    # Test with a high-momentum stock, letting the script find the anchor automatically
    ticker = "TSLA"

    try:
        results = run_screener(
            ticker=ticker,
            start_date="2026-02-01",
            anchor_date=None,  # Set to None to trigger auto-anchoring
            capital=50000,
            risk_per_trade=0.015
        )

        setups = results[results['Setup_Signal'] & (results['Shares_to_Buy'] > 0)]
        print(f"\nFound {len(setups)} valid pullback setups for {ticker}.")

        if not setups.empty:
            display_cols = ['Close', 'AVWAP', 'Setup_Signal', 'Proposed_Entry', 'Stop_Loss', 'Shares_to_Buy']
            print(setups.tail(5))  # Show the 5 most recent setups

    except Exception as e:
        print(f"Error processing {ticker}: {e}")