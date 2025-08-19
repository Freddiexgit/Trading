import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# Download stock data

def filter(input_file, output_file):
    ticker_and_vol = {}
    df_tickers = pd.read_csv(input_file)
    for index, row in df_tickers.iterrows():
        ticker = row['symbol']
        df = yf.download(ticker, period="20d")

        df["VolMA5"] = df["Volume"].rolling(5).mean()
        df["VolMA10"] = df["Volume"].rolling(10).mean()
        df = df.iloc[-1:]
        if df["VolMA5"].iloc[-1] > df["VolMA10"].iloc[-1]:
            ticker_and_vol[ticker] = df["VolMA5"].iloc[-1] - df["VolMA10"].iloc[-1]

    sorted_dict = dict(sorted(ticker_and_vol.items(), key=lambda item: item[1], reverse=True))
    with open(output_file, 'w') as f:
        f.write('symbol\n')
        for key, value in sorted_dict.items():
            f.write(f'{key}\n')

    # with open(output_file, 'w') as f:
    #     for ticker in tickers:
    #         f.write(f'{ticker}\n')