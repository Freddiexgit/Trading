# ============================================================
# FULL AUTO OPTIONS SCANNER (MULTI-TICKER + LIVE SIGNALS)
# ============================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime

st.set_page_config(layout="wide")

# ============================================================
# BLACK-SCHOLES GREEKS
# ============================================================

def bs_greeks(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return 0, 0, 0

    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)

    delta = norm.cdf(d1)
    theta = (-S * norm.pdf(d1) * sigma / (2*np.sqrt(T))
             - r*K*np.exp(-r*T)*norm.cdf(d2)) / 365
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))

    return delta, gamma, theta

# ============================================================
# SINGLE TICKER SCAN
# ============================================================

def scan_ticker(ticker, r=0.04):
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1d")

        if hist.empty:
            return None

        S = hist["Close"].iloc[-1]

        expiries = tk.options
        if len(expiries) == 0:
            return None

        # Select expiry > 300 days
        expiry = None
        for exp in expiries:
            days = (pd.to_datetime(exp) - pd.Timestamp.today()).days
            if days > 300:
                expiry = exp
                break

        if expiry is None:
            return None
        chain = tk.option_chain(expiry)

        T = (pd.to_datetime(expiry) - pd.Timestamp.today()).days / 365

        rows = []

        for _, row in chain.calls.iterrows():
            K = row["strike"]
            price = row["lastPrice"]
            iv = row["impliedVolatility"]

            if price <= 0 or iv <= 0:
                continue

            delta, gamma, theta = bs_greeks(S, K, T, r, iv)

            leverage = (abs(delta) * S) / price
            score = leverage * abs(delta) / (abs(theta) + 1e-6)

            rows.append({
                "Ticker": ticker,
                "StockPrice": S,
                "Strike": K,
                "Price": price,
                "Delta": delta,
                "Gamma": gamma,
                "Theta": theta,
                "IV": iv,
                "Leverage": leverage,
                "Score": score,
                "Expiry": expiry
            })

        df = pd.DataFrame(rows)

        if df.empty:
            return None

        return df

    except Exception:
        return None

# ============================================================
# MULTI-TICKER SCANNER
# ============================================================

def run_scanner(tickers, delta_min, delta_max, top_n_per_ticker=2):
    all_results = []

    progress = st.progress(0)

    for i, ticker in enumerate(tickers):
        df = scan_ticker(ticker)

        if df is not None:
            df = df[(df["Delta"] > delta_min) & (df["Delta"] < delta_max)]
            df = df.sort_values("Score", ascending=False).head(top_n_per_ticker)
            all_results.append(df)

        progress.progress((i + 1) / len(tickers))

    if not all_results:
        return pd.DataFrame()

    final_df = pd.concat(all_results)

    return final_df.sort_values("Score", ascending=False)

# ============================================================
# UI
# ============================================================

st.title("🚀 FULL AUTO OPTIONS SCANNER")

col1, col2 = st.columns(2)

# Default universe (you can replace with your CSV later)
default_tickers = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA",
    "AMD","NFLX","INTC","CRM","ADBE"
]

ticker_input = col1.text_area("Tickers (comma separated)", ",".join(default_tickers))

delta_range = col2.slider("Delta Range", 0.0, 1.0, (0.3, 0.7))

top_n = st.slider("Top N per ticker", 1, 5, 2)

run = st.button("🔥 Run Full Scan")

# ============================================================
# RUN SCANNER
# ============================================================

if run:
    tickers = [t.strip().upper() for t in ticker_input.split(",")]

    results = run_scanner(tickers, delta_range[0], delta_range[1], top_n)

    if results.empty:
        st.warning("No opportunities found")
    else:
        st.subheader("🏆 BEST OPTIONS ACROSS ALL STOCKS")
        st.dataframe(results, use_container_width=True)

        # Top picks
        st.subheader("🔥 TOP 10 OVERALL TRADES")
        st.dataframe(results.head(10), use_container_width=True)

        # Grouped view
        st.subheader("📊 Per-Ticker Best Trade")
        best_per_ticker = results.sort_values("Score", ascending=False).groupby("Ticker").head(1)
        st.dataframe(best_per_ticker, use_container_width=True)

# ============================================================
# RUN
# ============================================================

# streamlit run app.py
