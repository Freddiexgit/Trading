import pandas as pd
import numpy as np
import yfinance as yf
from statsmodels.regression.rolling import RollingOLS
import matplotlib.pyplot as plt

# ============================================================
# CONFIGURATION
# ============================================================
PAIRS = [("QQQ", "SPY"), ("TLT", "IEF"), ("GLD", "SLV")]
START = "2018-01-01"
END = "2026-03-31"

LOOKBACK = 60  # Rolling window for Mean/Std
Z_ENTRY = 2.0  # Entry Threshold
Z_EXIT = 0.5  # Profit Taking Threshold
MAX_HOLD_DAYS = 22  # Time-Stop (Approx 1 month)
TARGET_VOL = 0.12  # 12% Annualized Vol Target
COSTS = 0.0005  # 5bps Slippage/Comm per side


# ============================================================
# ENGINE FUNCTIONS
# ============================================================

def get_data(tickers):
    data = yf.download(tickers, start=START, end=END)["Close"]
    return data.ffill().dropna()


def compute_signals_with_time_stop(z_score):
    """
    Implements entry, exit, and a hard time-stop.
    """
    signals = pd.Series(0, index=z_score.index)
    duration = pd.Series(0, index=z_score.index)
    current_side = 0
    days_held = 0

    for i in range(1, len(z_score)):
        z = z_score.iloc[i]

        # If not in a position, look for entry
        if current_side == 0:
            if z > Z_ENTRY:
                current_side = -1  # Short the spread
                days_held = 0
            elif z < -Z_ENTRY:
                current_side = 1  # Long the spread
                days_held = 0

        # If in a position, check for exit conditions
        else:
            days_held += 1
            # Condition 1: Profit/Mean Reversion
            if (current_side == 1 and z >= -Z_EXIT) or (current_side == -1 and z <= Z_EXIT):
                current_side = 0
            # Condition 2: Time-Stop
            elif days_held >= MAX_HOLD_DAYS:
                current_side = 0

        signals.iloc[i] = current_side
        duration.iloc[i] = days_held

    return signals


def backtest_system():
    # 1. Fetch Data
    all_tickers = list(set([t for pair in PAIRS for t in pair] + ["^VIX"]))
    data = get_data(all_tickers)
    vix = data["^VIX"]
    prices = data.drop(columns=["^VIX"])

    portfolio_returns = pd.Series(0.0, index=prices.index)

    # 2. Process each pair
    for a, b in PAIRS:
        print(f"Processing Pair: {a}/{b}...")

        # Dynamic Hedge Ratio (Beta)
        model = RollingOLS(prices[a], prices[b], window=LOOKBACK)
        beta = model.fit().params.iloc[:, 0]

        # Calculate Spread & Z-Score
        spread = prices[a] - (beta * prices[b])
        z_score = (spread - spread.rolling(LOOKBACK).mean()) / spread.rolling(LOOKBACK).std()
        z_score = z_score.fillna(0)

        # Generate Signals (with Entry, Exit, and Time-Stop)
        raw_signal = compute_signals_with_time_stop(z_score)

        # Calculate Returns
        ret_a = prices[a].pct_change()
        ret_b = prices[b].pct_change()
        # Spread return accounts for the cost of the hedge
        spread_ret = (ret_a - beta * ret_b) / (1 + abs(beta))

        # Volatility Sizing
        realized_vol = spread_ret.rolling(20).std() * np.sqrt(252)
        vol_scaler = (TARGET_VOL / realized_vol).replace([np.inf, -np.inf], 0).fillna(0)

        # Crash Protection (VIX Filter)
        vix_filter = np.where(vix.rolling(5).mean() > 30, 0, 1)

        # Final Weights
        weights = raw_signal * vol_scaler * vix_filter

        # PnL Calculation (including transaction costs)
        trades = weights.diff().abs()
        pnl = (weights.shift(1) * spread_ret) - (trades * COSTS)

        portfolio_returns += pnl

    # Normalize by number of pairs
    portfolio_returns = portfolio_returns / len(PAIRS)
    return portfolio_returns


# ============================================================
# PERFORMANCE METRICS & RUN
# ============================================================

if __name__ == "__main__":
    returns = backtest_system()

    # Metrics
    cum_ret = (1 + returns).cumprod()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
    drawdown = (cum_ret / cum_ret.cummax()) - 1
    max_dd = drawdown.min()

    print("\n--- PERFORMANCE SUMMARY ---")
    print(f"Total Return: {cum_ret.iloc[-1] - 1:.2%}")
    print(f"Annualized Sharpe: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")

    # Plotting
    plt.figure(figsize=(12, 6))
    plt.plot(cum_ret, label="Equity Curve")
    plt.title("Modern LTCM-Style System (Time-Stop + Vol Targeting)")
    plt.grid(True)
    plt.show()