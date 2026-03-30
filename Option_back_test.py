import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime

st.set_page_config(layout="wide", page_title="LEAPS Scanner", page_icon="📈")


# ============================================================
# VECTORIZED BLACK-SCHOLES GREEKS (Includes Dividends)
# ============================================================
def bs_greeks_vectorized(S, K, T, r, sigma, q=0.0):
    """Calculates Greeks for an entire Pandas Series instantly using Numpy."""
    # Ignore divide by zero warnings for deep OTM/ITM edge cases
    with np.errstate(divide='ignore', invalid='ignore'):
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # Vectorized normal distribution operations
        delta = np.exp(-q * T) * norm.cdf(d1)
        gamma = (np.exp(-q * T) * norm.pdf(d1)) / (S * sigma * np.sqrt(T))

        # Theta per day
        theta = (-(S * sigma * np.exp(-q * T) * norm.pdf(d1)) / (2 * np.sqrt(T))
                 - r * K * np.exp(-r * T) * norm.cdf(d2)
                 + q * S * np.exp(-q * T) * norm.cdf(d1)) / 365.0

    # Fill NaNs with 0 for broken edge cases
    return np.nan_to_num(delta), np.nan_to_num(gamma), np.nan_to_num(theta)


# ============================================================
# SINGLE TICKER SCAN (Vectorized)
# ============================================================
def scan_ticker(ticker, min_oi, r=0.042):
    try:
        tk = yf.Ticker(ticker)

        # Get fast info for current price (faster than downloading history)
        S = tk.fast_info['lastPrice']

        # Estimate dividend yield roughly (using trailing annual div)
        div = tk.info.get('trailingAnnualDividendYield', 0.0)
        q = div if div is not None else 0.0

        expiries = tk.options
        if not expiries: return None

        # Find closest expiry > 300 days
        expiry = next((exp for exp in expiries if (pd.to_datetime(exp) - pd.Timestamp.today()).days > 300), None)
        if not expiry: return None

        # Fetch Chain
        chain = tk.option_chain(expiry).calls

        # LIQUIDITY FILTER: Remove stale/dead options
        df = chain[(chain['openInterest'] >= min_oi) & (chain['impliedVolatility'] > 0)].copy()
        if df.empty: return None

        T = (pd.to_datetime(expiry) - pd.Timestamp.today()).days / 365.0

        # Create Mid-Price to avoid "lastPrice" staleness (if bid/ask exist)
        df['Price'] = np.where((df['bid'] > 0) & (df['ask'] > 0),
                               (df['bid'] + df['ask']) / 2,
                               df['lastPrice'])

        # Calculate Greeks Vectorized
        df['Delta'], df['Gamma'], df['Theta'] = bs_greeks_vectorized(
            S, df['strike'], T, r, df['impliedVolatility'], q
        )

        # Calculate Metrics
        df['Leverage'] = (np.abs(df['Delta']) * S) / df['Price']

        # Safe Score Calculation (Avoid dividing by near-zero Theta)
        safe_theta = np.clip(np.abs(df['Theta']), 1e-4, None)
        df['Score'] = (df['Leverage'] * np.abs(df['Delta'])) / safe_theta

        # Formatting Output
        df['Ticker'] = ticker
        df['StockPrice'] = S
        df['Expiry'] = expiry

        # Select and rename columns
        res = df[['Ticker', 'StockPrice', 'strike', 'Price', 'Delta', 'Gamma', 'Theta',
                  'impliedVolatility', 'openInterest', 'Leverage', 'Score', 'Expiry']]
        res = res.rename(columns={'strike': 'Strike', 'impliedVolatility': 'IV', 'openInterest': 'OI'})

        return res

    except Exception as e:
        # In production, log `e` here
        return None


# ============================================================
# MULTI-TICKER SCANNER
# ============================================================
def run_scanner(tickers, delta_min, delta_max, min_oi, top_n=2):
    all_results = []
    progress_bar = st.progress(0)

    for i, ticker in enumerate(tickers):
        df = scan_ticker(ticker, min_oi)

        if df is not None:
            # Filter by Delta
            filtered = df[(df["Delta"] >= delta_min) & (df["Delta"] <= delta_max)]
            # Get Top N
            top_picks = filtered.sort_values("Score", ascending=False).head(top_n)
            all_results.append(top_picks)

        progress_bar.progress((i + 1) / len(tickers))

    progress_bar.empty()  # Clear progress bar when done

    if not all_results: return pd.DataFrame()


    if not all_results: return pd.DataFrame()

    # .reset_index(drop=True) ensures the index is a unique 0, 1, 2, 3...
    final_df = pd.concat(all_results).sort_values("Score", ascending=False)
    return final_df.reset_index(drop=True)


# ============================================================
# UI
# ============================================================
st.title("🚀 LEAPS Quantitative Scanner")
st.markdown("Finds highly capital-efficient, long-duration option trades.")

with st.sidebar:
    st.header("Scan Parameters")
    default_tickers = "AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, AMD, QQQ, SPY"
    ticker_input = st.text_area("Tickers (comma separated)", default_tickers)

    delta_range = st.slider("Target Delta Range", 0.0, 1.0, (0.50, 0.85))
    min_oi = st.number_input("Minimum Open Interest (Liquidity)", min_value=0, value=50)
    top_n = st.slider("Top Picks per Ticker", 1, 5, 2)

    run = st.button("🔥 Run Full Scan", use_container_width=True)

# ============================================================
# EXECUTION & FORMATTING
# ============================================================
if run:
    tickers = [t.strip().upper() for t in ticker_input.split(",")]
    with st.spinner('Scanning options chains...'):
        results = run_scanner(tickers, delta_range[0], delta_range[1], min_oi, top_n)

    if results.empty:
        st.warning("No opportunities found matching those criteria.")
    else:
        # Custom formatting for Streamlit dataframe
        styled_df = results.style.format({
            "StockPrice": "${:.2f}",
            "Strike": "${:.2f}",
            "Price": "${:.2f}",
            "Delta": "{:.3f}",
            "Gamma": "{:.4f}",
            "Theta": "${:.3f}",
            "IV": "{:.1%}",
            "Leverage": "{:.1f}x",
            "Score": "{:.2f}"
        }).background_gradient(subset=['Score'], cmap='viridis')

        st.subheader("🔥 TOP 10 OVERALL TRADES (By Efficiency Score)")
        st.dataframe(styled_df, use_container_width=True, height=400)

        st.subheader("📊 Top Pick Per Ticker")
        best_per_ticker = results.groupby("Ticker").head(1).sort_values("Score", ascending=False)
        st.dataframe(best_per_ticker.style.format({
            "StockPrice": "${:.2f}", "Strike": "${:.2f}", "Price": "${:.2f}",
            "Delta": "{:.3f}", "IV": "{:.1%}", "Leverage": "{:.1f}x", "Score": "{:.2f}"
        }), use_container_width=True)