# daily_macro_trader.py

import pandas as pd
import numpy as np
import yfinance as yf
import pandas_datareader.data as web
from datetime import datetime, timedelta
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
import warnings
import sys

# Suppress yfinance and hmmlearn warnings for a clean terminal output
warnings.filterwarnings('ignore')

# =========================
# CONFIGURATION
# =========================
MARKET_TICKERS = {"QQQ": "QQQ", "VIX": "^VIX", "TLT": "TLT"}
FRED_TICKERS = {"DFF": "FED_RATE", "CPIAUCSL": "CPI", "UNRATE": "UNEMP"}


# =========================
# 1. DATA PIPELINE
# =========================
def fetch_macro_data(years=4):
    end = datetime.today()
    start = end - timedelta(days=years * 365)

    try:
        raw = yf.download(list(MARKET_TICKERS.values()), start=start, end=end, progress=False)
        market_df = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
        market_df = market_df.rename(columns={v: k for k, v in MARKET_TICKERS.items()})

        fred_df = web.DataReader(list(FRED_TICKERS.keys()), 'fred', start, end)
        fred_df = fred_df.rename(columns=FRED_TICKERS)

        df = pd.concat([market_df, fred_df], axis=1)
        for col in ["FED_RATE", "CPI", "UNEMP"]:
            df[col] = df[col].ffill()

        return df.dropna()
    except Exception as e:
        print(f"❌ Critical Error fetching data: {e}")
        sys.exit(1)


# =========================
# 2. FEATURE ENGINEERING (Multi-Timeframe & Zero-Masked)
# =========================
def compute_features(df):
    # -------- CPI --------
    # 1M Immediate Shock (Zero-Masked)
    cpi_last_move = df["CPI"].diff().replace(0, np.nan).ffill()
    df["CPI_DELTA_1M"] = cpi_last_move / (df["CPI"] - cpi_last_move + 1e-8)

    # 3M Smoothed Trend (63 trading days)
    df["CPI_TREND_3M"] = (df["CPI"] - df["CPI"].shift(63)) / (df["CPI"].shift(63) + 1e-8)

    # 1Y Structural Trend (252 trading days)
    df["CPI_TREND_1Y"] = (df["CPI"] - df["CPI"].shift(252)) / (df["CPI"].shift(252) + 1e-8)

    # -------- FED RATE --------
    # 1M Immediate Shock (Basis Points)
    df["FED_DELTA_1M"] = df["FED_RATE"].diff().replace(0, np.nan).ffill()
    # 3M Smoothed Trend
    df["FED_TREND_3M"] = df["FED_RATE"] - df["FED_RATE"].shift(63)
    # 1Y Structural Trend
    df["FED_TREND_1Y"] = df["FED_RATE"] - df["FED_RATE"].shift(252)

    # -------- UNEMPLOYMENT --------
    # 1M Immediate Shock (Percentage Points)
    df["UNEMP_DELTA_1M"] = df["UNEMP"].diff().replace(0, np.nan).ffill()
    # 3M Smoothed Trend (The Sahm Rule Proxy timeframe)
    df["UNEMP_TREND_3M"] = df["UNEMP"] - df["UNEMP"].shift(63)
    # 1Y Structural Trend
    df["UNEMP_TREND_1Y"] = df["UNEMP"] - df["UNEMP"].shift(252)

    # -------- MARKET & VOLATILITY --------
    df["QQQ_EMA5"] = df["QQQ"].ewm(span=5, adjust=False).mean()
    df["QQQ_EMA10"] = df["QQQ"].ewm(span=10, adjust=False).mean()
    df["MARKET_UP"] = df["QQQ_EMA5"] > df["QQQ_EMA10"]
    df["TREND_STRENGTH"] = (df["QQQ_EMA5"] - df["QQQ_EMA10"]) / df["QQQ_EMA10"]

    df["VIX_Z"] = (df["VIX"] - df["VIX"].rolling(252).mean()) / (df["VIX"].rolling(252).std() + 1e-8)

    return df.dropna()

# =========================
# 3. OPTIONS EDGE & KELLY SIZING
# =========================
def compute_options_edge(df):
    df["RV"] = df["QQQ"].pct_change().rolling(20).std() * np.sqrt(252)
    df["IV"] = df["VIX"] / 100.0
    df["VIX_PERCENTILE"] = df["VIX"].rolling(252).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])
    return df.dropna()


def calculate_kelly_size(prob_win, payout_ratio=2.0, kelly_fraction=0.5, max_risk=0.05):
    prob_loss = 1.0 - prob_win
    kelly_pct = prob_win - (prob_loss / payout_ratio)
    kelly_pct = max(0.0, kelly_pct)
    final_risk_pct = min(kelly_pct * kelly_fraction, max_risk)
    return final_risk_pct


