import pandas as pd
import numpy as np
import yfinance as yf
import pandas_datareader.data as web
from datetime import datetime, timedelta
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

# =========================
# Configuration
# =========================
MARKET_TICKERS = {"QQQ": "QQQ", "VIX": "^VIX", "TLT": "TLT"}
FRED_TICKERS = {"DFF": "FED_RATE", "CPIAUCSL": "CPI", "UNRATE": "UNEMP"}


# =========================
# 1. Data Pipeline
# =========================
def fetch_macro_data(years=4):  # INCREASED TO 4 YEARS for ML training data
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

    return df.dropna()


# =========================
# 2. Feature Engineering
# =========================
def compute_features(df):
    # -------- CPI --------
    df["CPI_DELTA"] = (df["CPI"] - df["CPI"].shift(21)) / (df["CPI"].shift(21) + 1e-8)
    df["CPI_TREND_1Y"] = (df["CPI"] - df["CPI"].shift(252)) / (df["CPI"].shift(252) + 1e-8)

    # -------- FED --------
    df["FED_DELTA"] = df["FED_RATE"] - df["FED_RATE"].shift(21)
    df["FED_TREND_1Y"] = df["FED_RATE"] - df["FED_RATE"].shift(252)

    # -------- UNEMP --------
    df["UNEMP_DELTA"] = df["UNEMP"] - df["UNEMP"].shift(21)
    df["UNEMP_TREND_1Y"] = df["UNEMP"] - df["UNEMP"].shift(252)

    # -------- MARKET (EMA SIGNAL) --------
    df["QQQ_EMA5"] = df["QQQ"].ewm(span=5, adjust=False).mean()
    df["QQQ_EMA10"] = df["QQQ"].ewm(span=10, adjust=False).mean()
    df["MARKET_UP"] = df["QQQ_EMA5"] > df["QQQ_EMA10"]
    df["TREND_STRENGTH"] = (df["QQQ_EMA5"] - df["QQQ_EMA10"]) / df["QQQ_EMA10"]

    # -------- VOL --------
    df["VIX_Z"] = (df["VIX"] - df["VIX"].rolling(252).mean()) / (df["VIX"].rolling(252).std() + 1e-8)

    return df.dropna()


# =========================
# 3. Options Edge Calculator
# =========================
def compute_options_edge(df):
    # Realized Volatility (RV): 20-day historical standard deviation, annualized
    df["RV"] = df["QQQ"].pct_change().rolling(20).std() * np.sqrt(252)

    # Implied Volatility (IV): Proxied by the VIX
    df["IV"] = df["VIX"] / 100.0

    # Options Edge: Negative means options are cheap compared to actual stock movement
    df["VOL_PREMIUM"] = df["IV"] - df["RV"]

    # VIX Percentile (Last 252 days)
    df["VIX_PERCENTILE"] = df["VIX"].rolling(252).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])

    return df.dropna()


# =========================
# 4. HMM Probabilities
# =========================
def compute_hmm_probabilities(df, n_states=2):
    # Features the HMM will use to figure out the current macro state
    features = ["TREND_STRENGTH", "VIX_Z", "CPI_DELTA", "FED_DELTA", "UNEMP_DELTA"]
    X = df[features].copy()

    # Scale data for ML model
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train the Hidden Markov Model
    hmm_model = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=100, random_state=42)
    hmm_model.fit(X_scaled)

    # Predict Probabilities
    probs = hmm_model.predict_proba(X_scaled)

    # Dynamically identify which state is the "Recession" (the one with higher VIX)
    state_vix_means = [df.iloc[probs[:, i] >= 0.5]["VIX"].mean() for i in range(n_states)]
    high_vol_state = np.argmax(state_vix_means)
    low_vol_state = np.argmin(state_vix_means)

    # Assign probabilities
    df["P_EXPANSION"] = probs[:, low_vol_state]
    df["P_RECESSION"] = probs[:, high_vol_state]

    return df


# =========================
# 5. Probabilistic Trade Generator
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

    # Edge Filter: Only buy options if IV is lower than RV, OR if VIX is extremely low (<30th percentile)
    has_edge = (iv < rv) or (vix_pct < 0.30)

    # Output dashboard
    print("\n===== 🎲 PROBABILITIES & EDGE =====")
    print(f"P(Expansion):   {p_exp * 100:.1f}%")
    print(f"P(Recession):   {p_rec * 100:.1f}%")
    print(f"IV: {iv * 100:.1f}% | RV: {rv * 100:.1f}%")
    print(f"VIX Percentile: {vix_pct * 100:.1f}th")
    print(f"Options Edge:   {'✅ YES (Cheap)' if has_edge else '❌ NO (Expensive)'}")
    print("===================================")

    if not has_edge:
        return {"action": "SKIP OR SELL PREMIUM", "reason": "Options are overpriced (IV > RV). Selling environment."}

    if p_rec > 0.70:
        put_strike = round_strike(price * 0.95)
        return {"action": f"BUY PUT {put_strike}", "reason": "High probability of Recession + Options are cheap."}

    elif p_exp > 0.70:
        call_strike = round_strike(price * 1.05)
        return {"action": f"BUY CALL {call_strike}", "reason": "High probability of Expansion + Options are cheap."}

    else:
        return {"action": "WAIT / NEUTRAL", "reason": "Market in transition (<70% probability conviction)."}


# =========================
# EXECUTION
# =========================
if __name__ == "__main__":
    try:
        print("Fetching Macro Data & Training HMM...")
        # 1. Pipeline execution
        df = fetch_macro_data(years=4)
        df = compute_features(df)
        df = compute_options_edge(df)
        df = compute_hmm_probabilities(df)

        latest_data = df.iloc[-1]

        # 2. Print Raw Macro State
        print("\n===== 🏛️ MACRO INDICATORS =====")
        print(f"QQQ Price:   ${latest_data['QQQ']:.2f} (Trend: {'UP' if latest_data['MARKET_UP'] else 'DOWN'})")
        print(f"VIX Level:   {latest_data['VIX']:.2f}")
        print(f"CPI MoM Δ:   {latest_data['CPI_DELTA'] * 100:.2f}%")
        print(f"Fed MoM Δ:   {latest_data['FED_DELTA']:.2f} bps")
        print(f"Unemp MoM Δ: {latest_data['UNEMP_DELTA']:.2f}%")

        # 3. Generate Trade
        trade = generate_trade_probabilistic(latest_data)

        print(f"\n===== 🎯 TRADE EXECUTION =====")
        print(f"Action: {trade['action']}")
        print(f"Reason: {trade['reason']}\n")

    except Exception as e:
        import traceback

        traceback.print_exc()