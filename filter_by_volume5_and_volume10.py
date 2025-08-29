import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

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
        df = yf.download(ticker, period="20d")

        df["VolMA3"] = df["Volume"].rolling(3).mean()
        df["VolMA10"] = df["Volume"].rolling(10).mean()
        df = df.iloc[-1:]
        if df["VolMA3"].iloc[-1] > df["VolMA10"].iloc[-1]:
            # ticker_and_vol[ticker] = (df["VolMA3"].iloc[-1] - df["VolMA10"].iloc[-1]) / df["VolMA10"].iloc[-1]
            ticker_and_vol[ticker] = df["VolMA3"].iloc[-1] - df["VolMA10"].iloc[-1]
        sorted_dict = dict(sorted(ticker_and_vol.items(), key=lambda item: item[1], reverse=True))
    return sorted_dict


if __name__ == "__main__":
    df = pd.DataFrame({"symbol": ["OFSSH"]})
    cal(df)