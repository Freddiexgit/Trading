# =========================================================
# INSTITUTIONAL LEADER ROTATION RADAR
# =========================================================

import  traceback
import pandas as pd
import numpy as np
from typing import Dict, Any
import data_downloader

from analytics import industry_score

# ---------------- CONFIG ----------------


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

MARKET_ETF = "QQQ"

import os
from collections import defaultdict
industry_and_symbol = defaultdict(list)
symbol_and_industry = {}
def load_symbol_sector():
    base_dir = "resource/industries/"
    for file in os.listdir(base_dir):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(base_dir, file))
            industry_and_symbol[file.replace(".csv", "")] = df["symbol"].tolist()
            for key, values in industry_and_symbol.items():
                for val in values:
                    symbol_and_industry[val]=key


# ---------------- UTIL ----------------

def safe_div(a,b):
    if b == 0 or np.isnan(b):
        return np.nan
    return a/b


def slope(series):
    y = series.dropna().values
    if len(y) < 20:
        return np.nan
    x = np.arange(len(y))
    return np.polyfit(x,y,1)[0]


def add_atr(df, period=14):
    """Calculates the Average True Range and appends it to the DataFrame."""

    # 1. Calculate the three True Range components
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = np.abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = np.abs(df['Low'] - df['Close'].shift(1))

    # 2. Find the maximum of the three to get the daily True Range
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)

    # 3. Calculate the 14-day rolling average of the True Range
    df['ATR_14'] = df['TR'].rolling(window=period).mean()

    # 4. Clean up the intermediate calculation columns
    df.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1, inplace=True)

    return df
def rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# df must contain a 'Close' column indexed by time (datetime index recommended)
def add_macd_hist(df, fast=12, slow=26, signal=9, price_col='Close'):
    # compute EMAs
    ema_fast = df[price_col].ewm(span=fast, adjust=False).mean()
    ema_slow = df[price_col].ewm(span=slow, adjust=False).mean()

    # MACD line and signal line
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    # histogram
    macd_hist = macd_line - signal_line

    # attach to dataframe (choose column names you prefer)
    df['MACD'] = macd_line
    df['MACD_signal'] = signal_line
    df['MACD_hist'] = macd_hist

    return df

