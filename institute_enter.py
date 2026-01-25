import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import  data_downloader as dd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

def increasing_volume_decreasing_range(df):
    if len(df) < 3:
        return False

    last3 = df.tail(3)

    volumes = last3["Volume"].values
    ranges = (last3["High"] - last3["Low"]).values

    volume_increasing = volumes[0] < volumes[1] < volumes[2]
    range_decreasing = ranges[0] > ranges[1] > ranges[2]

    return volume_increasing and range_decreasing


def signal_vol_up_range_tight(df, N=4, lookback=20, threshold=0.75):
    if len(df) < max(lookback, N):
        print("error: not enough data")
        return False

    lastN = df.tail(N)

    volumes = lastN["Volume"].values
    volume_up = all(volumes[i] < volumes[i+1] for i in range(N-1))

    r = df["High"] - df["Low"]
    recent_avg = r.tail(N).mean()
    normal_avg = r.tail(lookback).mean()

    range_tight = recent_avg <= threshold * normal_avg

    return volume_up and range_tight

def institute_enter(file_name):

    df = pd.read_csv(file_name)
    tickers = df['symbol'].dropna().tolist()
    # tickers = [
    #     "AAPL"
    # ]
    result = []
    for ticker in tickers:
        df = dd.get_transaction_df(ticker,period="20d", interval="1d")
        ind = signal_vol_up_range_tight(df)

        if ind:
            result.append(ticker)
            print(ticker)


    s_str = datetime.now().strftime('%Y-%m-%d')
    if len(result)> 0:
        s_str = datetime.now().strftime('%Y-%m-%d')
        loc = f"resource/{s_str}/us/institution_enter.csv"
        df2 = pd.DataFrame(result, columns=['symbol']).drop_duplicates()
        df2.to_csv(f'{loc}', index=False)

if __name__  =="__main__":
    institute_enter("resource/my_watch_list.csv")