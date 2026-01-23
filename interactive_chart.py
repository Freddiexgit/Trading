import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# --- Load stock data ---
df = yf.download("AAPL", period="6mo", interval="1d")

# --- Calculate Moving Averages ---
df["MA20"] = df["Close"].rolling(20).mean()
df["MA50"] = df["Close"].rolling(50).mean()

# --- Candlestick Chart ---
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df.index,
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="Candlestick"
))

# --- Moving Averages ---
fig.add_trace(go.Scatter(x=df.index, y=df["MA20"],
                         line=dict(color="blue", width=1.5),
                         name="MA20"))
fig.add_trace(go.Scatter(x=df.index, y=df["MA50"],
                         line=dict(color="orange", width=1.5),
                         name="MA50"))

# --- Volume (secondary y-axis) ---
fig.add_trace(go.Bar(x=df.index, y=df["Volume"],
                     name="Volume", marker_color="gray",
                     opacity=0.3, yaxis="y2"))

# --- Layout ---
fig.update_layout(
    title="AAPL Stock Price (Interactive)",
    xaxis_title="Date",
    yaxis_title="Price",
    yaxis2=dict(overlaying="y", side="right", showgrid=False, position=1),
    xaxis_rangeslider_visible=False,
    template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

fig.show()