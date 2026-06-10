import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path

# -------------------------
# Configurable parameters
# -------------------------
OUT_CSV = 'pullback_scan_results.csv'
HISTORY_PERIOD = "6mo"           # for daily timeframe
LOWER_INTERVAL = "60m"           # lower timeframe for pullback confirmation (use "15m" for intraday)
MIN_BARS = 60
EMA_FAST = 10
EMA_MED = 50
EMA_SLOW = 200
ADX_PERIOD = 14
VOLUME_LOOKBACK = 20
PULLBACK_MAX_DEPTH = 0.38        # 38% of last impulse
PULLBACK_MIN_DEPTH = 0.03        # 3% minimum retrace
NEAR_EMA_PCT = 0.01              # within 1% of fast EMA
ATR_PERIOD = 14
ATR_STOP_MULT = 1.2
SCORE_THRESHOLD = 0.6            # require score >= this to accept
# -------------------------

def get_tickers_from_folder(input_csv):
   return  pd.read_csv(input_csv)[['symbol']].dropna().rename(columns={'symbol': 'ticker'})

# Wilder's RMA (Wilder moving average) using ewm with alpha = 1/period
def rma(series, period):
    return series.ewm(alpha=1/period, adjust=False).mean()

def atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    # Use Wilder's smoothing for ATR (RMA of TR)
    return rma(tr, period)

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def adx_ta_style(df, period=14):
    """
    ADX implementation closer to TA-Lib / Wilder:
    - Compute True Range (TR)
    - Compute +DM and -DM
    - Smooth TR, +DM, -DM with Wilder's RMA
    - Compute +DI and -DI as 100 * (smoothed DM / smoothed TR)
    - DX = 100 * abs(+DI - -DI) / (+DI + -DI)
    - ADX = RMA(DX, period)
    Returns ADX series (aligned with df index). NaNs for initial rows.
    """
    high = df['High']
    low = df['Low']
    close = df['Close']

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    # True Range
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder smoothing (RMA) of TR and DMs
    smoothed_tr = rma(tr.fillna(0), period)
    smoothed_plus_dm = rma(pd.Series(plus_dm, index=df.index).fillna(0), period)
    smoothed_minus_dm = rma(pd.Series(minus_dm, index=df.index).fillna(0), period)

    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        plus_di = 100 * (smoothed_plus_dm / smoothed_tr)
        minus_di = 100 * (smoothed_minus_dm / smoothed_tr)
        dx = 100 * (np.abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = rma(dx.fillna(0), period)
    # Return series aligned to df index
    return adx

def score_signal(features, weights=None):
    if weights is None:
        weights = {
            'trend': 0.3,
            'volume': 0.2,
            'pullback_depth': 0.2,
            'momentum': 0.2,
            'ema_proximity': 0.1
        }
    s = 0.0
    for k, w in weights.items():
        s += features.get(k, 0) * w
    return s

def analyze_ticker(ticker):
    # Download daily and lower timeframe
    try:
        df_daily = yf.download(ticker, period=HISTORY_PERIOD, interval="1d", progress=False, auto_adjust=True)
        # Fix for MultiIndex columns returned by newer yfinance versions
        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = df_daily.columns.get_level_values(0)
        df_lower = yf.download(ticker, period="60d", interval=LOWER_INTERVAL, progress=False, auto_adjust=True)
        if isinstance(df_lower.columns, pd.MultiIndex):
            df_lower.columns = df_lower.columns.get_level_values(0)
    except Exception as e:
        print(f"Download error {ticker}: {e}")
        return None

    # Basic sanity checks: enough bars and no pervasive NaNs
    if df_daily.empty or df_lower.empty:
        return None
    if len(df_daily) < MIN_BARS or len(df_lower) < 20:
        return None

    # Drop rows with NaNs in essential columns for indicator calc
    required_cols = ['High', 'Low', 'Close', 'Volume']
    if df_daily[required_cols].isnull().any(axis=None) or df_lower[required_cols].isnull().any(axis=None):
        # If there are NaNs, try to drop them; if too few rows remain, skip ticker
        df_daily = df_daily.dropna(subset=required_cols)
        df_lower = df_lower.dropna(subset=required_cols)
        if len(df_daily) < MIN_BARS or len(df_lower) < 20:
            return None

    # Daily indicators
    df_daily['EMA_50'] = ema(df_daily['Close'], EMA_MED)
    df_daily['EMA_200'] = ema(df_daily['Close'], EMA_SLOW)
    df_daily['ADX'] = adx_ta_style(df_daily, ADX_PERIOD)
    df_daily['ATR'] = atr(df_daily, ATR_PERIOD)

    # Lower timeframe indicators
    df_lower['EMA_10'] = ema(df_lower['Close'], EMA_FAST)
    df_lower['EMA_50'] = ema(df_lower['Close'], EMA_MED)
    df_lower['ATR'] = atr(df_lower, ATR_PERIOD)
    df_lower['Volume_MA'] = df_lower['Volume'].rolling(VOLUME_LOOKBACK).mean()

    # Ensure we have valid latest rows
    if df_daily['Close'].isnull().iloc[-1] or df_lower['Close'].isnull().iloc[-1]:
        return None

    latest_daily = df_daily.iloc[-1]
    latest_lower = df_lower.iloc[-1]

    # Trend filter: require daily EMA50 > EMA200 OR ADX strong
    is_uptrend = (latest_daily['EMA_50'] > latest_daily['EMA_200']) or (latest_daily['ADX'] > 20)

    # Identify last impulse high on lower timeframe: highest close in last N bars excluding last 3 bars
    lookback_impulse = 20
    if len(df_lower) < lookback_impulse + 3:
        return None
    impulse_slice = df_lower['Close'].iloc[-(lookback_impulse+3):-3]
    if impulse_slice.empty or impulse_slice.isnull().all():
        return None
    impulse_high = impulse_slice.max()
    if impulse_high <= 0 or np.isnan(impulse_high):
        return None

    pullback_depth = (impulse_high - latest_lower['Close']) / impulse_high if impulse_high > 0 else np.nan

    # Volume check: latest volume < recent average and/or declining sequence
    vol_ok = False
    if not np.isnan(latest_lower.get('Volume', np.nan)) and not np.isnan(latest_lower.get('Volume_MA', np.nan)):
        vol_ok = latest_lower['Volume'] < latest_lower['Volume_MA'] * 0.95
    vol_decline = False
    if len(df_lower['Volume']) >= 3:
        v = df_lower['Volume'].iloc[-3:]
        if not v.isnull().any():
            vol_decline = (v.iloc[0] > v.iloc[1] > v.iloc[2])

    near_ema = False
    if not np.isnan(latest_lower.get('EMA_10', np.nan)):
        near_ema = abs(latest_lower['Close'] - latest_lower['EMA_10']) / latest_lower['EMA_10'] < NEAR_EMA_PCT

    # Momentum: small lookback percent change
    momentum = np.nan
    if len(df_lower) > 6 and not np.isnan(df_lower['Close'].iloc[-6]):
        momentum = (latest_lower['Close'] - df_lower['Close'].iloc[-6]) / df_lower['Close'].iloc[-6]
    else:
        momentum = 0.0

    # ATR stop suggestion (use lower timeframe ATR for tighter intraday stops)
    atr_val = latest_lower['ATR'] if not np.isnan(latest_lower['ATR']) else latest_daily['ATR']
    stop_distance = atr_val * ATR_STOP_MULT if not np.isnan(atr_val) else np.nan
    target1 = latest_lower['Close'] + atr_val * 1.0 if not np.isnan(atr_val) else np.nan
    target2 = latest_lower['Close'] + atr_val * 2.0 if not np.isnan(atr_val) else np.nan

    # Build normalized features for scoring (clamp to 0..1)
    features = {}
    features['trend'] = 1.0 if is_uptrend else 0.0
    features['volume'] = 1.0 if (vol_ok or vol_decline) else 0.0
    # pullback depth: ideal between MIN and MAX -> map to 0..1
    if np.isnan(pullback_depth) or pullback_depth <= 0:
        features['pullback_depth'] = 0.0
    else:
        ideal = (PULLBACK_MIN_DEPTH + PULLBACK_MAX_DEPTH) / 2
        denom = (PULLBACK_MAX_DEPTH - PULLBACK_MIN_DEPTH) if (PULLBACK_MAX_DEPTH - PULLBACK_MIN_DEPTH) != 0 else 1e-6
        features['pullback_depth'] = max(0.0, 1 - abs(pullback_depth - ideal) / denom)
    features['momentum'] = np.clip((momentum + 0.02) / 0.04, 0, 1) if not np.isnan(momentum) else 0.0
    features['ema_proximity'] = 1.0 if near_ema else 0.0

    s = score_signal(features)

    # Build reasons vectorized and robust to NaNs
    reasons = []
    if not is_uptrend:
        reasons.append("Not in daily uptrend")
    if np.isnan(pullback_depth) or not (PULLBACK_MIN_DEPTH <= pullback_depth <= PULLBACK_MAX_DEPTH):
        reasons.append(f"Pullback depth {pullback_depth if not np.isnan(pullback_depth) else 'NaN'} outside range")
    if not (vol_ok or vol_decline):
        reasons.append("Volume not confirming")
    if not near_ema:
        reasons.append("Not near EMA10")

    candidate = {
        'Ticker': ticker,
        'Lower_Close': round(float(latest_lower['Close']), 6),
        'Daily_Close': round(float(latest_daily['Close']), 6),
        'Pullback_Depth': round(float(pullback_depth), 6) if not np.isnan(pullback_depth) else None,
        'Score': round(float(s), 4),
        'ATR_Stop': round(float(stop_distance), 6) if not np.isnan(stop_distance) else None,
        'Target1': round(float(target1), 6) if not np.isnan(target1) else None,
        'Target2': round(float(target2), 6) if not np.isnan(target2) else None,
        'Reasons': ';'.join(reasons) if reasons else 'OK'
    }

    # Return candidate regardless for debugging; caller can filter by Score/Reasons
    return candidate

def find_pullbacks(input_csv):
    tickers_df = get_tickers_from_folder(input_csv)
    results = []
    for _, row in tickers_df.iterrows():
        ticker = row['ticker']
        try:
            cand = analyze_ticker(ticker)
            if cand:
                results.append(cand)
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")
    if results:
        df = pd.DataFrame(results)
        high = df[df['Score'] >= SCORE_THRESHOLD]
        print(f"Total scanned: {len(tickers_df)}, candidates: {len(df)}, high quality: {len(high)}")
        df.to_csv(OUT_CSV, index=False)
        print(df.sort_values('Score', ascending=False).head(50).to_string(index=False))
    else:
        print("No pullbacks detected today.")

if __name__ == "__main__":
    find_pullbacks("resource/my_vip.csv")
