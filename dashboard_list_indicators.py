import os
from datetime import datetime

import numpy as np
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from PyPDF2 import PdfMerger



def ploy_fig(ticker, df,skip_macd_sell = "Yes"):
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

    df["MACD_buy_signal"] = np.where((df["MACD"] > df["MACD_signal"]) & (df["MACD"].shift(1) <= df["MACD_signal"].shift(1)), df["Close"], np.nan)
    df["MACD_sell_signal"] = np.where((df["MACD"] < df["MACD_signal"]) & (df["MACD"].shift(1) >= df["MACD_signal"].shift(1)), df["Close"], np.nan)


    df["OBV"] = ta.volume.OnBalanceVolumeIndicator(df["Close"], df["Volume"]).on_balance_volume()


    macd1 = ta.trend.MACD(df["Close"], window_slow=34,  # slow EMA
                          window_fast=5,  # fast EMA
                          window_sign=5)  # signal EMA
    df["MACD1"] = macd1.macd()
    df["MACD_signal1"] = macd1.macd_signal()
    df["MACD_hist1"] = macd1.macd_diff()
    df["MACD_buy_signal1"] = np.where(
        (df["MACD1"] > df["MACD_signal1"]) & (df["MACD1"].shift(1) <= df["MACD_signal1"].shift(1)), df["Close"], np.nan)
    df["MACD_sell_signal1"] = np.where(
        (df["MACD1"] < df["MACD_signal1"]) & (df["MACD1"].shift(1) >= df["MACD_signal1"].shift(1)), df["Close"], np.nan)

    df = df.iloc[50:]

    last_buy_idx = df["MACD_buy_signal1"].last_valid_index()
    last_sell_idx = df["MACD_sell_signal1"].last_valid_index()

    # Compare which is more recent
    if last_buy_idx is None and last_sell_idx is None:
        last_signal = None
    elif last_sell_idx is None or (last_buy_idx is not None and last_buy_idx > last_sell_idx):
        last_signal = "Buy"
        last_price = df.loc[last_buy_idx, "MACD_buy_signal1"]
        last_date = last_buy_idx
    else:
        last_signal = "Sell"
        last_price = df.loc[last_sell_idx, "MACD_sell_signal1"]
        last_date = last_sell_idx

    if last_signal != "Buy" and skip_macd_sell == "Yes":
         return  None
    # Create subplots
    fig = make_subplots(
        rows=7, cols=1, shared_xaxes=True,
        vertical_spacing=0.01,
        row_heights=[4, 2, 2, 1, 1, 1, 1 ],
        subplot_titles=[
            f' {ticker}', "Acute MACD","MACD","Volume","RSI", "KDJ", "OBV"
        ]
    )

    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Price"), row=1, col=1)
    for ma, color in zip(["MA5", "MA10", "MA20", "MA60"], ["blue", "orange", "magenta", "green"]):
        fig.add_trace(go.Scatter(x=df.index, y=df[ma], mode="lines", line=dict(color=color), name=ma), row=1, col=1)
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MACD_buy_signal1"],
                mode="markers",
                marker=dict(symbol="triangle-up", color="purple", size=16),
                name="MACD Buy",
                showlegend=False
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MACD_sell_signal1"],
                mode="markers",
                marker=dict(symbol="triangle-down", color="red", size=16),
                name="MACD Sell",
                showlegend = False
            ),
            row=1, col=1
        )




    # Acute MACD
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist1"], name="MACD Hist", marker_color="red"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD1"], mode="lines", name="MACD"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal1"], mode="lines", name="Signal"), row=2, col=1)
    # MACD
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"], name="MACD Hist", marker_color="gray"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines", name="MACD"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"], mode="lines", name="Signal"), row=3, col=1)
    # Volume
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color="green"), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["VolMA5"], mode="lines", line=dict(color="purple"), name="VolMA5"), row=4,
                  col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["VolMA10"], mode="lines", line=dict(color="pink"), name="VolMA10"), row=4,
                  col=1)



    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI"), row=5, col=1)

    # KDJ
    fig.add_trace(go.Scatter(x=df.index, y=df["K"], mode="lines", name="%K"), row=6, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["D"], mode="lines", name="%D"), row=6, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["J"], mode="lines", name="%J"), row=6, col=1)

    # OBV
    fig.add_trace(go.Scatter(x=df.index, y=df["OBV"], mode="lines", name="OBV"), row=7, col=1)



    fig.update_layout(height=1000, showlegend=True, xaxis_rangeslider_visible=False)
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"])  # hide weekends
        ]
    )
    # fig.show()
    return fig


def generate_pdf(df_tickers,output_filename,skip_macd_sell="Yes"):
    pdf_files = []
    for index, row in df_tickers.iterrows():
        print(f"Index: {index}, Value: {row['symbol']}")
        ticker = row['symbol']
        try:
            stock = yf.Ticker(ticker)
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            continue
        df = stock.history(period="6mo")


        fig = ploy_fig(f"{ticker}_{stock.info['shortName']}_{stock.info.get('industry')}", df,skip_macd_sell)
        if fig == None:
            print(f"Skipping {ticker} due to MACD sell .")
            continue
        # save temporary pdf for each stock
        filename = f"{ticker}.pdf"
        fig.write_image(f"resource/temp/{filename}", format="pdf",width=1200, height=1600)
        pdf_files.append(filename)

    # Merge all PDFs into one
    merger = PdfMerger()
    for pdf in pdf_files:
        merger.append(f"resource/temp/{pdf}")

    merger.write(output_filename)
    merger.close()
    for pdf in pdf_files:
        os.remove(f"resource/temp/{pdf}")  # Clean up temporary files