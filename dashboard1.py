from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from PyPDF2 import PdfMerger

def ploy_fig(ticker, df):
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

    ha_df = df.copy()
    ha_df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    ha_df['HA_Open'] = (df['Open'].shift(1) + df['Close'].shift(1)) / 2
    ha_df.iloc[0, ha_df.columns.get_loc('HA_Open')] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
    ha_df['HA_High'] = ha_df[['HA_Open', 'HA_Close', 'High']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['HA_Open', 'HA_Close', 'Low']].min(axis=1)


    # Create subplots
    fig = make_subplots(
        rows=11, cols=1, shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.3, 0.15, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08],
        subplot_titles=[
            f'Candlestick with {ticker}', "Volume", "RSI", "KDJ", "MACD", "W%R", "DMI", "BIAS", "OBV", "CCI", "ROC"
        ]
    )

    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Price"), row=1, col=1)
    for ma, color in zip(["MA5", "MA10", "MA20", "MA60"], ["blue", "orange", "magenta", "green"]):
        fig.add_trace(go.Scatter(x=df.index, y=df[ma], mode="lines", line=dict(color=color), name=ma), row=1, col=1)


    # # Heiken Ashi overlay
    # fig.add_trace(go.Candlestick(
    #     x=ha_df.index,
    #     open=ha_df['HA_Open'], high=ha_df['HA_High'],
    #     low=ha_df['HA_Low'], close=ha_df['HA_Close'],
    #     name="Heiken Ashi",
    #     increasing_line_color="blue",
    #     decreasing_line_color="orange",
    #     opacity=0.5
    # ),row=2, col=1)



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

    fig.update_layout(height=2600, showlegend=True, xaxis_rangeslider_visible=False)
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"])  # hide weekends
        ]
    )
    # fig.show()
    return fig



ticker = "AAPL"
# Load your CSV
df = pd.read_csv("resource/price_history_AAPL_2025-08-16.csv", parse_dates=["Date"])
df.set_index("Date", inplace=True)


pdf_files = []

fig = ploy_fig(ticker, df)

# save temporary pdf for each stock
filename = f"{ticker}.pdf"
fig.write_image(filename, format="pdf",width=1200, height=1600)
pdf_files.append(filename)

# Merge all PDFs into one
merger = PdfMerger()
for pdf in pdf_files:
    merger.append(pdf)

merger.write(f"stock_indicators_{datetime.now().strftime('%Y-%m-%d')}.pdf")
merger.close()