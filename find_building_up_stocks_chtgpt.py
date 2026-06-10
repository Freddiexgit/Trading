import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import linregress
import ta
import data_downloader as dd


# =====================================================
# OBV
# =====================================================

def calculate_obv(df):
    obv = [0]

    for i in range(1, len(df)):
        if df["Close"].iloc[i] > df["Close"].iloc[i - 1]:
            obv.append(obv[-1] + df["Volume"].iloc[i])

        elif df["Close"].iloc[i] < df["Close"].iloc[i - 1]:
            obv.append(obv[-1] - df["Volume"].iloc[i])

        else:
            obv.append(obv[-1])

    df["OBV"] = obv

    return df


# =====================================================
# ATR
# =====================================================

def calculate_atr(df, period=14):

    high_low = df["High"] - df["Low"]

    high_close = np.abs(
        df["High"] - df["Close"].shift()
    )

    low_close = np.abs(
        df["Low"] - df["Close"].shift()
    )

    tr = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    return tr.rolling(period).mean()


# =====================================================
# BB Width
# =====================================================

def add_bb_width(df):

    sma = df["Close"].rolling(20).mean()

    std = df["Close"].rolling(20).std()

    upper = sma + 2 * std
    lower = sma - 2 * std

    df["BB_Width"] = (
        upper - lower
    ) / sma

    return df


# =====================================================
# Pocket Pivot
# =====================================================

def pocket_pivot(df):

    if len(df) < 15:
        return False

    today = df.iloc[-1]

    prior = df.iloc[-11:-1]

    down_days = prior[
        prior["Close"]
        < prior["Close"].shift()
    ]

    if len(down_days) == 0:
        return False

    max_down_volume = (
        down_days["Volume"].max()
    )

    return (
        today["Close"]
        > df["Close"].iloc[-2]
        and
        today["Volume"]
        > max_down_volume
    )


# =====================================================
# Main Screener
# =====================================================

