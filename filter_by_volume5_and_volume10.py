import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import data_downloader as data
# Download stock data

def sort_by_3day_10day_volume(input_file,output_file):

    df_tickers = pd.read_csv(input_file)
    sorted_dict = cal(df_tickers)


    with open(output_file, 'w') as f:
        f.write('symbol\n')
        for key, value in sorted_dict.items():
            f.write(f'{key}\n')



def cal(df_tickers):
    ticker_and_vol = {}
    for index, row in df_tickers.iterrows():
        ticker = row['symbol']
        df = data.get_transaction_df(ticker, period="20d")
        df["Resistance"] = df["Close"].rolling(window=20).max().shift(1)
        df["AvgVolume"] = df["Volume"].rolling(window=20).mean()
        breakout = (df["Close"].iloc[-1] > df["Resistance"].iloc[-1]) & \
                   (df["Volume"].iloc[-1] > 1.5 * df["AvgVolume"].iloc[-1])
        if breakout:
            # signals["Breakout_Volume"] = True
            ticker_and_vol[ticker] = 1
        # df["VolMA3"] = df["Volume"].rolling(3).mean()
        # df["VolMA10"] = df["Volume"].rolling(10).mean()
        # df = df.iloc[-1:]
        # if df["VolMA3"].iloc[-1] > df["VolMA10"].iloc[-1]:
        #     # ticker_and_vol[ticker] = (df["VolMA3"].iloc[-1] - df["VolMA10"].iloc[-1]) / df["VolMA10"].iloc[-1]
        #     ticker_and_vol[ticker] = df["VolMA3"].iloc[-1] - df["VolMA10"].iloc[-1]
        # sorted_dict = dict(sorted(ticker_and_vol.items(), key=lambda item: item[1], reverse=True))
    return ticker_and_vol

def order_by_last_1day_and10day_volume(input_file,output_file):
    df_tickers = pd.read_csv(input_file)
    order(df_tickers,output_file)

def order(df_tickers,output_file):
    ticker_and_vol = {}
    for index, row in df_tickers.iterrows():
        ticker = row['symbol']
        df = data.get_transaction_df(ticker, period="20d")
        if len(df)<10: continue
        df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
        df["VolMA10"] = df["Volume"].rolling(10).mean()
        df = df.iloc[-1:]
        if df["Volume"].iloc[-1] > df["VolMA10"].iloc[-1] * 1.5 and df["Close"].iloc[-1]> df["Open"].iloc[-1]:
            ticker_and_vol[ticker] = (df["Volume"].iloc[-1] - df["VolMA10"].iloc[-1]) / df["VolMA10"].iloc[-1]

    sorted_dict = dict(sorted(ticker_and_vol.items(), key=lambda item: item[1], reverse=True))

    with open(output_file, 'w') as f:
        f.write('symbol\n')
        for key, value in sorted_dict.items():
            f.write(f'{key}\n')

if __name__ == "__main__":
    # df = pd.DataFrame({"symbol": ["OFSSH"]})
    # cal(df)
    df = data.get_transaction_df("OFSSH", period="20d")
    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    print(df)
    df["VolMA10"] = df["Volume"].rolling(10).mean()
    df = df.iloc[-1:]
    df.drop_level(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    print(df)
    if df["Volume"].iloc[-1] > df["VolMA10"].iloc[-1] * 1.3 and df["close"].iloc[-1]> df["open"].iloc[-1]:
        print( (df["Volume"].iloc[-1] - df["VolMA10"].iloc[-1]) / df["VolMA10"].iloc[-1])
