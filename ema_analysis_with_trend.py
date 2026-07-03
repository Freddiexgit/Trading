# =========================================================
# INSTITUTIONAL LEADER ROTATION RADAR (V2 - WITH OBV & EMA SYNCHRONIZATION)
# =========================================================

import os
import traceback
import pandas as pd
import numpy as np
from collections import defaultdict
from typing import Dict, Any

import data_downloader
from analytics import industry_score

# ---------------- CONFIG ----------------

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

MARKET_ETF = "QQQ"

industry_and_symbol = defaultdict(list)
symbol_and_industry = {}


def load_symbol_sector():
    base_dir = "resource/industries/"
    if not os.path.exists(base_dir):
        return
    for file in os.listdir(base_dir):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(base_dir, file))
            industry_and_symbol[file.replace(".csv", "")] = df["symbol"].tolist()
            for key, values in industry_and_symbol.items():
                for val in values:
                    symbol_and_industry[val] = key


# ---------------- UTIL ----------------

def safe_div(a: float, b: float, fallback: float = 0.0) -> float:
    try:
        return float(a) / float(b) if b not in (0, None, np.nan) else float(fallback)
    except Exception:
        return float(fallback)


def safe_mean(series: pd.Series, fallback: float = 0.0) -> float:
    v = series.dropna()
    return float(v.mean()) if not v.empty else float(fallback)


def normalize(x: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 0.0
    return float(np.clip((x - lo) / (hi - lo), 0.0, 1.0))


def my_pct_slope(series):
    """Scale-invariant slope calculated on percentage change."""
    y = series.dropna().values
    if len(y) < 2 or y[0] == 0:
        return 0.0

    y_norm = (y / y[0]) - 1
    x = np.arange(len(y_norm))

    slope_val, _ = np.polyfit(x, y_norm, 1)
    return slope_val * 100


def add_atr(df, period=14):
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = np.abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = np.abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR_14'] = df['TR'].rolling(window=period).mean()
    df.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1, inplace=True)
    return df


def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def add_macd_hist(df, fast=12, slow=26, signal=9, price_col='Close'):
    ema_fast = df[price_col].ewm(span=fast, adjust=False).mean()
    ema_slow = df[price_col].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    df['MACD'] = macd_line
    df['MACD_signal'] = signal_line
    df['MACD_hist'] = macd_line - signal_line
    return df


def add_obv(df):
    """Calculates On-Balance Volume (OBV)."""
    change = df['Close'].diff()
    direction = np.where(change > 0, 1, np.where(change < 0, -1, 0))
    df['OBV'] = (direction * df['Volume']).cumsum()
    df['OBV_EMA20'] = df['OBV'].ewm(span=20, adjust=False).mean()
    return df


