import numpy as np
import pandas as pd
import yfinance as yf
import data_downloader as dd
import traceback as tb
from scipy.stats import linregress

# ============================================================
# DATA LOADER
# ============================================================

def get_data(ticker, period="2y"):
    df = dd.get_transaction_df(ticker)
    if df is None or df.empty:
        return None
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.dropna()
    return df

def get_industry(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("industry", "Unknown")
    except:
        return "Unknown"

# ============================================================
# TECHNICAL INDICATORS
# ============================================================

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

# ============================================================
# RELATIVE STRENGTH
# ============================================================

def calculate_relative_strength(df, spy_df):
    if len(df) < 252 or len(spy_df) < 252:
        return 0

    aligned = pd.concat([df['Close'], spy_df['Close']], axis=1, join='inner').dropna()
    if len(aligned) < 252:
        return 0

    stock = aligned.iloc[:, 0]
    spy = aligned.iloc[:, 1]
    ratio = stock / spy
    current = float(ratio.iloc[-1])

    r3 = current / float(ratio.iloc[-63]) - 1
    r6 = current / float(ratio.iloc[-126]) - 1
    r9 = current / float(ratio.iloc[-189]) - 1
    r12 = current / float(ratio.iloc[-252]) - 1

    return (r3 * 0.40) + (r6 * 0.20) + (r9 * 0.20) + (r12 * 0.20)

# ============================================================
# INDUSTRY MOMENTUM ENGINE
# ============================================================

def build_industry_momentum(tickers):
    industry_map = {}
    for t in tickers:
        ind = get_industry(t)
        industry_map.setdefault(ind, []).append(t)

    spy = dd.get_transaction_df("SPY")
    spy_3m = spy["Close"].iloc[-1] / spy["Close"].iloc[-63] - 1

    industry_scores = {}

    for ind, group in industry_map.items():
        rets_1m, rets_3m, rets_6m = [], [], []
        above_50, above_200, leaders = 0, 0, 0
        count = 0

        for t in group:
            df = get_data(t)
            if df is None or len(df) < 200:
                continue

            count += 1
            price = df["Close"].iloc[-1]
            sma50 = df["Close"].rolling(50).mean().iloc[-1]
            sma200 = df["Close"].rolling(200).mean().iloc[-1]

            above_50 += price > sma50
            above_200 += price > sma200

            r1 = price / df["Close"].iloc[-21] - 1
            r3 = price / df["Close"].iloc[-63] - 1
            r6 = price / df["Close"].iloc[-126] - 1

            rets_1m.append(r1)
            rets_3m.append(r3)
            rets_6m.append(r6)

            if r3 > 0.20:
                leaders += 1

        if count == 0:
            continue

        score = (
            np.mean(rets_1m) * 0.25 +
            np.mean(rets_3m) * 0.35 +
            np.mean(rets_6m) * 0.20 +
            ((above_50 / count) * 0.5) +
            ((above_200 / count) * 0.5) +
            ((leaders / count) * 0.5) +
            ((np.mean(rets_3m) - spy_3m) * 1.0)
        )

        industry_scores[ind] = score

    return industry_scores

# ============================================================
# PATTERN DETECTION
# ============================================================

def detect_vcp(df):
    if len(df) < 60:
        return False
    r1 = float((df["High"].iloc[-60:-40].max() - df["Low"].iloc[-60:-40].min()) / df["Low"].iloc[-60:-40].min())
    r2 = float((df["High"].iloc[-40:-20].max() - df["Low"].iloc[-40:-20].min()) / df["Low"].iloc[-40:-20].min())
    r3 = float((df["High"].iloc[-20:].max() - df["Low"].iloc[-20:].min()) / df["Low"].iloc[-20:].min())
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
        if today_vol > float(down["Volume"].max()):
            return True
    return False

def breakout_trigger(df):
    if len(df) < 30:
        return False
    resistance = float(df["High"].iloc[-50:-1].max())
    price = float(df["Close"].iloc[-1])
    return price > resistance

# ============================================================
# STAGE CLASSIFICATION
# ============================================================

def classify_stage(df):
    if len(df) < 220:
        return "Unknown"

    price = float(df["Close"].iloc[-1])
    sma50 = float(df["Close"].rolling(50).mean().iloc[-1])
    sma150 = float(df["Close"].rolling(150).mean().iloc[-1])
    sma200 = float(df["Close"].rolling(200).mean().iloc[-1])
    sma200_20 = float(df["Close"].rolling(200).mean().shift(20).iloc[-1])

    trend = (price > sma50) and (sma50 > sma150) and (sma150 > sma200) and (sma200 > sma200_20)

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

# ============================================================
# MACRO
# ============================================================

def fetch_macro_environment():
    spy = dd.get_transaction_df("SPY")
    hyg = dd.get_transaction_df("HYG")
    ratio = hyg["Close"] / spy["Close"]
    risk_on = (ratio > ratio.rolling(20).mean()).tail(3).all()
    return {"SPY": spy, "HYG": hyg}, bool(risk_on)

# ============================================================
# STOCK ACCUMULATION DETECTION
# ============================================================

def detect_accumulation(ticker, rs_map, risk_on, industry_scores, industry_percentiles):
    df = get_data(ticker)
    if df is None or len(df) < 200:
        return None

    df = calculate_obv(df)
    df["ATR"] = calculate_atr(df)
    df = add_bb_width(df)

    price = float(df["Close"].iloc[-1])
    rs_rank = float(rs_map.get(ticker, 0))
    stage_val = classify_stage(df)
    vcp_signal = detect_vcp(df)
    pocket = check_pocket_pivot(df)
    breakout = breakout_trigger(df)

    # Volume metrics
    recent_df = df.tail(50)
    up_vol = float(recent_df[recent_df["Close"] > recent_df["Close"].shift()]["Volume"].sum())
    down_vol = float(recent_df[recent_df["Close"] < recent_df["Close"].shift()]["Volume"].sum())
    ud_ratio = up_vol / max(down_vol, 1.0)

    obv_slope = linregress(range(20), df["OBV"].tail(20))[0]
    obv_rising = obv_slope > 0

    current_bb = float(df["BB_Width"].iloc[-1])
    avg_bb = float(df["BB_Width"].rolling(50).mean().iloc[-1])
    bb_squeeze = current_bb < (avg_bb * 0.8)

    institutional = pocket or (ud_ratio > 1.2) or obv_rising

    max_high = float(df["High"].tail(252).max())
    near_high = ((max_high - price) / max_high) < 0.25 if max_high > 0 else False

    trend = "Stage 2" in stage_val or "Stage 3" in stage_val

    vol_50 = float(df["Volume"].rolling(50).mean().iloc[-1])
    vol_3 = float(df["Volume"].tail(3).mean())
    volume_dry_up = vol_3 < (vol_50 * 0.5)

    # Industry integration
    industry = get_industry(ticker)
    industry_score = industry_scores.get(industry, 0)
    industry_pct = industry_percentiles.get(industry, 0)

    # ============================================================
    # SCORING MODEL
    # ============================================================

    score = 0

    # RS scoring
    if rs_rank >= 50: score += 1
    if rs_rank >= 70: score += 2
    if rs_rank >= 85: score += 3
    if rs_rank >= 95: score += 4

    # Structure & Volume
    score += int(vcp_signal) * 2
    score += int(bb_squeeze) * 2
    score += int(obv_rising) * 1
    score += int(breakout) * 2
    score += int(pocket) * 2
    score += int(institutional) * 2
    score += int(trend) * 2
    score += int(near_high) * 1
    score += int(volume_dry_up) * 1
    score += int(risk_on) * 1

    # Industry boosts
    if industry_pct >= 60: score += 2
    if industry_pct >= 80: score += 3
    if industry_pct >= 90: score += 4

    # ============================================================
    # RATING
    # ============================================================

    if score >= 18:
        rating = "Elite Accumulation"
    elif score >= 13:
        rating = "Institutional Accumulation"
    elif score >= 9:
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
        "industry": industry,
        "industry_score": round(industry_score, 3),
        "industry_percentile": round(industry_pct, 1),
        "ud_ratio": round(ud_ratio, 2),
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


def main(input_file=None, output_file=None):
    if input_file:
        tickers = pd.read_csv(input_file)["symbol"].dropna().tolist()
    else:
        tickers = ["HRMY", "FVCB"]

    print(f"Loaded {len(tickers)} tickers")

    macro, risk_on = fetch_macro_environment()
    rs_map = build_rs_rank(tickers, macro["SPY"])

    # Build industry momentum
    industry_scores = build_industry_momentum(tickers)
    industry_percentiles = {
        ind: (pd.Series(industry_scores).rank(pct=True)[ind] * 100)
        for ind in industry_scores
    }

    results = []

    for i, t in enumerate(tickers):
        if i % 100 == 0:
            print(f"{i}/{len(tickers)}")
        try:
            r = detect_accumulation(t, rs_map, risk_on, industry_scores, industry_percentiles)
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
    main("resource/us_top_5000.csv","output/2026-06-19/us_1d/us_top_5000/find_building_up_gpt_2026-06-19_2.csv")
