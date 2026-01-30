import pandas as pd
import numpy as np
import data_downloader as dd
from datetime import datetime
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
# ---------------------------
# RSI Calculation (Wilder)
# ---------------------------
def rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def rsi_bottom(file_name,output_file = f"resource/{datetime.now().strftime('%Y-%m-%d')}/us/bottom.csv"):
    # ---------------------------
    # Example price data
    # ---------------------------
    # df must have column: 'Close'
    # df = pd.read_csv(f'resource/my_watch_list.csv')
    df = pd.read_csv(file_name)
    tickers = df['symbol'].dropna().tolist()
    # tickers = [
    #     "AAPL"
    # ]
    result = []
    for ticker in tickers:
        df1 = dd.get_transaction_df(ticker,period="10mo", interval="4h")


        if ~len(df1) > 120:
           continue

        df = df1.copy()



        # Indicator calculations
        # ---------------------------
        df["MA120"] = df["Close"].rolling(120).mean()
        df["RSI14"] = rsi(df["Close"], 14)
        df["RSI6"] = rsi(df["Close"], 6)

        # ---------------------------
        # RSI(2) cross up detection
        # ---------------------------
        df["RSI6_prev"] = df["RSI6"].shift(1)

        # rsi2_cross_up = (df["RSI6_prev"] < 20) & (df["RSI6"] >= 20)
        rsi2_cross_up = (df["RSI6_prev"] < df["RSI6"])
        df = df.iloc[-3:]

        # ---------------------------
        # Buy Signal
        # ---------------------------
        df["BUY_SIGNAL"] = (
            (df["Close"] > df["MA120"]) &
            # (df["RSI14"] > 40) &
            (df["RSI6"] < 30) &
            rsi2_cross_up
        )

        # ---------------------------
        # View signals
        # ---------------------------



        signals = df[df["BUY_SIGNAL"]]
        if len(signals) > 0:
            print(f"{ticker}")
            result.append(ticker)
            # print(signals[["Close","MA200","RSI14","RSI6"]])


    if len(result) > 0:
        df2 = pd.DataFrame(result, columns=['symbol']).drop_duplicates()
        df2.to_csv(f'{output_file}', index=False)

if __name__  =="__main__":
    rsi_bottom("resource/my_watch_list.csv")