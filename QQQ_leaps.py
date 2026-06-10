import yfinance as yf
import pandas as pd
import numpy as np
from math import log, sqrt, exp
from scipy.stats import norm

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1400)

# ============================================================
# Black-Scholes Greeks and Pricing
# ============================================================

def bs_call_price(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return max(S - K, 0)
    d1 = (log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*sqrt(T))
    d2 = d1 - sigma*sqrt(T)
    price = S * norm.cdf(d1) - K * exp(-r*T) * norm.cdf(d2)
    delta = norm.cdf(d1)
    gamma = norm.pdf(d1) / (S * sigma * sqrt(T))
    theta = (-S*norm.pdf(d1)*sigma/(2*sqrt(T)) - r*K*exp(-r*T)*norm.cdf(d2))/365
    return price, delta, gamma, theta

# ============================================================
# Fetch option chain and IV
# ============================================================

def get_option_chain(ticker, date, top_n=3):
    tk = yf.Ticker(ticker)
    S = tk.history(start=date - pd.Timedelta(days=2),
                   end=date + pd.Timedelta(days=1))["Close"]
    if S.empty:
        return pd.DataFrame(), None
    S = S.iloc[-1]  # last available price before or on target date

    expiries = tk.options
    if not expiries:
        return pd.DataFrame(), None  # <--- fix here

    expiry = expiries[0]
    chain = tk.option_chain(expiry)
    df = chain.calls.copy()

    rows = []
    T = (pd.to_datetime(expiry) - date).days / 252

    for _, row in df.iterrows():
        K = row["strike"]
        iv = row["impliedVolatility"]
        if iv is None or iv == 0:
            continue
        price, delta, gamma, theta = bs_call_price(S, K, T, r=0.02, sigma=iv)
        if price <= 0:
            continue
        leverage = (abs(delta) * S) / price
        pro_score = leverage * abs(delta) / (abs(theta) + 1e-6)
        rows.append({
            "strike": K, "price": price, "delta": delta,
            "gamma": gamma, "theta": theta, "iv": iv,
            "leverage": leverage, "score": pro_score,
            "expiry": expiry
        })

    df_out = pd.DataFrame(rows)
    df_out = df_out.sort_values("score", ascending=False).head(top_n)
    return df_out, S  # <--- always return two values
# ============================================================
# Backtest Engine
# ============================================================

def backtest_qqq_leaps_pro(
    ticker="QQQ",
    start="2016-01-01",
    end="2026-2-28",
    capital=10000,
    position_size=0.1,
    stop_loss=0.5,
    top_n=3
):
    dates = pd.date_range(start, end, freq="7D")  # weekly rebalance
    cash = capital
    open_positions = []
    equity_curve = []

    for date in dates:
        # -------------------
        # Update open positions
        # -------------------
        new_positions = []
        for pos in open_positions:
            chain, S = get_option_chain(ticker, date)
            if chain.empty:
                continue
            # find current price of same strike
            strike_row = chain[chain["strike"] == pos["strike"]]
            if strike_row.empty:
                # use intrinsic value proxy
                current_price = max(0, S - pos["strike"])
            else:
                current_price = float(strike_row["price"].iloc[0])
            pnl = (current_price - pos["entry_price"]) / pos["entry_price"]
            # stop loss
            if pnl < -stop_loss:
                cash += pos["contracts"] * current_price * 100
                continue
            # expiry check
            if pd.to_datetime(pos["expiry"]) <= date:
                cash += pos["contracts"] * current_price * 100
                continue
            pos["current_price"] = current_price
            new_positions.append(pos)
        open_positions = new_positions

        # -------------------
        # Get new signals
        # -------------------
        df, S = get_option_chain(ticker, date, top_n=top_n)
        if df.empty:
            equity_curve.append(cash + sum([p.get("current_price",p["entry_price"])*p["contracts"]*100 for p in open_positions]))
            continue
        for _, row in df.iterrows():
            allocation = capital * position_size
            contracts = allocation // (row["price"] * 100)
            if contracts <= 0:
                continue
            cost = contracts * row["price"] * 100
            if cash < cost:
                continue
            # simulate bid/ask
            buy_price = row["price"] * 1.02  # buy at ask
            cash -= cost
            open_positions.append({
                "strike": row["strike"],
                "entry_price": buy_price,
                "expiry": row["expiry"],
                "contracts": contracts
            })

        # -------------------
        # Update equity curve
        # -------------------
        total_value = cash + sum([p.get("current_price",p["entry_price"])*p["contracts"]*100 for p in open_positions])
        equity_curve.append(total_value)

    df_equity = pd.DataFrame({"date": dates, "equity": equity_curve})
    total_return = df_equity["equity"].iloc[-1]/df_equity["equity"].iloc[0] - 1

    print(f"Initial Capital: {capital}")
    print(f"Final Portfolio Value: ${df_equity['equity'].iloc[-1]:,.2f}")
    print(f"Total Return: {total_return:.2%}")
    return df_equity

# ============================================================
# Run Pro Backtest
# ============================================================

if __name__ == "__main__":
    df_result = backtest_qqq_leaps_pro()
    print(df_result.tail())