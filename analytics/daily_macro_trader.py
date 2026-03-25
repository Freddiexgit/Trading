import pandas as pd
import numpy as np
import yfinance as yf
import pandas_datareader.data as web
from datetime import datetime, timedelta

# =========================
# Configuration
# =========================
MARKET_TICKERS = {
    "QQQ": "QQQ",
    "VIX": "^VIX",
    "TLT": "TLT",
}

FRED_TICKERS = {
    "DFF": "FED_RATE",
    "CPIAUCSL": "CPI",
    "UNRATE": "UNEMP"
}

# =========================
# Utilities
# =========================
def zscore(series, window=252):
    return (series - series.rolling(window).mean()) / (series.rolling(window).std() + 1e-8)

def last_two_valid(series):
    s = series.dropna()
    if len(s) < 2:
        return np.nan, np.nan
    return s.iloc[-1], s.iloc[-2]

# =========================
# Data Pipeline
# =========================
# =========================
# Data Pipeline (Fixed Lookback)
# =========================
def fetch_macro_data(years=2):  # INCREASED TO 2 YEARS to prime the 252-day rolling windows
    end = datetime.today()
    start = end - timedelta(days=years * 365)

    raw = yf.download(list(MARKET_TICKERS.values()), start=start, end=end, progress=False)

    if isinstance(raw.columns, pd.MultiIndex):
        market_df = raw["Close"]
    else:
        market_df = raw

    market_df = market_df.rename(columns={v: k for k, v in MARKET_TICKERS.items()})

    fred_df = web.DataReader(list(FRED_TICKERS.keys()), 'fred', start, end)
    fred_df = fred_df.rename(columns=FRED_TICKERS)

    df = pd.concat([market_df, fred_df], axis=1)

    for col in ["FED_RATE", "CPI", "UNEMP"]:
        df[col] = df[col].ffill()

    df = df.dropna()
    return df


# =========================
# Feature Engineering (Fixed Timeframes)
# =========================
def compute_features(df):
    # 1 month = ~21 trading days, 1 year = ~252 trading days

    # -------- CPI --------
    # MoM Change
    df["CPI_DELTA"] = (df["CPI"] - df["CPI"].shift(21)) / (df["CPI"].shift(21) + 1e-8)
    # YoY Change
    df["CPI_TREND_1Y"] = (df["CPI"] - df["CPI"].shift(252)) / (df["CPI"].shift(252) + 1e-8)

    df["CPI_SCORE"] = np.tanh(df["CPI_DELTA"] * 5 + df["CPI_TREND_1Y"] * 3)

    # -------- FED --------
    # Monthly basis point change
    df["FED_DELTA"] = df["FED_RATE"] - df["FED_RATE"].shift(21)
    # Yearly basis point change
    df["FED_TREND_1Y"] = df["FED_RATE"] - df["FED_RATE"].shift(252)

    df["LIQUIDITY_SCORE"] = (
            -df["FED_DELTA"] * 0.7 +
            -df["FED_TREND_1Y"] * 0.3
    )

    # -------- UNEMP --------
    # MoM change
    df["UNEMP_DELTA"] = df["UNEMP"] - df["UNEMP"].shift(21)
    # YoY change
    df["UNEMP_TREND_1Y"] = df["UNEMP"] - df["UNEMP"].shift(252)

    df["LABOR_SCORE"] = (
            -df["UNEMP_DELTA"] * 0.5 +
            -df["UNEMP_TREND_1Y"] * 0.5
    )

    # =========================
    # MARKET (EMA SIGNAL)
    # =========================
    df["QQQ_EMA5"] = df["QQQ"].ewm(span=5, adjust=False).mean()
    df["QQQ_EMA10"] = df["QQQ"].ewm(span=10, adjust=False).mean()

    df["MARKET_UP"] = df["QQQ_EMA5"] > df["QQQ_EMA10"]
    df["TREND_STRENGTH"] = (df["QQQ_EMA5"] - df["QQQ_EMA10"]) / df["QQQ_EMA10"]

    # =========================
    # VOL
    # =========================
    df["VIX_Z"] = (
            (df["VIX"] - df["VIX"].rolling(252).mean()) /
            (df["VIX"].rolling(252).std() + 1e-8)
    )

    # Drop the NaNs created by the 252-day shift before returning
    return df.dropna()

