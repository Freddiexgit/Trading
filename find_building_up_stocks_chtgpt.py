import numpy as np
import pandas as pd
import yfinance as yf
import data_downloader as dd
import traceback as tb
from scipy.stats import linregress


# ============================================================
# DATA LOADER (yfinance)
# ============================================================

def get_data(ticker, period="2y"):
    df = dd.get_transaction_df(ticker)

    if df is None or df.empty:
        return None
    # Drop any duplicated columns that may arise from merging
    df = df.loc[:, ~df.columns.duplicated()]

    df = df.dropna()
    return df


def calculate_obv(df):
    direction = np.sign(df["Close"].diff()).fillna(0)
    df["OBV"] = (direction * df["Volume"]).cumsum()
    return df


def calculate_atr(df, period=14):
    hl = df["High"] - df["Low"]
    hc = np.abs(df["High"] - df["Close"].shift())
    lc = np.abs(df["Low"] - df["Close"].shift())
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def add_bb_width(df, window=20):
    sma = df["Close"].rolling(window).mean()
    std = df["Close"].rolling(window).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    df["BB_Width"] = (upper - lower) / sma
    return df


def calculate_relative_strength(df,spy_df):
    """
    Simple RS vs own history trend (proxy version)
    """
    """
        Calculates True Relative Strength vs the S&P 500 using O'Neil style weighting.
        """
    if len(df) < 252 or len(spy_df) < 252:
        return 0

    # Align dates between stock and SPY to ensure accurate division
    aligned_data = pd.concat([df['Close'], spy_df['Close']], axis=1, join='inner').dropna()
    if len(aligned_data) < 252:
        return 0

    stock_close = aligned_data.iloc[:, 0]
    spy_close = aligned_data.iloc[:, 1]

    # Create the Relative Ratio Line
    ratio = stock_close / spy_close

    current_ratio = float(ratio.iloc[-1])

    # Calculate performance of the ratio across timeframes
    r3 = (current_ratio / float(ratio.iloc[-63])) - 1
    r6 = (current_ratio / float(ratio.iloc[-126])) - 1
    r9 = (current_ratio / float(ratio.iloc[-189])) - 1
    r12 = (current_ratio / float(ratio.iloc[-252])) - 1

    # Apply O'Neil style momentum weighting
    return (r3 * 0.40) + (r6 * 0.20) + (r9 * 0.20) + (r12 * 0.20)


# ============================================================
# PATTERN DETECTION
# ============================================================

def detect_vcp(df):
    if len(df) < 60:
        return False

    # Force cast to float to prevent Series truth value ambiguity
    r1 = float((df["High"].iloc[-60:-40].max() - df["Low"].iloc[-60:-40].min()) / df["Low"].iloc[-60:-40].min())
    r2 = float((df["High"].iloc[-40:-20].max() - df["Low"].iloc[-40:-20].min()) / df["Low"].iloc[-40:-20].min())
    r3 = float((df["High"].iloc[-20:].max() - df["Low"].iloc[-20:].min()) / df["Low"].iloc[-20:].min())

    # Break up chained comparisons into explicit boolean logic
    return (r1 > r2) and (r2 > r3) and (r2 < r1 * 0.8) and (r3 < r2 * 0.8)


def check_pocket_pivot(df):
    if len(df) < 20:
        return False

    for i in range(1, 4):
        idx = -i
        today_vol = float(df["Volume"].iloc[idx])
        prior = df.iloc[idx - 11: idx - 1]

        down = prior[prior["Close"] < prior["Close"].shift()]
        if len(down) == 0:
            continue

        max_down_vol = float(down["Volume"].max())
        if today_vol > max_down_vol:
            return True

    return False


def breakout_trigger(df):
    if len(df) < 30:
        return False

    resistance = float(df["High"].iloc[-50:-1].max())
    price = float(df["Close"].iloc[-1])
    return price > resistance


def classify_stage(df):
    if len(df) < 200:
        return "Unknown"

    price = float(df["Close"].iloc[-1])
    sma50 = float(df["Close"].rolling(50).mean().iloc[-1])
    sma150 = float(df["Close"].rolling(150).mean().iloc[-1])
    sma200 = float(df["Close"].rolling(200).mean().iloc[-1])

    # Unchain comparisons
    trend = (price > sma50) and (sma50 > sma150) and (sma150 > sma200)

    recent_range = float(df["High"].iloc[-20:].max() - df["Low"].iloc[-20:].min())
    past_range = float(df["High"].iloc[-100:-20].max() - df["Low"].iloc[-100:-20].min())
    tightening = recent_range < (past_range * 0.6)

    if breakout_trigger(df) and trend:
        return "Stage 3"
    if trend:
        return "Stage 2"
    if tightening:
        return "Stage 1"
    return "Stage 4"