def load_data(ticker):

    df = data_downloader.get_transaction_df(ticker)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if df is None or len(df) < 200:
        return pd.DataFrame()
    df["MA10"] = df["Close"].ewm(span=10).mean()
    df["MA20"] = df["Close"].ewm(span=20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA60"] = df["Close"].rolling(60).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()
    df = add_atr(df)
    df["RSI14"]=rsi(df["Close"], 14)
    df = add_macd_hist(df)

    return df.dropna()


# =========================================================
# MARKET REGIME FILTER
# =========================================================

def market_ok():

    spy = load_data(MARKET_ETF)
    close = float(spy["Close"].iloc[-1])
    ma50  = float(spy["MA50"].iloc[-1])
    ma200 = float(spy["MA200"].iloc[-1])

    cond1 = close > ma200
    cond2 = ma50 > ma200

    return bool(cond1 and cond2)

# =========================================================
# SECTOR ROTATION ENGINE ⭐⭐⭐
# =========================================================

def sector_relative_strength(sector_etf):
    sec = load_data(sector_etf)["Close"]
    mkt = load_data(MARKET_ETF)["Close"]

    rs = sec / mkt
    return slope(rs.tail(90))


def sector_breadth(tickers):

    signals = []

    for t in tickers:
        try:
            df = load_data(t)
            signals.append(
                df["Close"].iloc[-1] > df["MA50"].iloc[-1]
            )
        except:
            pass

    if len(signals)==0:
        return np.nan

    return np.mean(signals)


def sector_score(sector):
    etf = industry_score.SECTOR_ETF.get(sector, "SPY")
    rs = sector_relative_strength(etf)

    members = industry_and_symbol[sector]
    if len(members) >= 10:
        members = members[:10]
    breadth = sector_breadth(members)

    score = 0.6*rs + 0.4*breadth
    return score


# =========================================================
# LEADER STRUCTURE SCORE
# =========================================================

import numpy as np
import pandas as pd
from typing import Dict, Any

def safe_mean(series: pd.Series, fallback: float = 0.0) -> float:
    v = series.dropna()
    return float(v.mean()) if not v.empty else float(fallback)

def safe_div(a: float, b: float, fallback: float = 0.0) -> float:
    try:
        return float(a) / float(b) if b not in (0, None, np.nan) else float(fallback)
    except Exception:
        return float(fallback)

def normalize(x: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 0.0
    return float(np.clip((x - lo) / (hi - lo), 0.0, 1.0))
# 1. define slope function
def my_slope(series):
    y = series.values
    x = np.arange(len(y))
    if len(y) < 2:
        return 0.0
    slope, _ = np.polyfit(x, y, 1)
    return slope


def leader_structure(
    df: pd.DataFrame,
    slope_func,
    lookback_trend: int = 60,
    vol_window: int = 20,
    ma_fast: str = "MA10",
    ma_mid: str = "MA20",
    ma_slow: str = "MA50",
    ma_macro: str = "MA200"
) -> Dict[str, Any]:
    """
    Returns a structured score and diagnostics describing leadership structure.

    Required columns: Close, Volume, and the MA columns named by parameters.
    slope_func: callable(series: pd.Series) -> float  (returns slope or trend magnitude)
    """
    diagnostics: Dict[str, Any] = {}
    required = {ma_fast, ma_mid, ma_slow, ma_macro, "Close", "Volume"}
    missing = required - set(df.columns)
    if missing:
        return {"score": 0.0, "status": "MISSING_COLUMNS", "diagnostics": {"missing": list(missing)}}

    if len(df) < lookback_trend:
        return {"score": 0.0, "status": "INSUFFICIENT_HISTORY", "diagnostics": {"len": len(df)}}

    # Positional safety
    last = df.iloc[-1]
    # 1. Macro trend filter (long-term)
    macro_up = bool(last["Close"] > df[ma_macro].iloc[-1])
    diagnostics["macro_up"] = macro_up

    # 2. Trend strength (slope of MA50 or MA60 over lookback_trend)
    try:
        trend_series = df[ma_slow].iloc[-lookback_trend:]
        trend_raw = float(slope_func(trend_series))
    except Exception:
        trend_raw = 0.0
    diagnostics["trend_raw"] = trend_raw

    # Normalize trend_raw relative to recent absolute slope magnitudes to keep score bounded
    # Use historical slopes to get a reasonable scale
    slopes = []
    window = max(lookback_trend, 60)
    for i in range(window, len(df)+1, max(1, window//4)):
        seg = df[ma_slow].iloc[max(0, i-window):i]
        if len(seg) >= 2:
            try:
                slopes.append(abs(float(slope_func(seg))))
            except Exception:
                pass
    slope_scale = max(np.percentile(slopes, 75) if slopes else 1.0, 1e-6)
    trend_norm = float(np.clip(trend_raw / slope_scale, -1.0, 1.0))
    # map to 0..1 where negative trend -> 0
    trend_score = float(np.clip((trend_norm + 1) / 2, 0.0, 1.0))
    diagnostics["trend_score"] = trend_score
    diagnostics["slope_scale"] = float(slope_scale)

    # 3. Moving average alignment (fast > mid > slow)
    alignment_bool = (last[ma_fast] > last[ma_mid]) and (last[ma_mid] > last[ma_slow])
    alignment_score = 1.0 if alignment_bool else 0.0
    diagnostics["alignment_bool"] = alignment_bool

    # 4. Volume expansion (last volume vs vol_window average)
    vol20 = safe_mean(df["Volume"].iloc[-vol_window:], fallback=1.0)
    vol_expansion = safe_div(last["Volume"], vol20, fallback=0.0)
    # normalize typical vol expansion to 0..1 using a reasonable cap (e.g., 3x)
    vol_score = float(np.clip((vol_expansion - 1.0) / (3.0 - 1.0), 0.0, 1.0))
    diagnostics["vol_expansion"] = float(vol_expansion)
    diagnostics["vol_score"] = vol_score

    # 5. Relative strength vs lookback (Close / MA50)
    rs = safe_div(last["Close"], last[ma_slow], fallback=1.0)
    rs_score = normalize(rs, 0.95, 1.15)  # 0.95->0, 1.0->~0.25, 1.15->1.0 (tunable)
    diagnostics["rs"] = float(rs)
    diagnostics["rs_score"] = rs_score

    # 6. Proximity to breakout (close relative to recent high)
    recent_high = df["High"].iloc[-lookback_trend:].max() if "High" in df.columns else last["Close"]
    proximity = safe_div(last["Close"], recent_high, fallback=1.0)
    proximity_score = normalize(proximity, 0.9, 1.02)
    diagnostics["recent_high"] = float(recent_high)
    diagnostics["proximity_score"] = proximity_score

    # 7. Composite weighting (tunable)
    # - trend_score: structural strength
    # - alignment_score: moving average confirmation
    # - vol_score: participation
    # - rs_score: relative strength vs peers/MA
    # - proximity_score: breakout readiness
    w_trend = 0.35
    w_align = 0.20
    w_vol = 0.15
    w_rs = 0.15
    w_prox = 0.15

    raw = (
        w_trend * trend_score +
        w_align * alignment_score +
        w_vol * vol_score +
        w_rs * rs_score +
        w_prox * proximity_score
    )

    # Penalize if macro trend is down
    if not macro_up:
        raw *= 0.6
        diagnostics["macro_penalty_applied"] = True
    else:
        diagnostics["macro_penalty_applied"] = False

    score = float(np.clip(raw, 0.0, 1.0))
    diagnostics.update({
        "w_trend": w_trend, "w_align": w_align, "w_vol": w_vol,
        "w_rs": w_rs, "w_prox": w_prox, "raw": float(raw)
    })

    status = "LEADER" if score >= 0.7 else ("WATCH" if score >= 0.45 else "LAGGER")
    return {"score": round(score, 3), "status": status, "diagnostics": diagnostics}


def detect_accumulation(
        df: pd.DataFrame,
        lookback: int = 20,
        up_down_ratio_threshold: float = 1.2
) -> Dict[str, Any]:
    """
    Detects institutional accumulation by analyzing volume flow and closing ranges.
   up_down_ratio: This is the most crucial metric for finding VCPs (Volatility Contraction Patterns) and base-building.
   If a stock is trading sideways for a month, but its up_down_ratio is 1.8,
   it means institutions are quietly vacuuming up shares on the up days and refusing to sell on the down days.

   cmf_20: If this number is consistently above 0.10, it means the stock is repeatedly closing in the top half of its daily range.
   It mathematically proves that intraday short-sellers are getting squeezed out by the closing bell.
    Required columns: Open, High, Low, Close, Volume
    """
    diagnostics: Dict[str, Any] = {}

    if len(df) < lookback:
        return {"status": "INSUFFICIENT_HISTORY", "score": 0.0, "diagnostics": diagnostics}

    # Slice the dataframe to the lookback window to optimize calculations
    window_df = df.iloc[-lookback:].copy()

    # ---------------------------------------------------------
    # 1. Volume Accumulation/Distribution Ratio (Up Vol vs Down Vol)
    # ---------------------------------------------------------
    # Calculate daily price change
    window_df['Change'] = window_df['Close'].diff()

    # Separate volume into Up days and Down days
    up_vol = window_df.loc[window_df['Change'] > 0, 'Volume'].sum()
    down_vol = window_df.loc[window_df['Change'] < 0, 'Volume'].sum()

    # Avoid division by zero
    if down_vol == 0:
        up_down_ratio = 5.0  # Arbitrary high cap if there were strictly no down days
    else:
        up_down_ratio = up_vol / down_vol

    diagnostics['up_vol'] = float(up_vol)
    diagnostics['down_vol'] = float(down_vol)
    diagnostics['up_down_ratio'] = float(up_down_ratio)

    # ---------------------------------------------------------
    # 2. Chaikin Money Flow (CMF) Logic
    # ---------------------------------------------------------
    # Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low)
    # Measures where the stock closes relative to its daily range.
    high_low_range = window_df['High'] - window_df['Low']

    # Prevent division by zero on zero-range days
    mfm = np.where(
        high_low_range > 0,
        ((window_df['Close'] - window_df['Low']) - (window_df['High'] - window_df['Close'])) / high_low_range,
        0.0
    )

    # Money Flow Volume = MFM * Volume
    mfv = mfm * window_df['Volume']

    # CMF = Sum of MFV / Sum of Volume over the period
    total_vol = window_df['Volume'].sum()
    cmf = mfv.sum() / total_vol if total_vol > 0 else 0.0

    diagnostics['cmf_20'] = float(cmf)

    # ---------------------------------------------------------
    # 3. Scoring & Classification
    # ---------------------------------------------------------
    # Score 1: Up/Down Ratio. Normalize against the threshold.
    # A ratio of 1.0 = Neutral. 1.2+ = Accumulation. < 0.8 = Distribution.
    ratio_score = np.clip((up_down_ratio - 0.8) / (up_down_ratio_threshold - 0.8), 0.0, 1.0)

    # Score 2: CMF. Ranges from roughly -0.5 to +0.5.
    # > 0.1 is healthy accumulation. > 0.25 is extreme accumulation.
    cmf_score = np.clip((cmf + 0.1) / 0.35, 0.0, 1.0)

    # Composite Score (Weighting tape action slightly heavier than closing ranges)
    w_ratio = 0.6
    w_cmf = 0.4

    score = (w_ratio * ratio_score) + (w_cmf * cmf_score)
    score = float(np.clip(score, 0.0, 1.0))

    diagnostics['ratio_score'] = float(ratio_score)
    diagnostics['cmf_score'] = float(cmf_score)
    diagnostics['raw_score'] = score

    # Classify the footprint
    if score >= 0.75 and cmf > 0.1:
        status = "HEAVY_ACCUMULATION"
    elif score >= 0.55:
        status = "MODERATE_ACCUMULATION"
    elif score <= 0.25 and cmf < -0.1:
        status = "HEAVY_DISTRIBUTION"
    else:
        status = "NEUTRAL"

    return {"status": status, "score": round(score, 3), "diagnostics": diagnostics}

# =========================================================
# FAKE BREAKOUT FILTER
# =========================================================

def fake_breakout_filter(
        df: pd.DataFrame,
        lookback: int = 60,
        vol_mult: float = 1.5,
        close_top_pct: float = 0.6,
        upper_wick_pct: float = 0.35,
        require_htf_confirm: bool = False,
        htf_df: pd.DataFrame | None = None,
        follow_through_bars: int = 0,
        pre_vol_bars: int = 5
) -> Dict[str, Any]:
    diagnostics: Dict[str, Any] = {}

    # Minimum rows required: lookback + 1 breakout bar + follow_through_bars + margin for vol20/pre5
    min_rows = lookback + 1 + follow_through_bars + max(20, pre_vol_bars)
    if len(df) < min_rows:
        return {"status": "INSUFFICIENT_HISTORY", "score": 0.0, "diagnostics": diagnostics}

    # Convert to positional index to avoid negative-slice surprises
    # breakout_pos is the integer index of the breakout bar within df (0..len-1)
    breakout_pos = len(df) - 1 - follow_through_bars

    # Resistance: highest high in the lookback window excluding breakout bar
    res_start = max(0, breakout_pos - lookback)
    res_end = breakout_pos  # exclusive of breakout_pos
    resistance = df["High"].iloc[res_start:res_end].max()
    diagnostics['resistance'] = float(resistance)

    # Breakout bar metrics
    b = df.iloc[breakout_pos]
    b_high = float(b["High"])
    b_low = float(b["Low"])
    b_close = float(b["Close"])
    b_open = float(b["Open"])
    b_vol = float(b["Volume"])

    diagnostics.update({
        'breakout_pos': int(breakout_pos),
        'breakout_high': b_high,
        'breakout_low': b_low,
        'breakout_close': b_close,
        'breakout_open': b_open,
        'breakout_vol': b_vol
    })

    # Trailing vol20 up to breakout_pos (exclude breakout bar)
    vol20_slice = df["Volume"].iloc[max(0, breakout_pos - 20): breakout_pos]
    vol20 = float(vol20_slice.mean()) if not vol20_slice.empty else float(df["Volume"].iloc[:breakout_pos].mean())
    vol20 = vol20 if (vol20 and not np.isnan(vol20)) else 1.0  # avoid zero division
    diagnostics['vol20'] = float(vol20)

    # Pre-breakout short-term average (n bars immediately before breakout)
    pre_start = max(0, breakout_pos - pre_vol_bars)
    pre5_slice = df["Volume"].iloc[pre_start: breakout_pos]
    pre5_vol_avg = float(pre5_slice.mean()) if not pre5_slice.empty else vol20
    pre5_vol_avg = pre5_vol_avg if (pre5_vol_avg and not np.isnan(pre5_vol_avg)) else vol20
    diagnostics['pre5_vol_avg'] = float(pre5_vol_avg)

    # Breakout attempt and hold
    breakout_attempt = b_high > resistance
    diagnostics['breakout_attempt'] = bool(breakout_attempt)
    if not breakout_attempt:
        return {"status": "NO_BREAKOUT", "score": 0.0, "diagnostics": diagnostics}

    held_at_close = b_close >= resistance  # use >= to allow exact holds
    diagnostics['held_at_close'] = bool(held_at_close)

    # Close position in daily range
    daily_range = b_high - b_low
    close_pos = (b_close - b_low) / daily_range if daily_range > 0 else 1.0
    close_pos = float(np.clip(close_pos, 0.0, 1.0))
    diagnostics['close_pos'] = close_pos

    # Wick / rejection detection
    upper_wick = b_high - max(b_open, b_close)
    upper_wick_pct_of_range = (upper_wick / daily_range) if daily_range > 0 else 0.0
    diagnostics['upper_wick_pct'] = float(upper_wick_pct_of_range)
    # Rejection defined as a large upper wick relative to range AND close is not strong
    rejection = (upper_wick_pct_of_range >= upper_wick_pct) and (close_pos < close_top_pct)
    diagnostics['rejection'] = bool(rejection)

    # Volume checks
    vol_surge_vs_20 = b_vol > (vol20 * vol_mult)
    vol_surge_vs_pre5 = b_vol > (pre5_vol_avg * vol_mult)
    diagnostics['vol_surge_vs_20'] = bool(vol_surge_vs_20)
    diagnostics['vol_surge_vs_pre5'] = bool(vol_surge_vs_pre5)

    # HTF confirmation
    htf_ok = False
    if require_htf_confirm:
        if htf_df is None or len(htf_df) < 1:
            htf_ok = False
        else:
            # Use latest HTF close (assumes htf_df is aligned to same calendar)
            htf_ok = float(htf_df["Close"].iloc[-1]) > resistance
    diagnostics['htf_ok'] = bool(htf_ok)

    # Follow-through: explicitly check the next follow_through_bars after breakout_pos
    follow_through_ok = None
    if follow_through_bars > 0:
        ft_start = breakout_pos + 1
        ft_end = min(len(df), breakout_pos + 1 + follow_through_bars)
        if ft_start < ft_end:
            ft_closes = df["Close"].iloc[ft_start:ft_end]
            # require average close of follow-through bars to be >= breakout close (tunable)
            follow_through_ok = float(ft_closes.mean()) >= b_close
        else:
            follow_through_ok = None
    diagnostics['follow_through_ok'] = follow_through_ok

    # Scoring
    hold_score = 1.0 if held_at_close else 0.0
    if vol_surge_vs_20 and vol_surge_vs_pre5:
        vol_score = 1.0
    elif vol_surge_vs_20 or vol_surge_vs_pre5:
        vol_score = 0.6
    else:
        vol_score = 0.0
    htf_score = 1.0 if htf_ok else 0.0
    rejection_penalty = -0.6 if rejection else 0.0

    if require_htf_confirm:
        w_hold, w_close, w_vol, w_htf = 0.30, 0.30, 0.25, 0.15
    else:
        w_hold, w_close, w_vol, w_htf = 0.35, 0.35, 0.30, 0.0

    raw_score = (w_hold * hold_score) + (w_close * close_pos) + (w_vol * vol_score) + (
                w_htf * htf_score) + rejection_penalty
    score = float(np.clip(raw_score, 0.0, 1.0))

    # Classification
    if not held_at_close:
        status = "FAKE_BREAKOUT" if rejection else "FAILED_BREAKOUT"
    elif score >= 0.8:
        status = "TRUE_BREAKOUT"
    elif score >= 0.55:
        status = "SUSPECT_BREAKOUT"
    else:
        status = "LOW_CONVICTION_BREAKOUT"

    diagnostics.update({
        'hold_score': hold_score,
        'vol_score': vol_score,
        'htf_score': htf_score,
        'rejection_penalty': rejection_penalty,
        'raw_score': float(raw_score)
    })

    return {"status": status, "score": round(score, 3), "diagnostics": diagnostics}


# =========================================================
# EARLY WARNING (-10 DAYS)
# =========================================================

def early_warning(df, k_atr=2.0, vol_mult=1.6, ma_fast=10, ma_mid=60, ma_long=200):
    # df must have: Close, High, Low, Volume, ATR_14, MA10, MA60, MA200, VOL20, MACD_hist, RSI14
    # 1. Macro trend
    if df['Close'].iloc[-1] <= df[f'MA{ma_long}'].iloc[-1]:
        return {'score': 0.0, 'signal': None}

    # 2. Volatility contraction (absolute range vs ATR)
    recent_high = df['High'].tail(5).max()
    recent_low = df['Low'].tail(5).min()
    recent_range = recent_high - recent_low
    dynamic_tight = recent_range < (df['ATR_14'].iloc[-1] * k_atr)

    # 3. Momentum
    slope_fast = slope(df[f'MA{ma_fast}'].tail(10))
    slope_mid = slope(df[f'MA{ma_mid}'].tail(10))
    ma_angle_pos = (slope_fast - slope_mid) > 0
    macd_ok = df['MACD_hist'].iloc[-1] > 0
    rsi_ok = df['RSI14'].iloc[-1] > 50

    # 4. Volume contraction then surge on breakout
    vol_contract = df['Volume'].tail(5).mean() < df['VOL20'].iloc[-1]
    consolidation_high = df['High'].iloc[-6:-1].max()
    breakout_today = df['Close'].iloc[-1] > consolidation_high
    vol_surge = df['Volume'].iloc[-1] > df['VOL20'].iloc[-1] * vol_mult

    # 5. Score components (tunable weights)
    score = (
        0.25 * float(ma_angle_pos) +
        0.20 * float(macd_ok or rsi_ok) +
        0.20 * float(dynamic_tight) +
        0.15 * float(vol_contract) +
        0.20 * float(breakout_today and vol_surge)
    )

    signal = None
    if score >= 0.75 and breakout_today and vol_surge:
        signal = 'IMMEDIATE_BUY'
    elif score >= 0.6:
        signal = 'WATCHLIST'
    return {'score': round(score, 3), 'signal': signal}



# =========================================================
# MAIN SCAN
# =========================================================

def run(tickers : list,output_file = "EMA_Trend.csv"):
    load_symbol_sector()
    if not market_ok():
        print("❌ Market regime not favorable")
        return

    print("\n🔥 MARKET OK — SCANNING...\n")

    results = []

    sector_cache = {}

    for ticker in tickers:

        df = load_data(ticker)
        if df is None or len(df) < 10:
            continue
        try:
            sector = symbol_and_industry[ticker]
            if sector not in sector_cache:
                sector_cache[sector] = sector_score(sector)

            sec_score = sector_cache[sector]

            core_result = leader_structure(df, my_slope)
            core = core_result.get('score', 0.0)
            core_signal = core_result.get('status', None)
            fake = fake_breakout_filter(df)
            fake_break_score = fake.get('score', 0.0)
            fake_break_signal = fake.get('status', None)
            accumulation_result = detect_accumulation(df)
            accumulation = accumulation_result.get('score', 0.0)
            accumulation_signal = accumulation_result.get('status', None)

            result = early_warning(df)
            early = result.get('score', 0.0)
            buy_signal = result.get('signal', None)
        except Exception as e:
            print(f"eam error: {ticker}",  e)
            traceback.print_exc()
            continue
        total = (
            0.55*core +
            0.25*fake_break_score +
            0.20*early
        ) * (1 + sec_score)

        results.append((ticker, total, sec_score, core,core_signal, fake_break_score,fake_break_signal, early,buy_signal,accumulation,accumulation_signal))

    print("================================")
    print("🔥 LEADER ROTATION RANKING")
    print("================================")
    results_sorted = sorted(results, key=lambda x:x[1], reverse=True)

    df =pd.DataFrame(results_sorted, columns=["symbol", "score", "sec_score", "core", "core_signal","fake_break_score","fake_break_signal" ,"early","buy_signal" ,"accumulation","accumulation_signal"])
    # print(df)
    df.to_csv(output_file, index=False)

# =========================================================

if __name__ == "__main__":
    watch_list = pd.read_csv(f"resource/nyse_and_nasdaq_top_500.csv")['symbol'].tolist()
    run(watch_list)