# =========================
# REGIME ENGINE (UPGRADED)
# =========================
def compute_regime(df):
    df = compute_features(df)
    latest = df.iloc[-1]

    # =========================
    # FACTORS (CLEAN NOW)
    # =========================
    growth_score = (
        latest["TREND_STRENGTH"] * 5 +
        latest["LABOR_SCORE"] * 2
    )

    inflation_score = latest["CPI_SCORE"] * 5
    liquidity_score = latest["LIQUIDITY_SCORE"] * 3
    risk_score = latest["VIX_Z"]

    scores = {
        "growth": float(growth_score),
        "inflation": float(inflation_score),
        "liquidity": float(liquidity_score),
        "risk": float(risk_score),
    }

    # =========================
    # REGIME LOGIC (MORE STABLE)
    # =========================
    if growth_score < -0.5 and risk_score > 0.5:
        regime = "HARD_LANDING"

    elif inflation_score > 0.5 and growth_score < 0:
        regime = "STAGFLATION"

    elif liquidity_score > 0.3 and growth_score > 0:
        regime = "LIQUIDITY_INJECTION"

    elif growth_score > 0.5 and inflation_score < 0.3:
        regime = "EXPANSION"

    elif growth_score > 0 and inflation_score > 0:
        regime = "REFLATION"

    else:
        regime = "TRANSITION"

    return regime, latest, scores

# =========================
# STRATEGY ENGINE
# =========================
def generate_trade(regime, price, vix, scores):

    def round_strike(x):
        return int(round(x / 5.0) * 5)

    vol_scale = np.clip(vix / 100, 0.1, 0.6)

    call_strike = round_strike(price * (1 + vol_scale))
    put_strike = round_strike(price * (1 - vol_scale))

    if regime in ["LIQUIDITY_INJECTION", "EXPANSION"]:
        return {
            "action": f"BUY CALL {call_strike}",
            "reason": "Growth strong + liquidity supportive"
        }

    elif regime == "HARD_LANDING":
        return {
            "action": f"BUY PUT {put_strike}",
            "reason": "Recession risk + volatility expansion"
        }

    elif regime == "STAGFLATION":
        return {
            "action": "PUT SPREAD",
            "reason": "Weak growth + sticky inflation"
        }

    elif regime == "REFLATION":
        return {
            "action": f"BULL CALL SPREAD {round_strike(price)}-{call_strike}",
            "reason": "Growth positive but inflation rising"
        }

    else:
        if scores["risk"] > 1:
            return {
                "action": "LONG STRADDLE",
                "reason": "High uncertainty / volatility expansion"
            }
        else:
            return {
                "action": "IRON CONDOR",
                "reason": "Low conviction / range-bound"
            }

# =========================
# EXECUTION
# =========================
if __name__ == "__main__":
    try:
        df = fetch_macro_data()
        regime, data, scores = compute_regime(df)

        trade = generate_trade(regime, data["QQQ"], data["VIX"], scores)

        print("\n===== MACRO STATE =====")
        print(f"CPI Δ: {data['CPI_DELTA']:.4f}")
        print(f"Fed Δ: {data['FED_DELTA']:.2f}")
        print(f"Unemp Δ: {data['UNEMP_DELTA']:.2f}")
        print(f"QQQ Trend: {'UP' if data['MARKET_UP'] else 'DOWN'}")
        print(f"VIX: {data['VIX']:.2f}")

        print("\n===== SCORES =====")
        for k, v in scores.items():
            print(f"{k}: {v:.2f}")

        print(f"\n===== REGIME =====\n{regime}")

        print(f"\n===== TRADE =====")
        print(f"Action: {trade['action']}")
        print(f"Reason: {trade['reason']}")

    except Exception as e:
        print(f"Error: {e}")