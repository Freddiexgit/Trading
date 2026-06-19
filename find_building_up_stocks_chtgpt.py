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
    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
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


def calculate_relative_strength(df):
    """
    Simple RS vs own history trend (proxy version)
    """
    if len(df) < 252:
        return 0

    price = df["Close"].iloc[-1]
    r3 = price / df["Close"].iloc[-63] - 1
    r6 = price / df["Close"].iloc[-126] - 1
    r12 = price / df["Close"].iloc[-252] - 1

    return r3 * 0.5 + r6 * 0.3 + r12 * 0.2


# ============================================================
# PATTERN DETECTION
# ============================================================

def detect_vcp(df):
    if len(df) < 60:
        return False

    r1 = (df["High"].iloc[-60:-40].max() - df["Low"].iloc[-60:-40].min()) / df["Low"].iloc[-60:-40].min()
    r2 = (df["High"].iloc[-40:-20].max() - df["Low"].iloc[-40:-20].min()) / df["Low"].iloc[-40:-20].min()
    r3 = (df["High"].iloc[-20:].max() - df["Low"].iloc[-20:].min()) / df["Low"].iloc[-20:].min()

    return (r1 > r2 > r3) and (r2 < r1 * 0.8) and (r3 < r2 * 0.8)


def check_pocket_pivot(df):
    if len(df) < 20:
        return False

    for i in range(1, 4):
        idx = -i
        today = df.iloc[idx]
        prior = df.iloc[idx - 11: idx - 1]

        down = prior[prior["Close"] < prior["Close"].shift()]
        if len(down) == 0:
            continue

        if today["Volume"] > down["Volume"].max():
            return True

    return False


def breakout_trigger(df):
    if len(df) < 30:
        return False

    resistance = df["High"].iloc[-50:-1].max()
    return df["Close"].iloc[-1] > resistance


def classify_stage(df):
    if len(df) < 200:
        return "Unknown"

    price = df["Close"].iloc[-1]
    sma50 = df["Close"].rolling(50).mean().iloc[-1]
    sma150 = df["Close"].rolling(150).mean().iloc[-1]
    sma200 = df["Close"].rolling(200).mean().iloc[-1]

    trend = price > sma50 > sma150 > sma200

    tightening = (
        df["High"].iloc[-20:].max() - df["Low"].iloc[-20:].min()
    ) < (
        df["High"].iloc[-100:-20].max() - df["Low"].iloc[-100:-20].min()
    ) * 0.6

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
    spy = yf.download("SPY", period="1y", auto_adjust=True, progress=False)
    hyg = yf.download("HYG", period="1y", auto_adjust=True, progress=False)

    ratio = hyg["Close"] / spy["Close"]
    risk_on = (ratio > ratio.rolling(20).mean()).tail(3).all()

    return {"SPY": spy, "HYG": hyg}, risk_on


# ============================================================
# RANKING
# ============================================================

def build_rs_rank(tickers):
    scores = []

    for t in tickers:
        df = get_data(t)
        if df is None or len(df) < 252:
            continue

        scores.append((t, calculate_relative_strength(df)))

    rs_df = pd.DataFrame(scores, columns=["ticker", "rs"])
    rs_df["rank"] = rs_df["rs"].rank(pct=True) * 100

    return dict(zip(rs_df["ticker"], rs_df["rank"]))


# ============================================================
# SCREENER
# ============================================================

def detect_accumulation(ticker, rs_map, risk_on):

    df = get_data(ticker)
    df = get_data(ticker)
    if df is None or len(df) < 200:
        return None

    df = calculate_obv(df)
    df["ATR"] = calculate_atr(df)
    df = add_bb_width(df)

    price = df["Close"].iloc[-1]

    # =========================
    # CORE METRICS
    # =========================

    rs_rank = rs_map.get(ticker, 0)

    stage_val = classify_stage(df)

    vcp_signal = detect_vcp(df)

    pocket = check_pocket_pivot(df)

    breakout = breakout_trigger(df)

    liquidity = (df["Close"] * df["Volume"]).tail(50).mean() > 2_000_000

    ud_ratio = (
            df[df["Close"] > df["Close"].shift()]["Volume"].sum()
            / max(df[df["Close"] < df["Close"].shift()]["Volume"].sum(), 1)
    )

    institutional = pocket or ud_ratio > 1.2

    near_high = (
                        (df["High"].tail(252).max() - price)
                        / df["High"].tail(252).max()
                ) < 0.25  # relaxed from 0.15 → 0.25

    trend = stage_val in ["Stage 2", "Stage 3"]

    # =========================
    # SOFT SCORE MODEL
    # =========================

    score = 0

    # RS scoring
    if rs_rank >= 50: score += 1
    if rs_rank >= 70: score += 2
    if rs_rank >= 85: score += 3
    if rs_rank >= 95: score += 4

    # Structure
    score += int(vcp_signal) * 2
    score += int(breakout) * 2
    score += int(pocket) * 2
    score += int(institutional) * 2
    score += int(trend) * 2
    score += int(near_high) * 1
    score += int(liquidity) * 2
    score += int(risk_on) * 1

    # =========================
    # RATING
    # =========================

    if score >= 12:
        rating = "Elite Accumulation"
    elif score >= 9:
        rating = "Institutional Accumulation"
    elif score >= 6:
        rating = "Strong Setup"
    elif score >= 4:
        rating = "Watchlist"
    else:
        rating = "Ignore"

    return {
        "ticker": ticker,
        "price": round(price, 2),
        "score": score,
        "rating": rating,
        "stage": stage_val,
        "rs_rank": round(rs_rank, 1),
        "vcp": vcp_signal,
        "breakout": breakout,
        "pocket": pocket,
        "institutional": institutional,
        "liquidity": liquidity
    }
# ============================================================
# MAIN
# ============================================================

def main(input_file = None, output_file = None):


    if input_file:
        tickers = pd.read_csv(input_file)["symbol"].dropna().tolist()
    else:
        tickers = ["HRMY","FVCB"]
    print(f"Loaded {len(tickers)} tickers")

    macro, risk_on = fetch_macro_environment()
    risk_on = risk_on.iloc[0] if isinstance(risk_on, pd.Series) else risk_on

    rs_map = build_rs_rank(tickers)


    results = []

    for i, t in enumerate(tickers):
        if i % 100 == 0:
            print(f"{i}/{len(tickers)}")
        try:
            r = detect_accumulation(t, rs_map, risk_on)
        except Exception  as e:
            print(f"Error processing {t}: {e}")
            tb.print_exc()
            continue
        if r:
            results.append(r)
    if len(results) == 0 :
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

# Error processing HRMY: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing CNM: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing FVCB: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing TRN: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing INTG: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing ETSY: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing URBN: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing WEC: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing FPH: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing CSQ: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing METCB: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing CLPT: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing QXO: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
# Error processing ROCK: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().