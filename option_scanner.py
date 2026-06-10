import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq  # For finding Implied Volatility
from math import log, sqrt, exp
from datetime import datetime, timedelta
pd.set_option("display.max_columns", None)

# ==========================================
# 1. Black-Scholes with Dividend Yield (q)
# ==========================================
def bs_price_with_q(S, K, T, r, sigma, q=0.007, type='call'):
    if T <= 0: return max(S - K, 0) if type == 'call' else max(K - S, 0)
    d1 = (log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    if type == 'call':
        return S * exp(-q * T) * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
    else:
        return K * exp(-r * T) * norm.cdf(-d2) - S * exp(-q * T) * norm.cdf(-d1)


# ==========================================
# 2. Find the "Market IV" (Calibration)
# ==========================================
def find_iv(market_price, S, K, T, r, q):
    """Finds the sigma that matches the market price."""
    objective = lambda sigma: bs_price_with_q(S, K, T, r, sigma, q) - market_price
    try:
        # Search for sigma between 1% and 300%
        return brentq(objective, 0.01, 3.0)
    except:
        return 0.20  # Fallback to 20% vol if search fails


# ==========================================
# 3. Corrected Scenario Analysis
# ==========================================
def analyze_leap_calibrated(ticker, buy_days=304, exit_days_left=300):
    tk = yf.Ticker(ticker)
    curr_s = tk.fast_info['lastPrice']

    # Get closest expiration
    target_date = datetime.now() + timedelta(days=buy_days)
    expiry_str = min(tk.options, key=lambda d: abs(datetime.strptime(d, '%Y-%m-%d') - target_date))

    # Get Market Data
    chain = tk.option_chain(expiry_str)

    atm_opt = chain.calls.iloc[(chain.calls['strike'] - curr_s).abs().idxmin()]

    K = atm_opt['strike']
    market_ask = atm_opt['ask'] if atm_opt['ask'] > 0 else atm_opt['lastPrice']

    # Constants
    r, q = 0.042, 0.007  # 2026 Rates and QQQ Div Yield
    T_entry = buy_days / 365.0
    T_exit = exit_days_left / 365.0

    # CALIBRATION: Find the IV the market is actually pricing in
    calibrated_iv = find_iv(market_ask, curr_s, K, T_entry, r, q)

    moves = [-0.10, -0.05, 0, 0.05, 0.10]
    results = []

    for m in moves:
        new_s = curr_s * (1 + m)
        # Use the CALIBRATED IV for the exit price
        exit_price = bs_price_with_q(new_s, K, T_exit, r, calibrated_iv, q)
        ret = (exit_price / market_ask) - 1

        results.append({
            "Stock Move": f"{m * 100:+.0f}%",
            "Stock Price": f"${new_s:.2f}",
            "Opt Value": f"${exit_price:.2f}",
            "Return": f"{ret * 100:+.2f}%"
        })

    print(f"--- Calibrated Analysis for {ticker} ---")
    print(f"Market Price: ${market_ask:.2f} | Calibrated IV: {calibrated_iv * 100:.1f}%")
    print(f"Holding for {buy_days - exit_days_left} days...\n")
    return pd.DataFrame(results)


if __name__ == "__main__":
    df = analyze_leap_calibrated("QQQ", 304, 300)
    print(df.to_string(index=False))