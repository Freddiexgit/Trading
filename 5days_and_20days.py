import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
from datetime import datetime
def find_position(symbol="APPL"):

    period = "1mo"   # Last 5 months of data

    # --- Load Stock Data ---
    df = yf.download(symbol, period=period)

    # --- Calculate Moving Averages ---
    df['MA_5'] = df['Close'].rolling(window=5).mean()
    df['MA_20'] = df['Close'].rolling(window=20).mean()

    # --- Identify Crossover Points ---
    df['Signal'] = 0
    # df['Signal'][df['MA_5'] > df['MA_20']] = 1
    df.loc[df['MA_5'] > df['MA_20'], 'Signal'] = 1

    df['Position'] = df['Signal'].diff()
    df.dropna(inplace=True)
    df1 = df['Position'][df['Position'] != 0]
    if len(df1) == 0:
        return 0
    first_non_zero = df1.iloc[-1]
    return  first_non_zero




    # print(df)
    # # --- Plot ---
    # plt.figure(figsize=(14, 7))
    # plt.plot(df['Close'], label='Close Price', alpha=0.4)
    # plt.plot(df['MA_5'], label='5-Day MA', linewidth=2)
    # plt.plot(df['MA_20'], label='20-Day MA', linewidth=2)
    #
    # # Mark Buy/Sell points
    # plt.plot(df[df['Position'] == 1].index, df['MA_5'][df['Position'] == 1], '^', markersize=10, color='g', label='Buy Signal')
    # plt.plot(df[df['Position'] == -1].index, df['MA_5'][df['Position'] == -1], 'v', markersize=10, color='r', label='Sell Signal')
    #
    # plt.title(f"{symbol} - 5-Day vs 20-Day MA")
    # plt.xlabel("Date")
    # plt.ylabel("Price")
    # plt.legend()
    # plt.grid(True)
    # plt.show()

def backtesting():
    # --- Parameters ---
    symbol = "AAPL"
    period = "6mo"
    initial_capital = 10000

    # --- Load Data ---
    df = yf.download(symbol, period=period)
    df['MA_5'] = df['Close'].rolling(window=5).mean()
    df['MA_20'] = df['Close'].rolling(window=20).mean()

    # --- Generate Signals ---
    df['Signal'] = 0
    df.loc[df['MA_5'] > df['MA_20'], 'Signal'] = 1
    df.loc[df['MA_5'] < df['MA_20'], 'Signal'] = -1
    df['Position'] = df['Signal'].diff()

    # --- Backtest Portfolio ---
    df['Holdings'] = 0
    df['Cash'] = initial_capital
    df['Total'] = initial_capital
    in_position = False
    shares_held = 0

    for i in range(1, len(df)):
        price = df['Close'].iloc[i]
        signal = df['Position'].iloc[i]

        if signal == 1 and not in_position:
            # Buy
            shares_held = df['Cash'].iloc[i - 1] // price
            cash_left = df['Cash'].iloc[i - 1] - (shares_held * price)
            in_position = True
        elif signal == -1 and in_position:
            # Sell
            cash_left = shares_held * price
            shares_held = 0
            in_position = False
        else:
            cash_left = df['Cash'].iloc[i - 1]

        holdings = shares_held * price
        total = cash_left + holdings

        df.loc[df.index[i], 'Cash'] = cash_left
        df.loc[df.index[i], 'Holdings'] = holdings
        df.loc[df.index[i], 'Total'] = total

    # --- Plot Portfolio Value ---
    plt.figure(figsize=(14, 6))
    plt.plot(df['Total'], label='Portfolio Value', linewidth=2)
    plt.title(f"{symbol} Strategy Backtest - 5/20 MA Crossover")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value ($)")
    plt.legend()
    plt.grid(True)
    plt.show()

    # --- Summary Stats ---
    final_value = df['Total'].iloc[-1]
    return_pct = (final_value - initial_capital) / initial_capital * 100
    print(f"Final Portfolio Value: ${final_value:.2f}")
    print(f"Return: {return_pct:.2f}%")

    # --- Show Trades ---
    trades = df[df['Position'].isin([1, -1])][['Close', 'Position']]
    print("\nTrade Log:")
    print(trades)

if __name__ == "__main__":
    df = pd.read_csv('resource/nyse_and_nasdaq_top_500.csv')
    tickers = df['symbol'].dropna().tolist()
    stock_5days_above_20days = []
    for ticker in tickers:
        if find_position(ticker) > 0:
            stock_5days_above_20days.append(ticker)
    df2  = pd.DataFrame(stock_5days_above_20days,columns=['symbol'])
    df2.to_csv(f'resource/stock_5days_above_20days_{datetime.now().strftime('%Y-%m-%d')}.csv', index=False)
    # find_position()