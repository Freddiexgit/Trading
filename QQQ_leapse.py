import yfinance as yf
import pandas as pd
import numpy as np
import math
from math import log, sqrt, exp
from scipy.stats import norm


# =========================
# Enhanced Black-Scholes
# =========================
def bs_call_price_real(S, K, T, r, sigma, q=0.01):
    S, K, T, sigma = float(S), float(K), float(T), float(sigma)
    if T <= 0 or sigma <= 0: return max(S - K, 0.0)
    d1 = (log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    price = S * exp(-q * T) * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
    return max(price, 0.01)


# =========================
# Regime-Filtered Backtest Engine
# =========================
def backtest_qqq_leaps_regime(
        start="2016-01-01",
        end=None,
        initial_capital=50000  # Realistic starting capital for whole contracts
):
    # 1) Setup Data & Indicators
    qqq = yf.download("QQQ", start=start, end=end, auto_adjust=True)
    qqq["Ret"] = qqq["Close"].pct_change()
    qqq["RV"] = qqq["Ret"].rolling(60).std() * np.sqrt(252)

    # The Regime Filter: 200-Day Simple Moving Average
    qqq["SMA_200"] = qqq["Close"].rolling(200).mean()
    qqq = qqq.dropna().copy()

    dates = qqq.index
    portfolio_value = initial_capital
    trades = []
    i = 0

    # Constants
    r = 0.04
    div_yield = 0.007
    slippage_pct = 0.02
    trading_days_to_hold = int((300 - 180) * (252 / 365))  # ~82 trading days

    while i < len(dates):
        buy_date = dates[i]
        S_buy = float(qqq.loc[buy_date, "Close"])
        sma_200 = float(qqq.loc[buy_date, "SMA_200"])
        rv_buy = float(qqq.loc[buy_date, "RV"])

        # 2) DYNAMIC REGIME LOGIC
        if S_buy > sma_200:
            # UPTREND: Risk-on. Normal IV premium, aggressive sizing.
            iv_premium = 1.15
            allocation_pct = 0.50
            regime = "Bull"
        else:
            # DOWNTREND: Risk-off. Extreme IV premium, defensive sizing.
            iv_premium = 1.40
            allocation_pct = 0.20  # Cut size by more than half
            regime = "Bear"

        iv_buy = rv_buy * iv_premium
        T_buy = 300 / 252.0
        T_sell = 180 / 252.0
        K = S_buy

        # 3) Calculate Entry & Realistic Sizing
        fair_buy_price = bs_call_price_real(S_buy, K, T_buy, r, iv_buy, q=div_yield)
        actual_buy_price = fair_buy_price * (1 + slippage_pct)
        contract_cost = actual_buy_price * 100

        trade_capital = portfolio_value * allocation_pct
        contracts = math.floor(trade_capital / contract_cost)

        # Skip trade if we can't afford 1 contract
        if contracts < 1:
            i += 21  # Wait a month and try again
            continue

        actual_deployed = contracts * contract_cost
        cash_reserve = portfolio_value - actual_deployed

        # 4) Forward to Sell Date
        sell_idx = i + trading_days_to_hold
        if sell_idx >= len(dates): break

        sell_date = dates[sell_idx]
        S_sell = float(qqq.loc[sell_date, "Close"])
        rv_sell = float(qqq.loc[sell_date, "RV"])
        sma_200_sell = float(qqq.loc[sell_date, "SMA_200"])

        # Determine exit regime for the sell-side IV premium
        exit_premium = 1.15 if S_sell > sma_200_sell else 1.40
        iv_sell = rv_sell * exit_premium

        fair_sell_price = bs_call_price_real(S_sell, K, T_sell, r, iv_sell, q=div_yield)
        actual_sell_price = fair_sell_price * (1 - slippage_pct)

        # 5) Portfolio Update
        trade_result = contracts * actual_sell_price * 100
        portfolio_value = cash_reserve + trade_result

        trades.append({
            "Buy_Date": buy_date.date(),
            "Regime": regime,
            "Contracts": contracts,
            "S_Buy": round(S_buy, 2),
            "Opt_Buy": round(actual_buy_price, 2),
            "Opt_Sell": round(actual_sell_price, 2),
            "Return": round((actual_sell_price / actual_buy_price) - 1, 4),
            "Port_Value": round(portfolio_value, 2)
        })
        i = sell_idx + 1

    return pd.DataFrame(trades)


if __name__ == "__main__":
    results = backtest_qqq_leaps_regime(start="2016-01-01")
    print(results.tail(10).to_string(index=False))
