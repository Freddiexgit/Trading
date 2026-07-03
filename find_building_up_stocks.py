import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import linregress
import ta
import warnings
import data_downloader as dd

warnings.simplefilter(action='ignore', category=FutureWarning)


# =====================================================
# Core Indicators
# =====================================================

def calculate_obv(df):
    direction = np.sign(df['Close'].diff()).fillna(0)
    df['OBV'] = (direction * df['Volume']).cumsum()
    return df


def calculate_atr(df, period=14):
    high_low = df["High"] - df["Low"]
    high_close = np.abs(df["High"] - df["Close"].shift())
    low_close = np.abs(df["Low"] - df["Close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def add_bb_width(df, window=20, dev=2):
    sma = df["Close"].rolling(window).mean()
    std = df["Close"].rolling(window).std()
    upper = sma + dev * std
    lower = sma - dev * std
    df["BB_Width"] = (upper - lower) / sma
    return df


def check_recent_pocket_pivot(df, lookback=3):
    if len(df) < 15 + lookback:
        return False

    for i in range(1, lookback + 1):
        idx = -i
        today = df.iloc[idx]
        prior = df.iloc[idx - 11: idx - 1]

        down_days = prior[prior["Close"] < prior["Close"].shift()]
        if len(down_days) == 0:
            continue

        max_down_volume = down_days["Volume"].max()

        if today["Close"] > df["Close"].iloc[idx - 1] and today["Volume"] > max_down_volume:
            return True

    return False


# =====================================================
# Macro Data Fetcher
# =====================================================

def fetch_macro_environment(benchmark="SPY", risk_asset="HYG"):
    print(f"Fetching macro environment data ({benchmark}, {risk_asset})...")
    macro_data = yf.download(
        [benchmark, risk_asset],
        period="1y",
        auto_adjust=True,
        progress=False
    )

    ratio = macro_data['Close'][risk_asset] / macro_data['Close'][benchmark]
    ratio_ma20 = ratio.rolling(20).mean()
    risk_on_condition = (ratio > ratio_ma20).tail(3).all()

    return macro_data, risk_on_condition


# =====================================================
# Main Screener Logic (Returns Dictionary)
# =====================================================

def detect_accumulation(
        ticker,
        macro_df,
        risk_on_env,
        benchmark="SPY",
        lookback_days=20,
        atr_thresh=0.04,
        range_thresh=0.12
):
    try:
        df = dd.get_transaction_df(ticker)
        df = df.dropna()

        if len(df) < 220:
            return {"Ticker": ticker, "Status": "Not enough history"}

        df["SMA50"] = df["Close"].rolling(50).mean()
        df["SMA150"] = df["Close"].rolling(150).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()

        df["ATR"] = calculate_atr(df)
        df = calculate_obv(df)
        df = add_bb_width(df)

        adx_indicator = ta.trend.ADXIndicator(
            high=df["High"], low=df["Low"], close=df["Close"], window=14
        )
        df["ADX"] = adx_indicator.adx()

        recent = df.tail(lookback_days)
        current_price = recent["Close"].iloc[-1]

        # SIGNALS
        atr_pct = recent["ATR"].iloc[-1] / current_price
        volatility_contraction = atr_pct < atr_thresh

        range_pct = (recent["High"].max() - recent["Low"].min()) / recent["Low"].min()
        consolidating = range_pct < range_thresh

        recent_vol = recent["Volume"].mean()
        prior_vol = df.iloc[-40:-20]["Volume"].mean()
        volume_dryup = recent_vol < (prior_vol * 0.8)

        x = np.arange(len(recent))
        slope, _, r, _, _ = linregress(x, recent["OBV"])
        obv_rising = (slope > 0) and (r ** 2 > 0.3)

        trend_quality = (
                    current_price > recent["SMA50"].iloc[-1] > recent["SMA150"].iloc[-1] > recent["SMA200"].iloc[-1])

        high_52w = df["High"].max()
        distance_from_high = (high_52w - current_price) / high_52w
        near_high = distance_from_high < 0.15

        spy_close = macro_df['Close'][benchmark]
        stock_return_6m = (current_price / df["Close"].iloc[-126]) - 1
        spy_return_6m = (spy_close.iloc[-1] / spy_close.iloc[-126]) - 1
        rs = stock_return_6m - spy_return_6m
        outperforming = rs > 0

        bb_pct = df["BB_Width"].rank(pct=True).iloc[-1]
        bb_squeeze = bb_pct < 0.20

        current_adx = df["ADX"].iloc[-1]
        old_adx = df["ADX"].iloc[-5]
        adx_setup = (current_adx < 25) and (current_adx > old_adx)

        pocket_pivot_signal = check_recent_pocket_pivot(df, lookback=3)

        up_vol = recent.loc[recent["Close"] > recent["Close"].shift(), "Volume"].sum()
        down_vol = recent.loc[recent["Close"] < recent["Close"].shift(), "Volume"].sum()
        ud_ratio = up_vol / max(down_vol, 1)
        ud_accumulation = ud_ratio > 1.5

        # SCORING
        score = sum([
            bb_squeeze * 2, adx_setup * 1, pocket_pivot_signal * 3, ud_accumulation * 2,
            obv_rising * 2, volume_dryup * 1, near_high * 2, risk_on_env * 2,
            trend_quality * 2, outperforming * 2
        ])

        if score >= 13:
            rating = "Institutional Accumulation"
        elif score >= 9:
            rating = "Strong Setup"
        elif score >= 6:
            rating = "Watchlist"
        else:
            rating = "Ignore"

        # Return as Dictionary
        return {
            "symbol": ticker,
            "Price": round(current_price, 2),
            "Score": score,
            "Rating": rating,
            "Trend Quality": trend_quality,
            "Near 52W High": near_high,
            "OBV Rising": obv_rising,
            "Volume Dryup": volume_dryup,
            "Pocket Pivot": pocket_pivot_signal,
            "BB Squeeze": bb_squeeze,
            "ADX Setup": adx_setup,
            "U/D Ratio": round(ud_ratio, 2),
            "Outperforming SPY": outperforming,
            "Risk-On (HYG/SPY)": risk_on_env,
            "ATR %": round(atr_pct, 4),
            "Range %": round(range_pct, 4),
            "RS vs SPY": round(rs, 4),
            "Dist from High": round(distance_from_high, 4),
            "BB Width %tile": round(bb_pct, 4),
            "ADX": round(current_adx, 2),
            "Status":"success"
        }

    except Exception as e:
        return {"Ticker": ticker, "Status": f"Error: {str(e)}"}

# 1. Basic Information & Scoring
# * Ticker: The stock symbol being analyzed (e.g., AAPL, NVDA).
# * Price: The most recent closing price of the stock.
# * Score: The total number of points the stock earned based on the algorithm's criteria. A higher score means a higher probability of institutional accumulation.
# * Rating: A human-readable label based on the Score (e.g., "🔥 Institutional Accumulation" or "🔴 Ignore").
# 2. Binary Signals (True / False)
# These columns represent specific conditions the algorithm looks for. If True, the stock usually earns points toward its total score.
# * Trend Quality: True if the stock is in a mathematically perfect uptrend (Current Price > 50-day moving average > 150-day > 200-day).
# * Near 52W High: True if the stock is trading within 15% of its 52-week high. Stocks near new highs are fundamentally stronger than stocks hitting new lows.
# * OBV Rising: True if On-Balance Volume is trending upward. This implies that volume is heavier on "up" days than "down" days—a classic footprint of institutional buying.
# * Volume Dryup: True if recent trading volume is at least 20% lower than previous weeks. This shows that selling pressure has dried up and the stock is quietly resting.
# * Pocket Pivot: True if the stock recently had an "up" day with volume higher than any "down" day in the prior 10 days. It is a stealthy buy signal developed by former William O'Neil portfolio managers.
# * BB Squeeze: True if the Bollinger Bands have pinched together tightly. This indicates extreme low volatility, which often precedes an explosive breakout.
# * ADX Setup: True if the ADX (Average Directional Index) is low but starting to curl up. This signals that a dormant, sideways stock is about to start trending again.
# * Outperforming SPY: True if the stock's 6-month percentage return is higher than the S&P 500 over the exact same period.
# * Risk-On (HYG/SPY): True if High-Yield Corporate Bonds (HYG) are outperforming the S&P 500. This is a macro-market indicator showing that Wall Street has an appetite for risk, providing a tailwind for breakouts.
# 3. Raw Metrics & Ratios
# These columns show the actual mathematical values powering the signals above.
# * U/D Ratio (Up/Down Volume): The total volume traded on "up" days divided by the volume on "down" days over the last 20 days. A ratio above 1.0 is good; above 1.5 shows heavy accumulation.
# * ATR % (Average True Range): The stock's average daily price swing expressed as a percentage of its current price. Lower numbers (under 4-5%) mean the stock is coiling tightly and peacefully.
# * Range %: The percentage difference between the highest high and lowest low over the last 20 days. A shallow base (under 12%) is much easier to break out of than a deep, volatile one.
# * RS vs SPY (Relative Strength): The actual percentage by which the stock is beating (or lagging) the S&P 500 over the last 6 months.
# * Dist from High: How far the current price is below its 52-week high, expressed as a percentage.
# * BB Width %tile (Bollinger Band Percentile): Where the current width of the Bollinger Bands ranks historically. A value of 10% means the bands are tighter right now than they have been 90% of the time over the past year.
# * ADX (Average Directional Index): The raw ADX value. Readings below 25 indicate a trendless, consolidating market. Readings above 25 indicate a strong, established trend.
# =====================================================
# Execution & DataFrame Creation
# =====================================================

def main(input_file,output_file):
    macro_data, risk_on = fetch_macro_environment()

    # tickers_to_scan = ["NVDA", "PLTR", "AAPL", "CRWD", "TSLA"]
    results_list = []
    tickers_to_scan = pd.read_csv(input_file)["symbol"].dropna().tolist()
    print("\nScanning tickers...")
    for t in tickers_to_scan:
        try:
            result_dict = detect_accumulation(t, macro_df=macro_data, risk_on_env=risk_on)
        except Exception  as e:
            print("Error processing ticker {t}: {e}")
            continue
        results_list.append(result_dict)

        # Create the DataFrame
    results_df = pd.DataFrame(results_list)
    results_df = results_df[results_df["Score"] >= 6]
    results_df.sort_values("Score", ascending=False, inplace=True)
    results_df.to_csv(output_file, index=False)

# 1. Basic Information & Scoring
# * Ticker: The stock symbol being analyzed (e.g., AAPL, NVDA).
# * Price: The most recent closing price of the stock.
# * Score: The total number of points the stock earned based on the algorithm's criteria. A higher score means a higher probability of institutional accumulation.
# * Rating: A human-readable label based on the Score (e.g., "🔥 Institutional Accumulation" or "🔴 Ignore").
# 2. Binary Signals (True / False)
# These columns represent specific conditions the algorithm looks for. If True, the stock usually earns points toward its total score.
# * Trend Quality: True if the stock is in a mathematically perfect uptrend (Current Price > 50-day moving average > 150-day > 200-day).
# * Near 52W High: True if the stock is trading within 15% of its 52-week high. Stocks near new highs are fundamentally stronger than stocks hitting new lows.
# * OBV Rising: True if On-Balance Volume is trending upward. This implies that volume is heavier on "up" days than "down" days—a classic footprint of institutional buying.
# * Volume Dryup: True if recent trading volume is at least 20% lower than previous weeks. This shows that selling pressure has dried up and the stock is quietly resting.
# * Pocket Pivot: True if the stock recently had an "up" day with volume higher than any "down" day in the prior 10 days. It is a stealthy buy signal developed by former William O'Neil portfolio managers.
# * BB Squeeze: True if the Bollinger Bands have pinched together tightly. This indicates extreme low volatility, which often precedes an explosive breakout.
# * ADX Setup: True if the ADX (Average Directional Index) is low but starting to curl up. This signals that a dormant, sideways stock is about to start trending again.
# * Outperforming SPY: True if the stock's 6-month percentage return is higher than the S&P 500 over the exact same period.
# * Risk-On (HYG/SPY): True if High-Yield Corporate Bonds (HYG) are outperforming the S&P 500. This is a macro-market indicator showing that Wall Street has an appetite for risk, providing a tailwind for breakouts.
# 3. Raw Metrics & Ratios
# These columns show the actual mathematical values powering the signals above.
# * U/D Ratio (Up/Down Volume): The total volume traded on "up" days divided by the volume on "down" days over the last 20 days. A ratio above 1.0 is good; above 1.5 shows heavy accumulation.
# * ATR % (Average True Range): The stock's average daily price swing expressed as a percentage of its current price. Lower numbers (under 4-5%) mean the stock is coiling tightly and peacefully.
# * Range %: The percentage difference between the highest high and lowest low over the last 20 days. A shallow base (under 12%) is much easier to break out of than a deep, volatile one.
# * RS vs SPY (Relative Strength): The actual percentage by which the stock is beating (or lagging) the S&P 500 over the last 6 months.
# * Dist from High: How far the current price is below its 52-week high, expressed as a percentage.
# * BB Width %tile (Bollinger Band Percentile): Where the current width of the Bollinger Bands ranks historically. A value of 10% means the bands are tighter right now than they have been 90% of the time over the past year.
# * ADX (Average Directional Index): The raw ADX value. Readings below 25 indicate a trendless, consolidating market. Readings above 25 indicate a strong, established trend.