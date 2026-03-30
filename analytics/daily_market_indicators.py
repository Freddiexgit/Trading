import pandas as pd
import numpy as np
import yfinance as yf
import pandas_datareader.data as web
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")

# =========================
# CONFIG
# =========================
LOOKBACK_YEARS = 2

MARKET_TICKERS = {
    "SPY": "SPY",
    "VIX": "^VIX",
    "VIX3M": "^VIX3M",
    "TNX": "^TNX",
    "US02Y": "^IRX",   # proxy for 2Y
    "DXY": "DX-Y.NYB"
}

CAPITAL_TICKERS = {
    "SPY": "SPY",
    "QQQ": "QQQ",
    "IWM": "IWM"
}

FRED_TICKERS = {
    "BAMLH0A0HYM2": "HY_SPREAD",
    "WALCL": "FED_ASSETS",
    "WTREGEN": "TGA",
    "RRPONTSYD": "REV_REPO",
    "UNRATE": "UNEMP",
    "NFCI": "FCI",
    "DFII10": "REAL_10Y"
}

# =========================
# DATA PIPELINE
# =========================
def download(tickers, start, end):
    df = yf.download(tickers, start=start, end=end, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        return df
    return df


def fetch_data():
    end = datetime.today()
    start = end - timedelta(days=LOOKBACK_YEARS * 365)

    # Market
    market = download(list(MARKET_TICKERS.values()), start, end)
    close = market["Close"].rename(columns={v: k for k, v in MARKET_TICKERS.items()})

    spy = market.xs("SPY", level=1, axis=1)

    # Capital
    cap = download(list(CAPITAL_TICKERS.values()), start, end)
    cap_close = cap["Close"]
    cap_vol = cap["Volume"]
    cap_close.columns = CAPITAL_TICKERS.keys()
    cap_vol.columns = CAPITAL_TICKERS.keys()

    total_cap = (cap_close * cap_vol).sum(axis=1)

    # Oil
    oil = yf.download("CL=F", start=start, end=end, progress=False)["Close"]

    # FRED
    fred = web.DataReader(list(FRED_TICKERS.keys()), "fred", start, end)
    fred = fred.rename(columns=FRED_TICKERS)

    # Merge
    df = pd.concat([close, fred], axis=1).sort_index().ffill()

    # Add extras
    df["SPY_HIGH"] = spy["High"]
    df["SPY_LOW"] = spy["Low"]
    df["SPY_VOL"] = spy["Volume"]
    df["TOTAL_CAP"] = total_cap
    df["OIL"] = oil

    return df.dropna()


# =========================
# FEATURES
# =========================
def compute_features(df):
    # RV
    df["RV"] = df["SPY"].pct_change().rolling(20).std() * np.sqrt(252) * 100

    # Trends
    df["UNEMP_3M"] = df["UNEMP"] - df["UNEMP"].shift(63)
    df["TNX_5D"] = df["TNX"] - df["TNX"].shift(5)
    df["VIX_HIGH"] = df["VIX"].rolling(3).max().shift(1)

    # Liquidity
    df["NET_LIQ"] = df["FED_ASSETS"] - df["TGA"] - df["REV_REPO"]
    df["NET_LIQ_4W"] = df["NET_LIQ"] - df["NET_LIQ"].shift(21)

    # Capital
    df["CAP_20"] = df["TOTAL_CAP"].rolling(20).mean()

    # Yield curve
    df["YC"] = df["TNX"] - df["US02Y"]
    df["YC_1M"] = df["YC"] - df["YC"].shift(21)

    # Financial conditions
    df["FCI_1M"] = df["FCI"] - df["FCI"].shift(21)

    # Dollar
    df["DXY_5"] = df["DXY"].rolling(5).mean()
    df["DXY_20"] = df["DXY"].rolling(20).mean()

    # Oil
    df["OIL_1M"] = df["OIL"] - df["OIL"].shift(21)

    # Real rates
    df["REAL_5D"] = df["REAL_10Y"] - df["REAL_10Y"].shift(5)

    return df.dropna()


# =========================
# SIGNAL ENGINE
# =========================
def evaluate(df):
    x = df.iloc[-1]

    results = {}

    # Core
    results["IV > RV"] = (x["VIX"] > x["RV"], f"IV: {x['VIX']:.1f}% | RV: {x['RV']:.1f}%")

    results["Fear Spike, Macro OK"] = (
        (x["VIX"] > 20 and x["UNEMP_3M"] <= 0.1),
        f"VIX: {x['VIX']:.1f} | Unemp 3M Δ: {x['UNEMP_3M']:+.1f}%"
    )

    results["Credit Stable"] = (
        x["HY_SPREAD"] < 5.0,
        f"HY Spread: {x['HY_SPREAD']:.2f}%"
    )

    results["Yields Falling"] = (
        x["TNX_5D"] < 0,
        f"10Y Δ: {x['TNX_5D']:+.2f}"
    )

    results["VIX Stabilizing"] = (
        x["VIX"] < x["VIX_HIGH"],
        f"VIX: {x['VIX']:.2f} vs High: {x['VIX_HIGH']:.2f}"
    )

    # Capitulation
    vol_avg = df["SPY_VOL"].rolling(20).mean().iloc[-1]
    wick = (x["SPY"] - x["SPY_LOW"]) / (x["SPY_HIGH"] - x["SPY_LOW"] + 1e-8)
    cap = x["TOTAL_CAP"]
    cap_avg = x["CAP_20"]

    cap_signal = (x["SPY_VOL"] > 1.2 * vol_avg) and (wick > 0.5) and (cap > 1.2 * cap_avg)

    results["Capitulation"] = (
        cap_signal,
        f"Vol: {x['SPY_VOL']/vol_avg:.1f}x | Wick: {wick*100:.0f}%"
    )

    results["Put/Call Proxy"] = (
        x["VIX"] > x["VIX3M"],
        f"VIX: {x['VIX']:.1f} vs VIX3M: {x['VIX3M']:.1f}"
    )

    results["Liquidity"] = (
        x["NET_LIQ_4W"] >= 0,
        f"Δ: {x['NET_LIQ_4W']/1000:+.0f}B"
    )

    # NEW MACRO
    results["Yield Curve Improving"] = (
        x["YC_1M"] > 0,
        f"Spread Δ: {x['YC_1M']:+.2f}"
    )

    results["Financial Conditions Easing"] = (
        x["FCI_1M"] < 0,
        f"FCI Δ: {x['FCI_1M']:+.2f}"
    )

    results["Dollar Weakening"] = (
        x["DXY_5"] < x["DXY_20"],
        f"DXY short < long"
    )

    results["Oil Not Spiking"] = (
        x["OIL_1M"] < 5,
        f"Oil Δ: {x['OIL_1M']:+.1f}"
    )

    results["Real Rates Falling"] = (
        x["REAL_5D"] < 0,
        f"Real Δ: {x['REAL_5D']:+.2f}"
    )

    return results


# =========================
# OUTPUT
# =========================
def run():
    print("Fetching data...")
    df = fetch_data()
    df = compute_features(df)

    signals = evaluate(df)

    print("\n" + "="*60)
    print("📊 FULL MACRO SYSTEM")
    print("="*60)

    score = 0
    for k, (status, detail) in signals.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {k:<30} | {detail}")
        score += int(status)

    print("-"*60)
    print(f"🎯 SCORE: {score} / {len(signals)}")

    if score >= 10:
        print("🟢 STRONG BUY ENVIRONMENT")
    elif score >= 7:
        print("🟡 ACCUMULATE")
    else:
        print("🔴 RISK-OFF")

    print("="*60)


if __name__ == "__main__":
    run()