import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

def detect_breakout(ticker, lookback=20, volume_factor=1.5):
    df = data.get_transaction_df(ticker, period="6mo", interval="1d")
    # df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    # df.dropna(inplace=True)

    # Rolling high/low
    df["Rolling_High"] = df["Close"].rolling(lookback).max()
    df["Rolling_Low"] = df["Close"].rolling(lookback).min()

    # Price breakout
    df["Price_Breakout"] = df["Close"] > df["Rolling_High"].shift(1)

    # Volume breakout
    df["Avg_Volume"] = df["Volume"].rolling(lookback).mean()
    df["Volume_Breakout"] = df["Volume"] > df["Avg_Volume"] * volume_factor

    # Combined breakout
    df["Breakout_Signal"] = df["Price_Breakout"] & df["Volume_Breakout"]

    return df

def plot_breakout(df, ticker):
    fig = go.Figure()

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="Price"
    ))

    # Highlight breakout signals
    breakout_points = df[df["Breakout_Signal"]]
    fig.add_trace(go.Scatter(
        x=breakout_points.index,
        y=breakout_points["Close"],
        mode="markers",
        marker=dict(size=12, color="red", symbol="star"),
        name="Breakout"
    ))

    # Add rolling resistance line (optional)
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Rolling_High"],
        mode="lines",
        line=dict(color="blue", dash="dot"),
        name=f"{20}-day High"
    ))

    fig.update_layout(
        title=f"{ticker} Price & Volume Breakout Detection",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_white"
    )

    fig.show()

# --- Run example ---
ticker = "RBLX"
df = detect_breakout(ticker)
plot_breakout(df, ticker)