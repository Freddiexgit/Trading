from datetime import datetime
import yfinance as yf
import os
import pandas as pd
import data_downloader as data
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

date = datetime.now().strftime("%Y-%m-%d")

if not os.path.exists(f"output/{date}/us"):
    # Create the directory
    os.makedirs(f"output/{date}/us")

def get_data(df , ticker):
    df = df.copy()
     # Compute EMAs
    df["EMA5"] = df["Close"].ewm(span=5, adjust=False).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA90"] = df["Close"].ewm(span=90, adjust=False).mean()
    df= df.iloc[-4:]
    df["5_cross_20"] = df["EMA5"] >= df["EMA20"]
    df["5_cross_90"] = df["EMA5"] >= df["EMA90"]
    df["20_cross_90"] = df["EMA20"] >= df["EMA90"]
    five_cross_20 = []
    twenty_cross_90 = []
    five_cross_90= []
    # print(ticker)
    # print(df)
    if len(df) < 2: return five_cross_20, five_cross_90, twenty_cross_90
    if((df['5_cross_20'] == True) & (df['5_cross_20'].shift(1) == False)).any():
        five_cross_20.append(ticker)
    if ((df['5_cross_90'] == True) & (df['5_cross_90'].shift(1) == False)).any():
        five_cross_90.append(ticker)
    if ((df['20_cross_90'] == True) & (df['20_cross_90'].shift(1) == False)).any():
        twenty_cross_90.append(ticker)
    return five_cross_20, five_cross_90, twenty_cross_90

def find_cross(df_tickers,output_folder = f"resource/{date}/us",is_back_test=False,start_date=None,end_date=None, interval = None):
    five_cross_20 = []
    twenty_cross_90 = []
    five_cross_90= []
    for index, row in df_tickers.iterrows():
        ticker = row['symbol']
        try:
            df1 = data.get_transaction_df(ticker, interval=interval, is_back_test=is_back_test, start_date=start_date, end_date=end_date)
            df = df1.copy()
        except Exception as e:
            print(f"Error downloading data for {ticker}: {e}")
            continue
        five_cross_20_1, five_cross_90_1, twenty_cross_90_1  = get_data(df, ticker)
        five_cross_20.extend(five_cross_20_1)
        five_cross_90.extend(five_cross_90_1)
        twenty_cross_90.extend(twenty_cross_90_1)

    if len(five_cross_20) > 0:
        df2 = pd.DataFrame(five_cross_20, columns=['symbol']).drop_duplicates()
        df2.to_csv(f'{output_folder}/find_cross_ema_{date}_5_20.csv', index=False)
    if len(five_cross_90) > 0:
        df2 = pd.DataFrame(five_cross_90, columns=['symbol']).drop_duplicates()
        df2.to_csv(f'{output_folder}/find_cross_ema_{date}_5_90.csv', index=False)
    if len(twenty_cross_90) > 0:
        df2 = pd.DataFrame(twenty_cross_90, columns=['symbol']).drop_duplicates()
        df2.to_csv(f'{output_folder}/find_cross_ema_{date}_20_90.csv', index=False)
    # print(five_cross_20)
    # print(five_cross_90)
    # print(twenty_cross_90)

if __name__  =="__main__":
    # df_tickers = pd.read_csv("resource/nyse_and_nasdaq_top_500.csv")
    # for index, row in df_tickers.iterrows():
    #     ticker = row['symbol']
    #     try:
    #         df = yf.download(ticker, period="4mo", interval="1d")
    #     except Exception as e:
    #         print(f"Error downloading data for {ticker}: {e}")
    #         continue
    #     df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    #     find_cross(df, ticker)
    #
    #     EMP
    #     PRH  21.607938  21.498378  22.171827
    tickers = ["ATEX"]
    find_cross(pd.DataFrame(tickers, columns=['symbol']),interval = "1wk", is_back_test=True,start_date="2025-10-01",end_date="2026-1-5")