def load_data(ticker):
    df = data_downloader.get_transaction_df(ticker)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if df is None or df.empty:
        return pd.DataFrame()

    if len(df) < 200:
        df["MA200"] = df["Close"].rolling(65).mean()
    else:
        df["MA200"] = df["Close"].rolling(200).mean()

    # Core Trend Ribbon: Standardized to EMAs
    df["EMA10"] = df["Close"].ewm(span=10, adjust=False).mean()
    df["EMA21"] = df["Close"].ewm(span=21, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    df["VOL20"] = df["Volume"].rolling(20).mean()
    df = add_atr(df)
    df["RSI14"] = rsi(df["Close"], 14)
    df = add_macd_hist(df)
    df = add_obv(df)

    return df


# =========================================================
# MARKET REGIME FILTER
# =========================================================

def market_ok():
    spy = load_data(MARKET_ETF)
    if spy.empty: return False
    close = float(spy["Close"].iloc[-1])
    ema50 = float(spy["EMA50"].iloc[-1])
    ma200 = float(spy["MA200"].iloc[-1])

    cond1 = close > ma200
    cond2 = ema50 > ma200

    return bool(cond1 and cond2)


# =========================================================
# SECTOR ROTATION ENGINE
# =========================================================

def sector_relative_strength(sector_etf):
    sec_df = load_data(sector_etf)
    mkt_df = load_data(MARKET_ETF)
    if sec_df.empty or mkt_df.empty: return 0.0

    rs = sec_df["Close"] / mkt_df["Close"]
    return my_pct_slope(rs.tail(90))


def sector_breadth(tickers):
    signals = []
    for t in tickers:
        try:
            df = load_data(t)
            if not df.empty:
                signals.append(df["Close"].iloc[-1] > df["EMA50"].iloc[-1])
        except:
            pass
    if len(signals) == 0:
        return np.nan
    return np.mean(signals)


def sector_score(sector):
    etf = industry_score.SECTOR_ETF.get(sector, "SPY") if hasattr(industry_score, 'SECTOR_ETF') else "SPY"
    rs = sector_relative_strength(etf)

    members = industry_and_symbol.get(sector, [])
    if len(members) >= 10:
        members = members[:10]
    breadth = sector_breadth(members)

    score = 0.6 * rs + 0.4 * (breadth if not np.isnan(breadth) else 0)
    return score


# =========================================================
# LEADER STRUCTURE SCORE
# =========================================================

def leader_structure(
        df: pd.DataFrame,
        slope_func,
        lookback_trend: int = 60,
        vol_window: int = 20,
        ma_fast: str = "EMA10",
        ma_mid: str = "EMA21",
        ma_slow: str = "EMA50",
        ma_macro: str = "MA200"
) -> Dict[str, Any]:
    diagnostics: Dict[str, Any] = {}
    required = {ma_fast, ma_mid, ma_slow, ma_macro, "Close", "Volume"}
    missing = required - set(df.columns)
    if missing:
        return {"score": 0.0, "status": "MISSING_COLUMNS", "diagnostics": {"missing": list(missing)}}

    if len(df) < lookback_trend:
        return {"score": 0.0, "status": "INSUFFICIENT_HISTORY", "diagnostics": {"len": len(df)}}

    last = df.iloc[-1]

    # 1. Macro trend filter
    macro_up = bool(last["Close"] > df[ma_macro].iloc[-1])
    diagnostics["macro_up"] = macro_up

    # 2. Trend strength
    try:
        trend_series = df[ma_slow].iloc[-lookback_trend:]
        trend_raw = float(slope_func(trend_series))
    except Exception:
        trend_raw = 0.0
    diagnostics["trend_raw"] = trend_raw

    slopes = []
    window = max(lookback_trend, 60)
    for i in range(window, len(df) + 1, max(1, window // 4)):
        seg = df[ma_slow].iloc[max(0, i - window):i]
        if len(seg) >= 2:
            try:
                slopes.append(abs(float(slope_func(seg))))
            except Exception:
                pass
    slope_scale = max(np.percentile(slopes, 75) if slopes else 1.0, 1e-6)
    trend_norm = float(np.clip(trend_raw / slope_scale, -1.0, 1.0))
    trend_score = float(np.clip((trend_norm + 1) / 2, 0.0, 1.0))
    diagnostics["trend_score"] = trend_score
    diagnostics["slope_scale"] = float(slope_scale)

    # 3. Moving average alignment & EXPANSION
    is_stacked = (last[ma_fast] > last[ma_mid]) and (last[ma_mid] > last[ma_slow])

    if len(df) >= 5:
        current_spread = last[ma_fast] - last[ma_slow]
        past_spread = df[ma_fast].iloc[-5] - df[ma_slow].iloc[-5]
        is_expanding = current_spread > past_spread
    else:
        is_expanding = False

    slow_slope_val = last[ma_slow] - df[ma_slow].iloc[-5]
    slow_pointing_up = slow_slope_val > 0

    alignment_bool = is_stacked and is_expanding and slow_pointing_up
    alignment_score = 1.0 if alignment_bool else (0.5 if is_stacked else 0.0)

    diagnostics["alignment_bool"] = alignment_bool
    diagnostics["is_expanding"] = is_expanding

    # 4. Volume expansion
    vol20 = safe_mean(df["Volume"].iloc[-vol_window:], fallback=1.0)
    vol_expansion = safe_div(last["Volume"], vol20, fallback=0.0)
    vol_score = float(np.clip((vol_expansion - 1.0) / (3.0 - 1.0), 0.0, 1.0))
    diagnostics["vol_score"] = vol_score

    # 5. Relative strength
    rs = safe_div(last["Close"], last[ma_slow], fallback=1.0)
    rs_score = normalize(rs, 0.95, 1.15)
    diagnostics["rs_score"] = rs_score

    # 6. Proximity to breakout
    recent_high = df["High"].iloc[-lookback_trend:].max() if "High" in df.columns else last["Close"]
    proximity = safe_div(last["Close"], recent_high, fallback=1.0)
    proximity_score = normalize(proximity, 0.9, 1.02)
    diagnostics["proximity_score"] = proximity_score

    # 7. Composite weighting
    w_trend = 0.35
    w_align = 0.20
    w_vol = 0.15
    w_rs = 0.15
    w_prox = 0.15

    raw = (
                w_trend * trend_score + w_align * alignment_score + w_vol * vol_score + w_rs * rs_score + w_prox * proximity_score)

    if not macro_up:
        raw *= 0.6
        diagnostics["macro_penalty_applied"] = True
    else:
        diagnostics["macro_penalty_applied"] = False

    score = float(np.clip(raw, 0.0, 1.0))
    status = "LEADER" if score >= 0.7 else ("WATCH" if score >= 0.45 else "LAGGER")

    return {"score": round(score, 3), "status": status, "diagnostics": diagnostics}


# =========================================================
# ACCUMULATION FOOTPRINT
# =========================================================

def detect_accumulation(df: pd.DataFrame, lookback: int = 20, up_down_ratio_threshold: float = 1.2) -> Dict[str, Any]:
    diagnostics: Dict[str, Any] = {}
    if len(df) < lookback:
        return {"status": "INSUFFICIENT_HISTORY", "score": 0.0, "diagnostics": diagnostics}

    window_df = df.iloc[-lookback:].copy()

    # 1. Volume Accumulation/Distribution Ratio
    window_df['Change'] = window_df['Close'].diff()
    up_vol = window_df.loc[window_df['Change'] > 0, 'Volume'].sum()
    down_vol = window_df.loc[window_df['Change'] < 0, 'Volume'].sum()
    up_down_ratio = 5.0 if down_vol == 0 else up_vol / down_vol

    # 2. Chaikin Money Flow (CMF)
    high_low_range = window_df['High'] - window_df['Low']
    mfm = np.where(high_low_range > 0, (
                (window_df['Close'] - window_df['Low']) - (window_df['High'] - window_df['Close'])) / high_low_range,
                   0.0)
    mfv = mfm * window_df['Volume']
    total_vol = window_df['Volume'].sum()
    cmf = mfv.sum() / total_vol if total_vol > 0 else 0.0

    # 3. Scoring
    ratio_score = np.clip((up_down_ratio - 0.8) / (up_down_ratio_threshold - 0.8), 0.0, 1.0)
    cmf_score = np.clip((cmf + 0.1) / 0.35, 0.0, 1.0)
    score = float(np.clip((0.6 * ratio_score) + (0.4 * cmf_score), 0.0, 1.0))

    if score >= 0.75 and cmf > 0.1:
        status = "HEAVY_ACCUMULATION"
    elif score >= 0.55:
        status = "MODERATE_ACCUMULATION"
    elif score <= 0.25 and cmf < -0.1:
        status = "HEAVY_DISTRIBUTION"
    else:
        status = "NEUTRAL"

    diagnostics.update({'up_down_ratio': float(up_down_ratio), 'cmf_20': float(cmf)})
    return {"status": status, "score": round(score, 3), "diagnostics": diagnostics}


# =========================================================
# FAKE BREAKOUT FILTER (WITH OBV)
# =========================================================

def fake_breakout_filter(
        df: pd.DataFrame,
        lookback: int = 60,
        vol_mult: float = 1.5,
        close_top_pct: float = 0.6,
        upper_wick_pct: float = 0.35,
        follow_through_bars: int = 0,
        pre_vol_bars: int = 5
) -> Dict[str, Any]:
    diagnostics: Dict[str, Any] = {}

    min_rows = lookback + 1 + follow_through_bars + max(20, pre_vol_bars)
    if len(df) < min_rows or "OBV" not in df.columns:
        return {"status": "INSUFFICIENT_HISTORY", "score": 0.0, "diagnostics": diagnostics}

    breakout_pos = len(df) - 1 - follow_through_bars

    # 1. Price Resistance
    res_start = max(0, breakout_pos - lookback)
    res_end = breakout_pos
    resistance = df["High"].iloc[res_start:res_end].max()

    # 2. OBV Resistance
    obv_resistance = df["OBV"].iloc[res_start:res_end].max()

    b = df.iloc[breakout_pos]
    b_high, b_low, b_close, b_open, b_vol, b_obv = b["High"], b["Low"], b["Close"], b["Open"], b["Volume"], b["OBV"]

    # Breakout check
    if b_high <= resistance:
        return {"status": "NO_BREAKOUT", "score": 0.0, "diagnostics": diagnostics}

    held_at_close = b_close >= resistance

    # OBV Confirmation
    obv_breakout = b_obv >= obv_resistance
    obv_trending_up = b_obv > float(b["OBV_EMA20"])

    # Price Structure
    daily_range = b_high - b_low
    close_pos = float(np.clip((b_close - b_low) / daily_range if daily_range > 0 else 1.0, 0.0, 1.0))
    upper_wick = b_high - max(b_open, b_close)
    upper_wick_pct_of_range = (upper_wick / daily_range) if daily_range > 0 else 0.0
    rejection = (upper_wick_pct_of_range >= upper_wick_pct) and (close_pos < close_top_pct)

    # Volume Surge
    vol20_slice = df["Volume"].iloc[max(0, breakout_pos - 20): breakout_pos]
    vol20 = float(vol20_slice.mean()) if not vol20_slice.empty else 1.0
    vol_surge_vs_20 = b_vol > (vol20 * vol_mult)

    # Scoring
    hold_score = 1.0 if held_at_close else 0.0
    vol_score = 1.0 if vol_surge_vs_20 else 0.0

    if obv_breakout and obv_trending_up:
        obv_score = 1.0
    elif obv_breakout or obv_trending_up:
        obv_score = 0.5
    else:
        obv_score = 0.0

    rejection_penalty = -0.6 if rejection else 0.0
    raw_score = (0.30 * hold_score) + (0.25 * close_pos) + (0.20 * vol_score) + (0.25 * obv_score) + rejection_penalty
    score = float(np.clip(raw_score, 0.0, 1.0))

    if not held_at_close:
        status = "FAKE_BREAKOUT" if rejection else "FAILED_BREAKOUT"
    elif score >= 0.8:
        status = "TRUE_BREAKOUT"
    elif score >= 0.55:
        status = "SUSPECT_BREAKOUT"
    else:
        status = "LOW_CONVICTION_BREAKOUT"

    return {"status": status, "score": round(score, 3), "diagnostics": diagnostics}


# =========================================================
# EARLY WARNING (-10 DAYS)
# =========================================================

def early_warning(df, k_atr=2.0, vol_mult=1.6, ma_fast="EMA10", ma_mid="EMA50", ma_long="MA200"):
    if df['Close'].iloc[-1] <= df[ma_long].iloc[-1]:
        return {'score': 0.0, 'signal': None}

    recent_high = df['High'].tail(5).max()
    recent_low = df['Low'].tail(5).min()
    recent_range = recent_high - recent_low
    dynamic_tight = recent_range < (df['ATR_14'].iloc[-1] * k_atr)

    slope_fast = my_pct_slope(df[ma_fast].tail(10))
    slope_mid = my_pct_slope(df[ma_mid].tail(10))
    ma_angle_pos = (slope_fast - slope_mid) > 0
    macd_ok = df['MACD_hist'].iloc[-1] > 0
    rsi_ok = df['RSI14'].iloc[-1] > 50

    vol_contract = df['Volume'].tail(5).mean() < df['VOL20'].iloc[-1]
    consolidation_high = df['High'].iloc[-6:-1].max()
    breakout_today = df['Close'].iloc[-1] > consolidation_high
    vol_surge = df['Volume'].iloc[-1] > df['VOL20'].iloc[-1] * vol_mult

    score = (0.25 * float(ma_angle_pos) + 0.20 * float(macd_ok or rsi_ok) + 0.20 * float(dynamic_tight) + 0.15 * float(
        vol_contract) + 0.20 * float(breakout_today and vol_surge))

    signal = None
    if score >= 0.75 and breakout_today and vol_surge:
        signal = 'IMMEDIATE_BUY'
    elif score >= 0.6:
        signal = 'WATCHLIST'

    return {'score': round(score, 3), 'signal': signal}


# =========================================================
# MAIN SCAN
# =========================================================

def run(tickers: list, output_file):
    load_symbol_sector()

    results = []
    sector_cache = {}

    for ticker in tickers:
        try:
            df = load_data(ticker)
        except Exception as e:
            print(f"Data load error: {ticker}", e)
            continue

        if df is None or len(df) < 10:
            continue

        try:
            sector = symbol_and_industry.get(ticker, "Unknown")
            if sector not in sector_cache:
                sector_cache[sector] = sector_score(sector)
            sec_score = sector_cache[sector]

            core_result = leader_structure(df, my_pct_slope)
            core, core_signal = core_result.get('score', 0.0), core_result.get('status', None)

            fake = fake_breakout_filter(df)
            fake_break_score, fake_break_signal = fake.get('score', 0.0), fake.get('status', None)

            accumulation_result = detect_accumulation(df)
            accumulation, accumulation_signal = accumulation_result.get('score', 0.0), accumulation_result.get('status',
                                                                                                               None)

            early_res = early_warning(df)
            early, buy_signal = early_res.get('score', 0.0), early_res.get('signal', None)

        except Exception as e:
            print(f"Calculation error: {ticker}", e)
            traceback.print_exc()
            continue

        total = (0.55 * core + 0.25 * fake_break_score + 0.20 * early) * (1 + sec_score)
        results.append(
            (ticker, total, sec_score, core, core_signal, fake_break_score, fake_break_signal, early, buy_signal,
             accumulation, accumulation_signal))

    print("==========================================")
    print("🔥 LEADER ROTATION RANKING (OBV VALIDATED)")
    print("==========================================")

    results_sorted = sorted(results, key=lambda x: x[1], reverse=True)
    df_out = pd.DataFrame(results_sorted, columns=[
        "symbol", "score", "sec_score", "core", "core_signal",
        "fake_break_score", "fake_break_signal", "early", "buy_signal",
        "accumulation", "accumulation_signal"
    ])
    if output_file is None:
        print(df_out)
    else:
        df_out.to_csv(output_file, index=False)
    print(f"Scan complete. Results saved to {output_file}")


# =========================================================

if __name__ == "__main__":
    watch_list = ["DSWL"]
    run(watch_list,None)