def detect_accumulation(
    ticker,
    benchmark="SPY",
    lookback_days=20
):

    print(f"\nAnalyzing {ticker}")

    try:

        df = yf.download(
            ticker,
            period="1y",
            auto_adjust=True,
            progress=False
        )

        if len(df) < 220:
            print("Not enough history")
            return

        # -------------------------
        # Indicators
        # -------------------------

        df["SMA50"] = (
            df["Close"]
            .rolling(50)
            .mean()
        )

        df["SMA150"] = (
            df["Close"]
            .rolling(150)
            .mean()
        )

        df["SMA200"] = (
            df["Close"]
            .rolling(200)
            .mean()
        )

        df["ATR"] = calculate_atr(df)

        df = calculate_obv(df)

        df = add_bb_width(df)

        adx_indicator = ta.trend.ADXIndicator(
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            window=14
        )

        df["ADX"] = adx_indicator.adx()

        recent = df.tail(lookback_days)

        current_price = (
            recent["Close"]
            .iloc[-1]
        )

        # =================================================
        # SIGNALS
        # =================================================

        # 1 Volatility contraction

        atr_pct = (
            recent["ATR"].iloc[-1]
            / current_price
        )

        volatility_contraction = (
            atr_pct < 0.04
        )

        # 2 Consolidation

        range_pct = (
            recent["High"].max()
            - recent["Low"].min()
        ) / recent["Low"].min()

        consolidating = (
            range_pct < 0.12
        )

        # 3 Volume Dry-up

        recent_vol = (
            recent["Volume"]
            .mean()
        )

        prior_vol = (
            df.iloc[-40:-20]["Volume"]
            .mean()
        )

        volume_dryup = (
            recent_vol
            < prior_vol * 0.8
        )

        # 4 OBV trend

        x = np.arange(len(recent))

        slope, _, r, _, _ = linregress(
            x,
            recent["OBV"]
        )

        obv_rising = (
            slope > 0
            and r**2 > 0.3
        )

        # 5 Trend quality

        trend_quality = (
            current_price
            > recent["SMA50"].iloc[-1]
            > recent["SMA150"].iloc[-1]
            > recent["SMA200"].iloc[-1]
        )

        # 6 Near highs

        high_52w = (
            df["High"]
            .max()
        )

        distance_from_high = (
            high_52w
            - current_price
        ) / high_52w

        near_high = (
            distance_from_high < 0.15
        )

        # 7 Relative strength

        spy = yf.download(
            benchmark,
            period="3mo",
            auto_adjust=True,
            progress=False
        )

        stock_return = (
            current_price
            / recent["Close"].iloc[0]
            - 1
        )

        spy_return = (
            spy["Close"].iloc[-1]
            / spy["Close"].iloc[-lookback_days]
            - 1
        )

        rs = (
            stock_return
            - spy_return
        )

        outperforming = (
            rs > 0
        )

        # 8 BB squeeze

        bb_pct = (
            df["BB_Width"]
            .rank(pct=True)
            .iloc[-1]
        )

        bb_squeeze = (
            bb_pct < 0.20
        )

        # 9 ADX setup

        current_adx = (
            df["ADX"]
            .iloc[-1]
        )

        old_adx = (
            df["ADX"]
            .iloc[-5]
        )

        adx_setup = (
            current_adx < 25
            and current_adx > old_adx
        )

        # 10 Pocket Pivot

        pocket_pivot_signal = (
            pocket_pivot(df)
        )

        # 11 Up/Down Volume

        up_vol = recent.loc[
            recent["Close"]
            > recent["Close"].shift(),
            "Volume"
        ].sum()

        down_vol = recent.loc[
            recent["Close"]
            < recent["Close"].shift(),
            "Volume"
        ].sum()

        ud_ratio = (
            up_vol
            / max(down_vol, 1)
        )

        ud_accumulation = (
            ud_ratio > 1.5
        )

        # 12 HYG/SPY

        hyg = yf.download(
            "HYG",
            period="6mo",
            auto_adjust=True,
            progress=False
        )

        spy6 = yf.download(
            "SPY",
            period="6mo",
            auto_adjust=True,
            progress=False
        )

        ratio = (
            hyg["Close"]
            / spy6["Close"]
        )

        ratio_ma20 = (
            ratio
            .rolling(20)
            .mean()
        )

        risk_on = (
            ratio.iloc[-1]
            > ratio_ma20.iloc[-1]
        )

        # =================================================
        # SCORE
        # =================================================

        score = 0

        if bb_squeeze:
            score += 2

        if adx_setup:
            score += 1

        if pocket_pivot_signal:
            score += 3

        if ud_accumulation:
            score += 2

        if obv_rising:
            score += 2

        if volume_dryup:
            score += 1

        if near_high:
            score += 2

        if risk_on:
            score += 2

        if trend_quality:
            score += 2

        if outperforming:
            score += 2

        # =================================================
        # Rating
        # =================================================

        if score >= 13:
            rating = "🔥 Institutional Accumulation"

        elif score >= 9:
            rating = "🟢 Strong Setup"

        elif score >= 6:
            rating = "🟡 Watchlist"

        else:
            rating = "🔴 Ignore"

        # =================================================
        # Report
        # =================================================

        print("=" * 60)

        print(f"Ticker: {ticker}")
        print(f"Price : {current_price:.2f}")

        print(f"\nScore : {score}")
        print(f"Rating: {rating}")

        print("\nSignals")

        print(f"Trend Quality        : {trend_quality}")
        print(f"Near 52W High        : {near_high}")
        print(f"OBV Rising           : {obv_rising}")
        print(f"Volume Dryup         : {volume_dryup}")
        print(f"Pocket Pivot         : {pocket_pivot_signal}")
        print(f"BB Squeeze           : {bb_squeeze}")
        print(f"ADX Setup            : {adx_setup}")
        print(f"UD Ratio             : {ud_ratio:.2f}")
        print(f"Outperforming SPY    : {outperforming}")
        print(f"HYG/SPY Risk-On      : {risk_on}")

        print("\nMetrics")

        print(f"ATR %                : {atr_pct:.2%}")
        print(f"Range %              : {range_pct:.2%}")
        print(f"RS vs SPY            : {rs:.2%}")
        print(f"Distance High        : {distance_from_high:.2%}")
        print(f"BB Width Percentile  : {bb_pct:.2%}")
        print(f"ADX                  : {current_adx:.2f}")

        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")


# =====================================================
# Example
# =====================================================

detect_accumulation("NVDA")
detect_accumulation("PLTR")
detect_accumulation("AAPL")