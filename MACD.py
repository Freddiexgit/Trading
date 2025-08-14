from datetime import datetime

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
import numpy as np


def MACD_buying_point(ticker='RBLX', period='4mo'):
    """
    Calculate MACD and identify buying points for a given stock ticker.

    Parameters:
    ticker (str): Stock symbol to analyze.
    period (str): Period for historical data (e.g., '4mo' for 4 months).

    Returns:
    DataFrame: DataFrame with MACD, Signal Line, Histogram, and Buy/Sell signals.
    """
    # Step 1: Download historical stock data
    df = yf.download(ticker, period=period)

    # Step 2: Calculate EMAs
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()

    # Step 3: Calculate MACD and Signal Line
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()

    # Step 4: Add to DataFrame
    df['ema_12'] = ema_12
    df['ema_26'] = ema_26
    df['MACD'] = macd
    df['Signal'] = signal
    df['Histogram'] = df['MACD'] - df['Signal']

    print(df)
    # Step 5: Plot
    plt.figure(figsize=(12, 6))
    # plt.plot(df.index, df['ema_12'], label='12-day', color='green')
    # plt.plot(df.index, df['ema_26'], label='26-day', color='darkgreen')
    plt.plot(df.index, df['MACD'], label='MACD', color='blue')
    plt.plot(df.index, df['Signal'], label='Signal Line', color='red')
    plt.bar(df.index, df['Histogram'], label='Histogram', color='gray')
    df['Turning Point'] = ((df['Histogram'] < 0) & (df['Histogram'].shift(-1) > 0)).astype(int)
    df['blow_0'] = np.where(df['Turning Point'] > 0, 1, 0)
    plt.plot(df['MACD'][df['blow_0'] == 1].index, df['MACD'][df['blow_0'] == 1], '^', markersize=10, color='g',
             label='Buy Signal')

    plt.title(f'MACD Indicator for {ticker}')
    plt.legend()
    plt.grid(True)
    plt.show()


    # # Identify turning points and buy/sell signals
    # df['Turning Point'] = ((df['Histogram'] < 0) & (df['Histogram'].shift(-1) > 0)).astype(int)
    # df['blow_0'] = np.where(df['MACD'] > 0, 1, 0)
    # df1 = df['blow_0'][df['blow_0'] != 0]
    # if len(df1) == 0:
    #     return 0
    # first_non_zero = df1.iloc[-1]
    # return  first_non_zero







if __name__ == "__main__":
    # df = pd.read_csv('resource/stock_5days_above_20days_2025-08-12.csv')
    # tickers = df['symbol'].dropna().tolist()
    # MACD_buy = []
    # for ticker in tickers:
    #     if MACD_buying_point(ticker) > 0:
    #         MACD_buy.append(ticker)
    # df2  = pd.DataFrame(MACD_buy,columns=["symbol"])
    # df2.to_csv(f'resource/macd_buy_sing_{datetime.now().strftime('%Y-%m-%d')}.csv', index=False)
    MACD_buying_point()