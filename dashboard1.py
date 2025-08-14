import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta

# Load your CSV
df = pd.read_csv("resource/price_history_AAPL_2025-08-15.csv", parse_dates=["Date"])
df.set_index("Date", inplace=True)

# Moving averages
df["MA5"] = df["Close"].rolling(5).mean()
df["MA10"] = df["Close"].rolling(10).mean()
df["MA20"] = df["Close"].rolling(20).mean()
df["MA60"] = df["Close"].rolling(60).mean()

df["VolMA5"] = df["Volume"].rolling(5).mean()
df["VolMA10"] = df["Volume"].rolling(10).mean()

# Technical indicators
df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()

stoch = ta.momentum.StochasticOscillator(df["High"], df["Low"], df["Close"])
df["K"] = stoch.stoch()
df["D"] = stoch.stoch_signal()
df["J"] = 3 * df["K"] - 2 * df["D"]

macd = ta.trend.MACD(df["Close"])
df["MACD"] = macd.macd()
df["MACD_signal"] = macd.macd_signal()
df["MACD_hist"] = macd.macd_diff()

df["W%R"] = ta.momentum.WilliamsRIndicator(df["High"], df["Low"], df["Close"]).williams_r()

dmi = ta.trend.ADXIndicator(df["High"], df["Low"], df["Close"])
df["+DI"] = dmi.adx_pos()
df["-DI"] = dmi.adx_neg()
df["ADX"] = dmi.adx()
df["ADXR"] = df["ADX"].rolling(5).mean()

df["BIAS"] = (df["Close"] - df["MA20"]) / df["MA20"] * 100
df["OBV"] = ta.volume.OnBalanceVolumeIndicator(df["Close"], df["Volume"]).on_balance_volume()
df["CCI"] = ta.trend.CCIIndicator(df["High"], df["Low"], df["Close"]).cci()
df["ROC"] = ta.momentum.ROCIndicator(df["Close"]).roc()

# Create subplots
fig = make_subplots(
    rows=11, cols=1, shared_xaxes=True,
    vertical_spacing=0.02,
    row_heights=[0.3, 0.15, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08],
    subplot_titles=[
        "Candlestick with MAs", "Volume", "RSI", "KDJ", "MACD", "W%R", "DMI", "BIAS", "OBV", "CCI", "ROC"
    ]
)

# Candlestick
fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Price"), row=1, col=1)
for ma, color in zip(["MA5", "MA10", "MA20", "MA60"], ["blue", "orange", "magenta", "green"]):
    fig.add_trace(go.Scatter(x=df.index, y=df[ma], mode="lines", line=dict(color=color), name=ma), row=1, col=1)

# Volume
fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color="green"), row=2, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["VolMA5"], mode="lines", line=dict(color="purple"), name="VolMA5"), row=2, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["VolMA10"], mode="lines", line=dict(color="pink"), name="VolMA10"), row=2, col=1)

# RSI
fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI"), row=3, col=1)

# KDJ
fig.add_trace(go.Scatter(x=df.index, y=df["K"], mode="lines", name="%K"), row=4, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["D"], mode="lines", name="%D"), row=4, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["J"], mode="lines", name="%J"), row=4, col=1)

# MACD
fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"], name="MACD Hist", marker_color="gray"), row=5, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines", name="MACD"), row=5, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"], mode="lines", name="Signal"), row=5, col=1)

# W%R
fig.add_trace(go.Scatter(x=df.index, y=df["W%R"], mode="lines", name="W%R"), row=6, col=1)

# DMI
fig.add_trace(go.Scatter(x=df.index, y=df["+DI"], mode="lines", name="+DI"), row=7, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["-DI"], mode="lines", name="-DI"), row=7, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["ADX"], mode="lines", name="ADX"), row=7, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["ADXR"], mode="lines", name="ADXR"), row=7, col=1)

# BIAS
fig.add_trace(go.Scatter(x=df.index, y=df["BIAS"], mode="lines", name="BIAS"), row=8, col=1)

# OBV
fig.add_trace(go.Scatter(x=df.index, y=df["OBV"], mode="lines", name="OBV"), row=9, col=1)

# CCI
fig.add_trace(go.Scatter(x=df.index, y=df["CCI"], mode="lines", name="CCI"), row=10, col=1)

# ROC
fig.add_trace(go.Scatter(x=df.index, y=df["ROC"], mode="lines", name="ROC"), row=11, col=1)

fig.update_layout(height=1600, showlegend=True, xaxis_rangeslider_visible=False)
fig.show()