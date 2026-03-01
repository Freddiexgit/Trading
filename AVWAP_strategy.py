import pandas as pd
import numpy as np
import yfinance as yf
from typing import Optional, Tuple

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1200)

def fetch_price_data(ticker: str, start: str, end: Optional[str] = None, interval: str = "1d") -> pd.DataFrame:
    """
    Fetch OHLCV data and normalize columns.
    """
    df = yf.download(ticker, start=start, end=end, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    if df.empty:
        raise ValueError(f"No data returned for {ticker} between {start} and {end}.")
    df.index = pd.to_datetime(df.index)
    return df

def anchored_vwap(df: pd.DataFrame, anchor_date: pd.Timestamp, price_col: str = "Close") -> pd.Series:
    """
    Compute Anchored VWAP from anchor_date forward.
    AVWAP = cumulative(TypicalPrice * Volume) / cumulative(Volume)
    """
    tp = (df['High'] + df['Low'] + df[price_col]) / 3.0
    tpv = tp * df['Volume']
    mask = df.index >= anchor_date
    cum_tpv = tpv.where(mask).cumsum()
    cum_vol = df['Volume'].where(mask).cumsum()
    # Avoid division by zero
    avwap = cum_tpv.div(cum_vol).reindex(df.index)
    return avwap

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average True Range (ATR) using Wilder's smoothing.
    """
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift(1)).abs()
    low_close = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr_series = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr_series

def compute_indicators(df: pd.DataFrame, anchor_date: str) -> pd.DataFrame:
    """
    Compute EMAs, AVWAP, ATR, and helper columns.
    """
    df = df.copy()
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['AVWAP'] = anchored_vwap(df, pd.to_datetime(anchor_date))
    df['ATR_14'] = atr(df, period=14)
    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3.0
    return df

def generate_signals(df: pd.DataFrame,
                     avwap_tolerance: float = 0.02,
                     pullback_touch: bool = True) -> pd.DataFrame:
    """
    Create boolean signal columns for the 'First Pullback' setup.
    - Uptrend: EMA10 > EMA20
    - Pullback_Zone: Low touches EMA10 or AVWAP (configurable)
    - Distance_to_AVWAP: close within avwap_tolerance
    """
    df = df.copy()
    df['Uptrend'] = df['EMA_10'] > df['EMA_20']
    # Pullback: low <= EMA_10 or low <= AVWAP (only where AVWAP exists)
    df['Pullback_Zone'] = False
    mask_avwap = df['AVWAP'].notna()
    df.loc[df.index, 'Pullback_Zone'] = (
        (df['Low'] <= df['EMA_10']) |
        (mask_avwap & (df['Low'] <= df['AVWAP']))
    )
    # Distance to AVWAP (relative)
    df['Distance_to_AVWAP'] = np.where(mask_avwap, (df['Close'] - df['AVWAP']).abs() / df['AVWAP'], np.nan)
    df['Close_Coiled'] = df['Distance_to_AVWAP'] <= avwap_tolerance
    df['Setup_Signal'] = df['Uptrend'] & df['Pullback_Zone'] & df['Close_Coiled']
    return df

def position_sizing(df: pd.DataFrame,
                    capital: float = 10000.0,
                    risk_per_trade: float = 0.01,
                    stop_multiplier_atr: float = 1.5,
                    fixed_stop_pct: Optional[float] = None) -> pd.DataFrame:
    """
    Compute proposed entry (next open), stop loss (ATR-based or fixed), shares to buy.
    - If fixed_stop_pct provided, use that; otherwise use ATR * stop_multiplier_atr.
    """
    df = df.copy()
    dollar_risk = capital * risk_per_trade
    # Proposed entry: next day's open (shift -1). For last row this will be NaN.
    df['Proposed_Entry'] = df['Open'].shift(-1)
    # Compute stop distance per share
    if fixed_stop_pct is not None:
        df['Stop_Loss'] = df['Proposed_Entry'] * (1 - fixed_stop_pct)
        df['Per_Share_Risk'] = df['Proposed_Entry'] - df['Stop_Loss']
    else:
        # ATR-based stop below low or entry minus ATR*multiplier, whichever is tighter
        df['ATR_Stop'] = df['Proposed_Entry'] - (df['ATR_14'] * stop_multiplier_atr)
        # Ensure stop is below today's low to avoid immediate stop-outs
        df['Stop_Loss'] = np.minimum(df['ATR_Stop'], df['Proposed_Entry'] * 0.98)
        df['Per_Share_Risk'] = df['Proposed_Entry'] - df['Stop_Loss']

    # Avoid division by zero or negative risk
    df['Per_Share_Risk'] = df['Per_Share_Risk'].clip(lower=1e-6)
    df['Shares_to_Buy'] = np.floor(dollar_risk / df['Per_Share_Risk'])
    df.loc[~df['Setup_Signal'], 'Shares_to_Buy'] = 0
    df['Position_Value'] = df['Shares_to_Buy'] * df['Proposed_Entry']
    return df


def calculate_martin_luk_setup(ticker: str,
                               start_date: str,
                               anchor_date: str,
                               capital: float = 10000.0,
                               risk_per_trade: float = 0.01,
                               avwap_tolerance: float = 0.02,
                               stop_multiplier_atr: float = 1.5,
                               fixed_stop_pct: Optional[float] = None,
                               simulate: bool = True) -> pd.DataFrame:
    """
    High-level wrapper that returns rows from anchor_date forward with signals, sizing, and optional simulation.
    """
    df = fetch_price_data(ticker, start=start_date)
    anchor_ts = pd.to_datetime(anchor_date)
    if anchor_ts not in df.index:
        # If exact anchor date not present (holiday/weekend), pick next available trading day
        next_idx = df.index[df.index >= anchor_ts]
        if next_idx.empty:
            raise ValueError(f"Anchor date {anchor_date} is after available data for {ticker}.")
        anchor_ts = next_idx[0]

    df = compute_indicators(df, anchor_ts)
    df = generate_signals(df, avwap_tolerance=avwap_tolerance)
    df = position_sizing(df, capital=capital, risk_per_trade=risk_per_trade,
                         stop_multiplier_atr=stop_multiplier_atr, fixed_stop_pct=fixed_stop_pct)

    # Return only rows from anchor forward
    return df.loc[df.index >= anchor_ts].copy()

# --- Example usage ---
if __name__ == "__main__":
    ticker = "NVDA"
    df_results = calculate_martin_luk_setup(
        ticker=ticker,
        start_date="2026-01-01",
        anchor_date="2026-02-25",
        capital=10000,
        risk_per_trade=0.01,
        avwap_tolerance=0.02,
        stop_multiplier_atr=1.5,
        fixed_stop_pct=None,
        simulate=True
    )
    setups = df_results[df_results['Setup_Signal'] & (df_results['Shares_to_Buy'] > 0)]
    print(f"Found {len(setups)} potential pullback entries for {ticker}")
    if not setups.empty:
        display_cols = ['Open', 'Close', 'EMA_10', 'EMA_20', 'AVWAP', 'Distance_to_AVWAP',
                        'Setup_Signal', 'Proposed_Entry', 'Stop_Loss', 'Shares_to_Buy']
        print(setups[display_cols])
