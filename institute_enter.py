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

# df = pd.read_csv(f'resource/nyse_and_nasdaq_top_500.csv')
# tickers = df['symbol'].dropna().tolist()
tickers = [
    "AAPL"
]
result = []
for ticker in tickers:
    df = dd.get_transaction_df(ticker,period="3d", interval="1d")
    ind = increasing_volume_decreasing_range(df)
    print(df)
    if ind:
        result.append(ticker)
        print(ticker)


s_str = datetime.now().strftime('%Y-%m-%d')
if len(result)> 0:
    s_str = datetime.now().strftime('%Y-%m-%d')
    loc = f"resource/{s_str}/us/insti_enter.csv"
    df2 = pd.DataFrame(result, columns=['symbol']).drop_duplicates()
    df2.to_csv(f'{loc}', index=False)