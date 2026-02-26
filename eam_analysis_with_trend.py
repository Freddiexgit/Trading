# =========================================================
# INSTITUTIONAL LEADER ROTATION RADAR
# =========================================================


import pandas as pd
import numpy as np

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

    etf = industry_score.SECTOR_ETF[sector]

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

def leader_structure(df):

    trend = slope(df["MA60"].tail(60))
    alignment = (
        df["MA10"].iloc[-1] >
        df["MA20"].iloc[-1] >
        df["MA50"].iloc[-1]
    )

    volume_expansion = safe_div(
        df["Volume"].iloc[-1],
        df["VOL20"].iloc[-1]
    )

    score = (
        0.5*trend +
        0.3*alignment +
        0.2*volume_expansion
    )

    return score


# =========================================================
# FAKE BREAKOUT FILTER
# =========================================================
from typing import Dict, Any
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

def run(tickers : list,output_file = "leader_rotation.csv"):
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

            core = leader_structure(df)
            fake = fake_breakout_filter(df)
            fake_break_score = fake.get('score', 0.0)
            fake_break_signal = fake.get('status', None)

            result = early_warning(df)
            early = result.get('score', 0.0)
            buy_signal = result.get('signal', None)
        except Exception as e:
            print(f"eam error: {ticker}",  e)
            continue
        total = (
            0.55*core +
            0.25*fake_break_score +
            0.20*early
        ) * (1 + sec_score)

        results.append((ticker, total, sec_score, core, fake,fake_break_score,fake_break_signal, early,buy_signal))

    print("================================")
    print("🔥 LEADER ROTATION RANKING")
    print("================================")
    results_sorted = sorted(results, key=lambda x:x[1], reverse=True)

    df =pd.DataFrame(results_sorted, columns=["symbol", "score", "sec_score", "core", "fake","fake_break_score","fake_break_signal" ,"early","buy_signal"])
    # print(df)
    df.to_csv(output_file, index=False)

# =========================================================

if __name__ == "__main__":
    current_dir = os.getcwd()
    print(f"Current Directory: {current_dir}")
    # watch_list = pd.read_csv(f"../resource/my_vip.csv")['symbol'].tolist()
    watch_list = ["AAPL"]

    run(watch_list)
