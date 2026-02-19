# ==========================================================
# Professional Leader Radar
# 机构级龙头扫描器
# ==========================================================

import yfinance as yf
import pandas as pd
import numpy as np

# =========================
# 参数区（只改这里）
# =========================
STOCKS = ["NVDA","AMD","AVGO","MU","SMCI"]
SECTOR_ETF = "SOXX"
MARKET = "SPY"
START_DATE = "2023-01-01"


# =========================
# 工具函数
# =========================
def slope(series):
    x = np.arange(len(series))
    return np.polyfit(x, series, 1)[0]


# =========================
# 市场环境层
# =========================
def market_regime(spy):

    spy["MA50"] = spy["Close"].rolling(50).mean()
    spy["MA200"] = spy["Close"].rolling(200).mean()

    return (
        spy["Close"].iloc[-1] > spy["MA200"].iloc[-1]
        and spy["MA50"].iloc[-1] > spy["MA200"].iloc[-1]
    )


# =========================
# 个股指标计算
# =========================
def prepare_stock(df):

    # ===== 均线 =====
    df["EMA10"] = df["Close"].ewm(span=10, adjust=False).mean()
    df["MA60"] = df["Close"].rolling(60).mean()

    # ===== 斜率 =====
    df["slope10"] = df["EMA10"].rolling(10).apply(slope)
    df["slope60"] = df["MA60"].rolling(20).apply(slope)

    df["angle_strength"] = df["slope10"] - df["slope60"]

    # ===== 波动率 =====
    df["range"] = (df["High"] - df["Low"]) / df["Close"]

    df["vol_contract"] = (
        df["range"] <
        df["range"].rolling(20).mean()
    )

    # ===== 接近新高 =====
    df["near_high"] = (
        df["Close"] >
        0.85 * df["High"].rolling(120).max()
    )

    # ===== 成交量结构 =====
    df["vol_dry"] = (
        df["Volume"].rolling(10).mean() <
        df["Volume"].rolling(50).mean()
    )

    df["vol_break"] = (
        df["Volume"] >
        1.5 * df["Volume"].rolling(20).mean()
    )

    # ===== OBV =====
    df["OBV"] = (
        np.sign(df["Close"].diff()).fillna(0)
        * df["Volume"]
    ).cumsum()

    df["obv_slope"] = df["OBV"].rolling(20).apply(slope)

    # ===== Smart Money =====
    up_vol = df["Volume"].where(df["Close"] > df["Close"].shift())
    down_vol = df["Volume"].where(df["Close"] < df["Close"].shift())

    df["smart_money_ratio"] = (
        up_vol.rolling(20).mean() /
        down_vol.rolling(20).mean()
    )

    return df


# =========================
# 龙头雷达评分
# =========================
def radar_score(df, market_ok, sector_rs):

    structure_ok = (
        (df["angle_strength"] > 0) &
        df["vol_contract"] &
        df["near_high"]
    )

    smart_money_ok = df["smart_money_ratio"] > 1.2
    obv_ok = df["obv_slope"] > 0

    df["RADAR_SCORE"] = (
        25 * market_ok +
        20 * (sector_rs > 0) +
        20 * structure_ok +
        20 * smart_money_ok +
        15 * obv_ok
    )

    return df


# =========================
# 主程序
# =========================
def main():

    print("\nDownloading market data...")

    spy = yf.download(MARKET, start=START_DATE)
    sector = yf.download(SECTOR_ETF, start=START_DATE)

    # ===== 市场环境 =====
    market_ok = market_regime(spy)

    spy["ret60"] = spy["Close"].pct_change(60)
    sector["ret60"] = sector["Close"].pct_change(60)

    sector_rs = (
        sector["ret60"].iloc[-1] -
        spy["ret60"].iloc[-1]
    )

    ranking = []

    print("\nScanning stocks...\n")

    for ticker in STOCKS:

        try:
            df = yf.download(ticker, start=START_DATE)
            df = prepare_stock(df)
            df = radar_score(df, market_ok, sector_rs)

            score = df["RADAR_SCORE"].iloc[-1]
            ranking.append((ticker, round(score, 2)))

            print(f"{ticker} score: {score:.2f}")

        except Exception as e:
            print(f"{ticker} failed:", e)

    # ===== 排名 =====
    ranking.sort(key=lambda x: x[1], reverse=True)

    print("\n==============================")
    print("🔥 Leader Radar Ranking")
    print("==============================")

    for r in ranking:
        print(r)


# =========================
if __name__ == "__main__":
    main()