# =========================
# 4. HMM MACHINE LEARNING (Using Smoothed Features)
# =========================
def compute_hmm_probabilities(df, n_states=2):
    # Swap out the 1M Deltas for the 3M Trends
    features = [
        "TREND_STRENGTH",
        "VIX_Z",
        "CPI_TREND_3M",
        "FED_TREND_3M",
        "UNEMP_TREND_3M"
    ]
    X = df[features].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # random_state ensures the model doesn't randomly flip state labels on different runs
    hmm_model = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=100, random_state=42)
    hmm_model.fit(X_scaled)

    probs = hmm_model.predict_proba(X_scaled)

    # Identify the Recession state dynamically (higher VIX)
    state_vix_means = [df.iloc[probs[:, i] >= 0.5]["VIX"].mean() for i in range(n_states)]
    high_vol_state = np.argmax(state_vix_means)
    low_vol_state = np.argmin(state_vix_means)

    df["P_EXPANSION"] = probs[:, low_vol_state]
    df["P_RECESSION"] = probs[:, high_vol_state]

    return df


# =========================
# 5. TRADE GENERATOR
# =========================
def generate_trade_probabilistic(latest):
    p_exp = latest["P_EXPANSION"]
    p_rec = latest["P_RECESSION"]
    iv = latest["IV"]
    rv = latest["RV"]
    vix_pct = latest["VIX_PERCENTILE"]
    price = latest["QQQ"]

    def round_strike(x):
        return int(round(x / 5.0) * 5)

    has_edge = (iv < rv) or (vix_pct < 0.30)
    dominant_prob = max(p_exp, p_rec)
    suggested_risk = calculate_kelly_size(prob_win=dominant_prob)

    print("\n===== 🎲 MODEL PROBABILITIES & EDGE =====")
    print(f"P(Expansion):   {p_exp * 100:.1f}%")
    print(f"P(Recession):   {p_rec * 100:.1f}%")
    print(f"IV: {iv * 100:.1f}%  |  RV: {rv * 100:.1f}%")
    print(f"VIX Percentile: {vix_pct * 100:.1f}th")
    print(f"Options Edge:   {'✅ YES (Cheap)' if has_edge else '❌ NO (Expensive)'}")
    print(f"Optimal Risk:   {suggested_risk * 100:.2f}% of Portfolio")

    print("\n===== 🎯 DAILY ACTION PLAN =====")
    if not has_edge:
        print("ACTION: SKIP OR SELL PREMIUM")
        print("REASON: Options are overpriced (IV > RV). Negative expected value on long options.")
    elif p_rec > 0.70:
        put_strike = round_strike(price * 0.95)
        print(f"ACTION: BUY QQQ {put_strike} PUT")
        print(f"SIZING: Risk exactly {suggested_risk * 100:.2f}% of portfolio capital.")
        print("REASON: High Recession probability + Options are mathematically cheap.")
    elif p_exp > 0.70:
        call_strike = round_strike(price * 1.05)
        print(f"ACTION: BUY QQQ {call_strike} CALL")
        print(f"SIZING: Risk exactly {suggested_risk * 100:.2f}% of portfolio capital.")
        print("REASON: High Expansion probability + Options are mathematically cheap.")
    else:
        print("ACTION: WAIT / NEUTRAL")
        print("REASON: Market in transition. Probabilities too mixed (<70% conviction) to deploy capital.")
    print("================================\n")


# =========================
# EXECUTION
# =========================
if __name__ == "__main__":
    print(f"\nInitializing Daily Macro Scan for: {datetime.today().strftime('%Y-%m-%d')}")
    print("Fetching 4-year data runway and training HMM...")

    df = fetch_macro_data(years=4)
    df = compute_features(df)
    df = compute_options_edge(df)
    df = compute_hmm_probabilities(df)

    latest_data = df.iloc[-1]

    print("\n===== 🏛️ CURRENT MACRO DATA =====")
    print(f"QQQ Price:      ${latest_data['QQQ']:.2f} (Trend: {'UP' if latest_data['MARKET_UP'] else 'DOWN'})")
    print(f"VIX Level:      {latest_data['VIX']:.2f}")
    # Changed 'MoM' to '3M' to match the 3-month smoothed trend variable
    print(f"Fed Rate:       {latest_data['FED_RATE']:.2f}% (3M Δ: {latest_data['FED_TREND_3M'] * 100:+.1f} bps)")
    print(f"CPI 3M Δ:       {latest_data['CPI_TREND_3M'] * 100:+.2f}%")
    print(f"Unemp 3M Δ:     {latest_data['UNEMP_TREND_3M']:+.2f}%")

    generate_trade_probabilistic(latest_data)