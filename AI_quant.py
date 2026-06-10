import pandas as pd
import numpy as np
import yfinance as yf

# ==============================
# SETTINGS
# ==============================

START_DATE = "2016-01-01"
TOP_N = 10
STOP_LOSS = 0.15
TICKER_FILE = "tickers.csv"
SECTOR_FILE = "sector_map.csv"


# ==============================
# DOWNLOAD PRICE DATA
# ==============================

def download_prices(tickers):

    prices = yf.download(
        tickers,
        start=START_DATE,
        auto_adjust=True,
        progress=False
    )["Close"]

    return prices


# ==============================
# MOMENTUM
# ==============================

def momentum(prices):

    r6 = prices.pct_change(126)
    r12 = prices.pct_change(252)

    return 0.6*r6 + 0.4*r12


# ==============================
# RS ACCELERATION
# ==============================

def rs_acceleration(prices):

    r3 = prices.pct_change(63)
    r6 = prices.pct_change(126)

    return r3 - r6


# ==============================
# TREND FILTER
# ==============================

def trend(prices):

    ma200 = prices.rolling(200).mean()

    return (prices > ma200).astype(int)


# ==============================
# EARNINGS GROWTH
# ==============================

def earnings_growth(ticker):

    try:

        t = yf.Ticker(ticker)
        income = t.income_stmt

        if income is None or income.shape[1] < 2:
            return 0

        latest = income.iloc[0,0]
        prev = income.iloc[0,1]

        if prev == 0:
            return 0

        return (latest - prev) / abs(prev)

    except:
        return 0


def build_earnings_vector(tickers):

    eg = {}

    for t in tickers:
        print("earnings:", t)
        eg[t] = earnings_growth(t)

    return pd.Series(eg)


# ==============================
# INDUSTRY MOMENTUM
# ==============================

def industry_momentum(prices, sector_map):

    r6 = prices.pct_change(126)

    sector_returns = {}

    for sector in sector_map["sector"].unique():

        tickers = sector_map[
            sector_map["sector"] == sector
        ]["symbol"]

        tickers = [t for t in tickers if t in prices.columns]

        if len(tickers) == 0:
            continue

        sector_returns[sector] = r6[tickers].mean(axis=1)

    sector_df = pd.DataFrame(sector_returns)

    industry_factor = pd.DataFrame(index=prices.index)

    for t in prices.columns:

        s = sector_map.loc[
            sector_map["symbol"] == t, "sector"
        ]

        if len(s) == 0:
            industry_factor[t] = 0
            continue

        industry_factor[t] = sector_df[s.values[0]]

    return industry_factor


# ==============================
# FACTOR SCORE
# ==============================

def factor_score(prices, industry_factor, earnings):

    m = momentum(prices)
    accel = rs_acceleration(prices)
    t = trend(prices)

    eg_matrix = pd.DataFrame(
        np.tile(earnings.values, (len(prices),1)),
        index=prices.index,
        columns=prices.columns
    )

    score = (
        0.4*m +
        0.2*accel +
        0.2*industry_factor +
        0.1*eg_matrix +
        0.1*t
    )

    return score


# ==============================
# BACKTEST ENGINE
# ==============================

def run_backtest(prices, score):

    dates = prices.resample("M").last().index

    portfolio_value = 1.0
    equity_curve = []

    for i in range(len(dates)-1):

        d = dates[i]
        next_d = dates[i+1]

        s = score.loc[d].dropna()

        top = s.nlargest(TOP_N).index

        weight = 1 / TOP_N

        period_return = 0

        for ticker in top:

            p0 = prices.loc[d, ticker]
            p1 = prices.loc[next_d, ticker]

            r = (p1 - p0) / p0

            if r < -STOP_LOSS:
                r = -STOP_LOSS

            period_return += r * weight

        portfolio_value *= (1 + period_return)

        equity_curve.append({
            "Date": next_d,
            "Return": period_return,
            "Equity": portfolio_value
        })

    df = pd.DataFrame(equity_curve)

    return df.set_index("Date")


# ==============================
# PERFORMANCE METRICS
# ==============================

def performance_stats(df):

    r = df["Return"]

    years = len(r)/12

    cagr = df["Equity"].iloc[-1]**(1/years)-1

    sharpe = r.mean()/r.std()*np.sqrt(12)

    drawdown = df["Equity"]/df["Equity"].cummax()-1

    max_dd = drawdown.min()

    return {
        "CAGR": round(cagr,3),
        "Sharpe": round(sharpe,3),
        "MaxDrawdown": round(max_dd,3)
    }


# ==============================
# MAIN
# ==============================

def main():

    tickers = pd.read_csv(TICKER_FILE)["symbol"].tolist()
    sector_map = pd.read_csv(SECTOR_FILE)

    print("Downloading prices...")
    prices = download_prices(tickers)

    print("Calculating earnings growth...")
    earnings = build_earnings_vector(tickers)

    print("Computing industry momentum...")
    industry_factor = industry_momentum(prices, sector_map)

    print("Computing factor scores...")
    score = factor_score(prices, industry_factor, earnings)

    print("Running backtest...")
    equity = run_backtest(prices, score)

    stats = performance_stats(equity)

    print("\nStrategy Performance")
    print(stats)

    equity.to_csv("equity_curve.csv")


if __name__ == "__main__":
    main()