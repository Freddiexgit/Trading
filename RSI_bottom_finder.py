import pandas as pd
import numpy as np
import data_downloader as dd
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

def rsi_bottom(file_name):
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
        df = dd.get_transaction_df(ticker,period="10mo", interval="1d")


        if ~len(df) > 0:
           continue


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
        # print(df)
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

        from datetime import datetime

        signals = df[df["BUY_SIGNAL"]]
        if len(signals) > 0:
            print(f"{ticker}")
            result.append(ticker)
            # print(signals[["Close","MA200","RSI14","RSI6"]])

    s_str = datetime.now().strftime('%Y-%m-%d')
    if len(result) > 0:
        s_str = datetime.now().strftime('%Y-%m-%d')
        loc = f"resource/{s_str}/us/bottom.csv"
        df2 = pd.DataFrame(result, columns=['symbol']).drop_duplicates()
        df2.to_csv(f'{loc}', index=False)

if __name__  =="__main__":
    rsi_bottom("resource/my_watch_list.csv")