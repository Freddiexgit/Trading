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
            early = early_warning(df)
        except Exception as e:
            print(f"eam error: {ticker}",  e)
            continue
        total = (
            0.55*core +
            0.25*fake +
            0.20*early
        ) * (1 + sec_score)

        results.append((ticker, total))

    print("================================")
    print("🔥 LEADER ROTATION RANKING")
    print("================================")
    results_sorted = sorted(results, key=lambda x:x[1], reverse=True)
    # for r in results_sorted:
    #     print(r[0], round(r[1],3))
    pd.DataFrame(results_sorted, columns=["symbol", "Score"]).to_csv(output_file, index=False)

# =========================================================

if __name__ == "__main__":
    current_dir = os.getcwd()
    print(f"Current Directory: {current_dir}")
    # watch_list = pd.read_csv(f"../resource/my_vip.csv")['symbol'].tolist()
    watch_list = ["AAPL"]

    run(watch_list)
