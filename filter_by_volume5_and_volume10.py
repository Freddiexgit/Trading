import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# Download stock data

def filter(input_file, output_file):
    tickers = ["symbol"]
    df_tickers = pd.read_csv(input_file)
    for index, row in df_tickers.iterrows():
        ticker = row['symbol']
        df = yf.download(ticker, period="20d")

        df["VolMA5"] = df["Volume"].rolling(5).mean()
        df["VolMA10"] = df["Volume"].rolling(10).mean()
        df = df.iloc[-1:]
        if df["VolMA5"].iloc[-1] > df["VolMA10"].iloc[-1]:
            tickers.append(ticker)


    with open(output_file, 'w') as f:
        for ticker in tickers:
            f.write(f'{ticker}\n')