# ============================================================
# MACRO
# ============================================================

def fetch_macro_environment():
    spy = dd.get_transaction_df("SPY")
    hyg = dd.get_transaction_df("HYG")

    ratio = hyg["Close"] / spy["Close"]
    risk_on = (ratio > ratio.rolling(20).mean()).tail(3).all()

    # Guarantee scalar boolean
    if isinstance(risk_on, pd.Series):
        risk_on = risk_on.iloc[0]

    return {"SPY": spy, "HYG": hyg}, bool(risk_on)


# ============================================================
# RANKING
# ============================================================
def check_ttm_squeeze(df, length=20):
    if len(df) < length:
        return False

    # Bollinger Bands (2 Standard Deviations)
    sma = df["Close"].rolling(length).mean()
    std = df["Close"].rolling(length).std()
    bb_upper = sma + (2.0 * std)
    bb_lower = sma - (2.0 * std)

    # Keltner Channels (1.5 ATR)
    atr = df["ATR"]  # Assuming calculate_atr() has already been run on df
    kc_upper = sma + (1.5 * atr)
    kc_lower = sma - (1.5 * atr)

    # The Squeeze is ON when BB is completely inside KC
    squeeze_on = (bb_upper < kc_upper) & (bb_lower > kc_lower)

    # Return true if we are currently in a squeeze
    return bool(squeeze_on.iloc[-1])

def build_rs_rank(tickers,spy_df=None):
    scores = []

    for t in tickers:
        df = get_data(t)
        if df is None or len(df) < 252:
            continue

        scores.append((t, calculate_relative_strength(df, spy_df)))

    if not scores:
        return {}

    rs_df = pd.DataFrame(scores, columns=["ticker", "rs"])
    rs_df["rank"] = rs_df["rs"].rank(pct=True) * 100

    return dict(zip(rs_df["ticker"], rs_df["rank"]))


def classify_stage(df):
    if len(df) < 220:  # Need extra buffer for SMA lookbacks
        return "Unknown"

    price = float(df["Close"].iloc[-1])
    sma50 = float(df["Close"].rolling(50).mean().iloc[-1])
    sma150 = float(df["Close"].rolling(150).mean().iloc[-1])
    sma200 = float(df["Close"].rolling(200).mean().iloc[-1])

    # Check if 200 SMA is actually trending up (current > 20 days ago)
    sma200_20d_ago = float(df["Close"].rolling(200).mean().shift(20).iloc[-1])
    sma200_rising = sma200 > sma200_20d_ago

    # True Minervini Trend Template
    trend = (price > sma50) and (sma50 > sma150) and (sma150 > sma200) and sma200_rising

    recent_range = float(df["High"].iloc[-20:].max() - df["Low"].iloc[-20:].min())
    past_range = float(df["High"].iloc[-100:-20].max() - df["Low"].iloc[-100:-20].min())
    tightening = recent_range < (past_range * 0.6)

    if breakout_trigger(df) and trend:
        return "Stage 3 (Breakout)"
    if trend:
        return "Stage 2 (Advancing)"
    if tightening:
        return "Stage 1 (Basing)"
    return "Stage 4 (Declining)"


