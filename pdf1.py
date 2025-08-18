import plotly.graph_objects as go
import pandas as pd
df = pd.read_csv("resource/price_history_AAPL_2025-08-15.csv", parse_dates=["Date"])
df.set_index("Date", inplace=True)
# Example with your OHLC dataframe
fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close']
)])
# import plotly.io as pio
# pio.kaleido.scope.default_format = "pdf"
# pio.kaleido.scope.default_width = 1000
# pio.kaleido.scope.default_height = 600
# pio.kaleido.scope.default_scale = 1

fig.write_image("candlestick.pdf")
# Save to PDF with Kaleido
fig.write_image("candlestick.pdf")   # automatically uses kaleido