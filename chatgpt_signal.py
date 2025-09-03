import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

def get_stock_data(ticker, period="6mo", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval)
    except Exception as e:
        print(f"Error downloading {ticker}")
        return pd.DataFrame()
    df.dropna(inplace=True)
    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    return df

def detect_signals(df):
    signals = {}

    # --- EMA CROSSOVER (Trend) ---
    df["EMA5"] = df["Close"].ewm(span=5).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA_Crossover"] = (df["EMA5"] > df["EMA20"]) & (df["EMA5"].shift(1) <= df["EMA20"].shift(1))
    if df["EMA_Crossover"].iloc[-1]:
        signals["EMA_Crossover"] = True

    # --- RSI Bullish Divergence (Reversal) ---
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    recent = df.tail(10)
    price_low1, price_low2 = recent["Close"].iloc[-5], recent["Close"].iloc[-1]
    rsi_low1, rsi_low2 = recent["RSI"].iloc[-5], recent["RSI"].iloc[-1]
    if price_low2 < price_low1 and rsi_low2 > rsi_low1:
        signals["RSI_Divergence"] = True

    # --- Breakout with Volume (Momentum) ---
    df["Resistance"] = df["Close"].rolling(window=20).max().shift(1)
    df["AvgVolume"] = df["Volume"].rolling(window=20).mean()
    breakout = (df["Close"].iloc[-1] > df["Resistance"].iloc[-1]) & \
               (df["Volume"].iloc[-1] > 1.5 * df["AvgVolume"].iloc[-1])
    if breakout:
        signals["Breakout_Volume"] = True

    return signals, df

def plot_signals(df, ticker, signals):
    fig = go.Figure()

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="Candles"
    ))

    # EMA lines
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA5"], mode="lines", line=dict(color="blue"), name="EMA5"))
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], mode="lines", line=dict(color="orange"), name="EMA20"))

    # Mark EMA crossover
    if "EMA_Crossover" in signals:
        cross = df[df["EMA_Crossover"]]
        fig.add_trace(go.Scatter(
            x=cross.index, y=cross["Close"],
            mode="markers", marker=dict(color="green", size=12, symbol="triangle-up"),
            name="EMA Crossover"
        ))

    # Mark Breakout
    if "Breakout_Volume" in signals:
        resistance = df["Resistance"].iloc[-1]
        fig.add_hline(y=resistance, line_dash="dot", line_color="purple", annotation_text="Breakout Level")
        fig.add_trace(go.Scatter(
            x=[df.index[-1]], y=[df["Close"].iloc[-1]],
            mode="markers", marker=dict(color="purple", size=14, symbol="star"),
            name="Breakout"
        ))

    # Mark RSI Divergence
    if "RSI_Divergence" in signals:
        fig.add_trace(go.Scatter(
            x=[df.index[-1]], y=[df["Close"].iloc[-1]],
            mode="markers", marker=dict(color="red", size=14, symbol="diamond"),
            name="RSI Divergence"
        ))

    fig.update_layout(
        title=f"{ticker} Buy Signals",
        xaxis_title="Date", yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_white"
    )
    fig.show()

# --- Example Run ---
df = pd.read_csv(f'resource/nyse_and_nasdaq_top_500.csv')
tickers = df['symbol'].dropna().tolist()

for ticker in tickers:
    df = get_stock_data(ticker)
    if df.empty: continue
    signals, df = detect_signals(df)
    if signals:
        print(f"Signals for {ticker}: {signals}")
        plot_signals(df, ticker, signals)
    else:
        print(f"No signals for {ticker}")