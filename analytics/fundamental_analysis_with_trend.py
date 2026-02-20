# =========================================================
# INSTITUTIONAL LEADER ROTATION RADAR
# =========================================================

import yfinance as yf
import pandas as pd
import numpy as np

# ---------------- CONFIG ----------------

TICKERS = ["NVDA","AMD","AVGO","MU","SMCI"]

SECTOR_MAP = {
    "NVDA": "SEMI",
    "AMD": "SEMI",
    "AVGO": "SEMI",
    "MU": "SEMI",
    "SMCI": "AI_SERVER"
}

SECTOR_ETF = {
    "SEMI": "SMH",
    "AI_SERVER": "QQQ"
}

MARKET_ETF = "SPY"


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


def load_data(ticker):

    df = yf.download(
        ticker,
        period="1y",
        auto_adjust=True,
        progress=False
    )

    # ⭐ 修复 yfinance MultiIndex bug
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df["MA10"] = df["Close"].ewm(span=10).mean()
    df["MA20"] = df["Close"].ewm(span=20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA60"] = df["Close"].rolling(60).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

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

    etf = SECTOR_ETF[sector]

    rs = sector_relative_strength(etf)

    members = [k for k,v in SECTOR_MAP.items() if v==sector]
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

def fake_breakout_filter(df):

    breakout = df["Close"].iloc[-1] > df["Close"].rolling(60).max().iloc[-2]
    volume = df["Volume"].iloc[-1] > 1.2*df["VOL20"].iloc[-1]

    if breakout and volume:
        return 1.0

    return 0.6


# =========================================================
# EARLY WARNING (-10 DAYS)
# =========================================================

def early_warning(df):

    ma_angle = slope(df["MA10"].tail(10)) - slope(df["MA60"].tail(10))

    vol_contract = df["Volume"].tail(5).mean() < df["VOL20"].iloc[-1]

    tight_range = (
        df["High"].tail(5).max() -
        df["Low"].tail(5).min()
    ) / df["Close"].iloc[-1] < 0.08

    score = (
        0.5*(ma_angle>0) +
        0.3*vol_contract +
        0.2*tight_range
    )

    return score


# =========================================================
# MAIN SCAN
# =========================================================

def run():

    if not market_ok():
        print("❌ Market regime not favorable")
        return

    print("\n🔥 MARKET OK — SCANNING...\n")

    results = []

    sector_cache = {}

    for ticker in TICKERS:

        df = load_data(ticker)

        sector = SECTOR_MAP[ticker]

        if sector not in sector_cache:
            sector_cache[sector] = sector_score(sector)

        sec_score = sector_cache[sector]

        core = leader_structure(df)
        fake = fake_breakout_filter(df)
        early = early_warning(df)

        total = (
            0.55*core +
            0.25*fake +
            0.20*early
        ) * (1 + sec_score)

        results.append((ticker, total))

    print("================================")
    print("🔥 LEADER ROTATION RANKING")
    print("================================")

    for r in sorted(results, key=lambda x:x[1], reverse=True):
        print(r[0], round(r[1],3))


# =========================================================

if __name__ == "__main__":
    run()
