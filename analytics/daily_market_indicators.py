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
MARKET_TICKERS = {
    "SPY": "SPY",
    "VIX": "^VIX",
    "VIX3M": "^VIX3M",
    "TNX": "^TNX"
}

FRED_TICKERS = {
    "BAMLH0A0HYM2": "HY_SPREAD",
    "WALCL": "FED_ASSETS",
    "WTREGEN": "TGA",
    "RRPONTSYD": "REV_REPO",
    "UNRATE": "UNEMP"
}

CAPITAL_TICKERS = {
    "SPY": "SPY",
    "QQQ": "QQQ",
    "IWM": "IWM"
}

# =========================
# HELPERS
# =========================
def download_safe(tickers, start, end):
    try:
        df = yf.download(tickers, start=start, end=end, progress=False)
        if df.empty:
            raise ValueError("Empty download")
        return df
    except Exception as e:
        raise RuntimeError(f"Download failed: {e}")


# =========================
# DATA PIPELINE
# =========================
def fetch_data(years=1):
    end = datetime.today()
    start = end - timedelta(days=years * 365)

    # ---- Market ----
    market_raw = download_safe(list(MARKET_TICKERS.values()), start, end)

    close = market_raw["Close"].rename(columns={v: k for k, v in MARKET_TICKERS.items()})

    spy = market_raw.xs("SPY", level=1, axis=1)

    # ---- Capital ----
    cap_raw = download_safe(list(CAPITAL_TICKERS.values()), start, end)

    cap_close = cap_raw["Close"]
    cap_vol = cap_raw["Volume"]

    cap_close.columns = CAPITAL_TICKERS.keys()
    cap_vol.columns = CAPITAL_TICKERS.keys()

    cap_dollar = cap_close * cap_vol

    # ---- FRED ----
    fred = web.DataReader(list(FRED_TICKERS.keys()), "fred", start, end)
    fred = fred.rename(columns=FRED_TICKERS)

    # ---- Merge ----
    df = pd.concat([close, fred], axis=1).sort_index().ffill()

    # Add OHLCV
    df["SPY_HIGH"] = spy["High"]
    df["SPY_LOW"] = spy["Low"]
    df["SPY_OPEN"] = spy["Open"]
    df["SPY_VOL"] = spy["Volume"]

    # Add capital
    df["TOTAL_CAPITAL"] = cap_dollar.sum(axis=1)

    return df.dropna()


# =========================
# FEATURES
# =========================
def compute_features(df):
    # Volatility
    df["RV_20"] = df["SPY"].pct_change().rolling(20).std() * np.sqrt(252) * 100

    # Unemployment trend
    df["UNEMP_3M"] = df["UNEMP"] - df["UNEMP"].shift(63)

    # Yield trend
    df["TNX_5D"] = df["TNX"] - df["TNX"].shift(5)

    # VIX stabilization
    df["VIX_3D_HIGH"] = df["VIX"].rolling(3).max().shift(1)

    # Liquidity
    df["NET_LIQ"] = df["FED_ASSETS"] - df["TGA"] - df["REV_REPO"]
    df["NET_LIQ_4W"] = df["NET_LIQ"] - df["NET_LIQ"].shift(21)

    # Capital trend
    df["CAP_20D"] = df["TOTAL_CAPITAL"].rolling(20).mean()

    return df.dropna()


# =========================
# SIGNAL ENGINE
# =========================
def evaluate(df):
    latest = df.iloc[-1]

    checklist = {}

    # 1. IV > RV
    iv = latest["VIX"]
    rv = latest["RV_20"]
    checklist["IV > RV"] = {
        "status": iv > rv,
        "detail": f"IV: {iv:.1f}% | RV: {rv:.1f}%"
    }

    # 2. Fear spike, macro OK
    macro_ok = (latest["VIX"] > 20) and (latest["UNEMP_3M"] <= 0.1)
    checklist["Fear Spike, Macro OK"] = {
        "status": macro_ok,
        "detail": f"VIX: {latest['VIX']:.1f} | Unemp 3M Δ: {latest['UNEMP_3M']:+.1f}%"
    }

    # 3. Credit stable
    credit = latest["HY_SPREAD"]
    checklist["Credit Stable"] = {
        "status": credit < 5.0,
        "detail": f"HY Spread: {credit:.2f}% (Danger > 5.0%)"
    }

    # 4. Yields falling
    yield_delta = latest["TNX_5D"]
    checklist["Yields Falling"] = {
        "status": yield_delta < 0,
        "detail": f"10Y Yield 5D Δ: {yield_delta:+.2f} bps"
    }

    # 5. VIX stabilizing
    vix_high = latest["VIX_3D_HIGH"]
    checklist["VIX Stabilizing"] = {
        "status": latest["VIX"] < vix_high,
        "detail": f"VIX: {latest['VIX']:.2f} vs 3D High: {vix_high:.2f}"
    }

    # 6. Capitulation candle (enhanced)
    vol_avg = df["SPY_VOL"].rolling(20).mean().iloc[-1]
    wick = (latest["SPY"] - latest["SPY_LOW"]) / (latest["SPY_HIGH"] - latest["SPY_LOW"] + 1e-8)

    cap_avg = latest["CAP_20D"]
    cap = latest["TOTAL_CAPITAL"]

    capitulation = (
        (latest["SPY_VOL"] > vol_avg * 1.2)
        and (wick > 0.5)
        and (cap > cap_avg * 1.2)
    )

    checklist["Capitulation Candle"] = {
        "status": capitulation,
        "detail": f"Vol: {latest['SPY_VOL']/vol_avg:.1f}x Avg | Wick: {wick*100:.0f}% of range"
    }

    # 7. Put/Call proxy
    backwardation = latest["VIX"] > latest["VIX3M"]
    checklist["High Put/Call (Backwardation)"] = {
        "status": backwardation,
        "detail": f"VIX: {latest['VIX']:.1f} vs VIX3M: {latest['VIX3M']:.1f}"
    }

    # 8. Liquidity stable
    liq_delta = latest["NET_LIQ_4W"]
    checklist["Liquidity Stable"] = {
        "status": liq_delta >= 0,
        "detail": f"Net Liq 4W Δ: ${liq_delta/1000:+.0f} Billion"
    }

    return checklist


# =========================
# OUTPUT
# =========================
def print_dashboard(df, checklist):
    latest = df.iloc[-1]

    cap = latest["TOTAL_CAPITAL"] / 1e9
    cap_avg = latest["CAP_20D"] / 1e9
    cap_ratio = cap / cap_avg

    print("\n" + "=" * 50)
    print(" 🚨 INSTITUTIONAL BOTTOM-FISHING SCANNER 🚨")
    print("=" * 50)

    print(f"💰 Total Trading Capital        | ${cap:.0f}B ({cap_ratio:.2f}x avg)\n")

    for name, data in checklist.items():
        icon = "✅" if data["status"] else "❌"
        print(f"{icon} {name:<30} | {data['detail']}")

    print("-" * 50)

    score = sum([1 for x in checklist.values() if x["status"]])
    total = len(checklist)

    print(f"🎯 TOTAL SCORE: {score} / {total}")

    if score >= 7:
        print("🟢 VERDICT: ALL-IN BUY SIGNAL")
    elif score >= 5:
        print("🟡 VERDICT: SCALING IN")
    else:
        print("🔴 VERDICT: NO TRADE")
    print("=" * 50 + "\n")


# =========================
# MAIN
# =========================
def run():
    print("Fetching data...")
    df = fetch_data()
    df = compute_features(df)
    checklist = evaluate(df)
    print_dashboard(df, checklist)


if __name__ == "__main__":
    run()