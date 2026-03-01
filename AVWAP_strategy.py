import yfinance as yf
import pandas as pd
import numpy as np
tickers = pd.read_csv("resource/my_vip.csv")["symbol"].tolist()

def market_ok(symbol="SPY") -> bool:
    spy = yf.download(symbol, period="1y", auto_adjust=True, progress=False)

    spy["MA50"] = spy["Close"].rolling(50).mean()
    spy["MA200"] = spy["Close"].rolling(200).mean()

    last_close = float(spy["Close"].iloc[-1])
    last_ma50 = float(spy["MA50"].iloc[-1])
    last_ma200 = float(spy["MA200"].iloc[-1])

    cond1 = last_close > last_ma50
    cond2 = last_ma50 > last_ma200

    return cond1 and cond2

def momentum_score(df):
    ret_3m = df["Close"].pct_change(63).iloc[-1]
    ret_6m = df["Close"].pct_change(126).iloc[-1]

    ma50 = df["Close"].rolling(50).mean()
    ma150 = df["Close"].rolling(150).mean()

    trend = (
        df["Close"].iloc[-1] > ma50.iloc[-1] >
        ma150.iloc[-1]
    )

    volume_expansion = (
        df["Volume"].iloc[-5:].mean() >
        1.3 * df["Volume"].rolling(50).mean().iloc[-1]
    )

    score = ret_3m*0.6 + ret_6m*0.4

    return score if trend and volume_expansion else None

def volatility_contraction(df):
    ranges = (df["High"] - df["Low"]) / df["Close"]

    recent = ranges.tail(5).mean()
    past = ranges.tail(30).mean()

    return recent < past * 0.7

def near_high(df):
    high_60 = df["High"].rolling(60).max().iloc[-1]
    price = df["Close"].iloc[-1]

    return price > high_60 * 0.92

def run_screener(tickers):
    results = []

    if not market_ok():
        print("Market regime weak — reduce exposure.")
        return results

    for t in tickers:
        df = yf.download(t, period="1y", auto_adjust=True)

        if len(df) < 200:
            continue

        score = momentum_score(df)

        if score is None:
            continue

        if not volatility_contraction(df):
            continue

        if not near_high(df):
            continue

        results.append((t, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results

leaders = run_screener(tickers)
print(leaders)