def detect_accumulation(ticker, rs_map, risk_on):
    df = get_data(ticker)

    if df is None or len(df) < 200:
        return None

    df = calculate_obv(df)
    df["ATR"] = calculate_atr(df)
    df = add_bb_width(df)

    price = float(df["Close"].iloc[-1])

    # =========================
    # UPGRADED CORE METRICS
    # =========================

    rs_rank = float(rs_map.get(ticker, 0))
    stage_val = classify_stage(df)
    vcp_signal = bool(detect_vcp(df))
    pocket = bool(check_pocket_pivot(df))
    breakout = bool(breakout_trigger(df))

    # 1. Recent Liquidity
    liquidity = float((df["Close"] * df["Volume"]).tail(50).mean()) > 2_000_000

    # 2. Time-Bounded Up/Down Volume (Last 50 days only)
    recent_df = df.tail(50)
    up_vol = float(recent_df[recent_df["Close"] > recent_df["Close"].shift()]["Volume"].sum())
    down_vol = float(recent_df[recent_df["Close"] < recent_df["Close"].shift()]["Volume"].sum())
    ud_ratio = up_vol / max(down_vol, 1.0)

    # 3. Utilize OBV: Is accumulation trending up over the last month?
    # Simple linear regression slope of OBV
    obv_slope = linregress(range(20), df["OBV"].tail(20))[0]
    obv_rising = obv_slope > 0

    # 4. Utilize BB Width: Is price squeezing?
    current_bb_width = float(df["BB_Width"].iloc[-1])
    avg_bb_width = float(df["BB_Width"].rolling(50).mean().iloc[-1])
    bb_squeeze = current_bb_width < (avg_bb_width * 0.8)  # 20% tighter than usual

    institutional = pocket or (ud_ratio > 1.2) or obv_rising

    max_high = float(df["High"].tail(252).max())
    near_high = ((max_high - price) / max_high) < 0.25 if max_high > 0 else False

    trend = "Stage 2" in stage_val or "Stage 3" in stage_val

    vol_50d_avg = float(df["Volume"].rolling(50).mean().iloc[-1])
    vol_3d_avg = float(df["Volume"].tail(3).mean())
    volume_dry_up = vol_3d_avg < (vol_50d_avg * 0.5)

    # 2. TTM Squeeze (Extreme Tightness)
    is_squeezing = check_ttm_squeeze(df)


    # =========================
    # UPGRADED SOFT SCORE MODEL
    # =========================
    score = 0

    # RS scoring
    if rs_rank >= 50: score += 1
    if rs_rank >= 70: score += 2
    if rs_rank >= 85: score += 3
    if rs_rank >= 95: score += 4

    # Structure & Volume Evidence
    score += int(vcp_signal) * 2
    score += int(bb_squeeze) * 2  # Newly activated
    score += int(obv_rising) * 1  # Newly activated
    score += int(breakout) * 2
    score += int(pocket) * 2
    score += int(institutional) * 2
    score += int(trend) * 2
    score += int(near_high) * 1
    score += int(liquidity) * 2
    score += int(risk_on) * 1
    score += int(volume_dry_up) * 1
    score += int(is_squeezing) * 2

    # =========================
    # RATING ADJUSTMENT
    # =========================
    # Adjusted thresholds since max possible score is now higher
    if score >= 16:
        rating = "Elite Accumulation"
    elif score >= 12:
        rating = "Institutional Accumulation"
    elif score >= 8:
        rating = "Strong Setup"
    elif score >= 5:
        rating = "Watchlist"
    else:
        rating = "Ignore"

    return {
        "symbol": ticker,
        "score": score,
        "rating": rating,
        "stage": stage_val,
        "ud_ratio": round(ud_ratio, 2),  # Good to see in final output
        "rs_rank": round(rs_rank, 1),
        "bb_squeeze": bb_squeeze,
        "obv_rising": obv_rising,
        "pocket": pocket,
        "open": df["Open"].iloc[-1],
        "close": df["Close"].iloc[-1],
         "volume": df["Volume"].iloc[-1],
         "date": df.index[-1].strftime("%Y-%m-%d")
    }
# ============================================================
# MAIN
# ============================================================

def main(input_file=None, output_file=None):
    if input_file:
        tickers = pd.read_csv(input_file)["symbol"].dropna().tolist()
    else:
        tickers = ["HRMY", "FVCB"]

    print(f"Loaded {len(tickers)} tickers")

    macro, risk_on = fetch_macro_environment()
    rs_map = build_rs_rank(tickers, macro["SPY"])

    results = []

    for i, t in enumerate(tickers):
        if i % 100 == 0:
            print(f"{i}/{len(tickers)}")
        try:
            r = detect_accumulation(t, rs_map, risk_on)
            if r:
                results.append(r)
        except Exception as e:
            print(f"Error processing {t}: {e}")
            tb.print_exc()
            continue

    if len(results) == 0:
        print("No stocks passed the screening criteria.")
        return

    df = pd.DataFrame(results)
    df = df.sort_values(["score", "rs_rank"], ascending=False)

    if output_file:
        df.to_csv(output_file, index=False)
    else:
        print(df.head(50))


if __name__ == "__main__":
    main()