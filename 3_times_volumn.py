import yfinance as yf
import pandas as pd
import os


def run_stock_analysis(csv_file_path):
    # 1. Load tickers from your CSV
    if not os.path.exists(csv_file_path):
        print(f"Error: {csv_file_path} not found.")
        return

    # Assumes CSV has a column named 'ticker' or 'Symbol'
    tickers_df = pd.read_csv(csv_file_path)

    tickers = tickers_df["symbol"].unique().tolist()

    all_trades = []

    print(f"Starting backtest for {len(tickers)} tickers...")

    for ticker in tickers:
        try:
            # 2. Get 2 years of daily data
            df = yf.download(ticker, period="2y", interval="1d", progress=False,auto_adjust = True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.empty or len(df) < 11:
                continue

            # 3. Calculate Indicators
            # Vol_Mean_10_Prev: Mean of previous 10 days (excluding current row)
            df['Vol_Mean_10_Prev'] = df['Volume'].rolling(window=10).mean().shift(1)

            # 10-period Exponential Moving Average
            df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()

            # 4. Define Buy Signal
            # Current Volume > 3x Mean of past 10 days AND Price is increasing (Close > Open)
            df['Buy_Signal'] = (df['Volume'] > (df['Vol_Mean_10_Prev'] * 3)) & (df['Close'] > df['Open'])

            # 5. Backtest Logic (1 share per trade)
            in_position = False
            buy_price = 0
            entry_date = None

            # Iterate through the dataframe to simulate trades
            for timestamp, row in df.dropna(subset=['Vol_Mean_10_Prev']).iterrows():
                if not in_position:
                    # Check for Entry
                    if row['Buy_Signal']:
                        in_position = True
                        buy_price = float(row['Close'])
                        entry_date = timestamp
                else:
                    # Check for Exit: Price hits or drops below 10 EMA
                    if float(row['Close']) <= float(row['EMA_10']):
                        exit_price = float(row['Close'])
                        profit = exit_price - buy_price

                        all_trades.append({
                            'Ticker': ticker,
                            'Entry_Date': entry_date.date(),
                            'Exit_Date': timestamp.date(),
                            'Entry_Price': round(buy_price, 2),
                            'Exit_Price': round(exit_price, 2),
                            'Profit': round(profit, 2),
                            'ROI_%': round((profit / buy_price) * 100, 2)
                        })
                        in_position = False

        except Exception as e:
            print(f"Could not process {ticker}: {e}")

    # 6. Reporting
    if all_trades:
        results_df = pd.DataFrame(all_trades)

        print("\n" + "=" * 30)
        print("   BACKTEST PERFORMANCE")
        print("=" * 30)
        print(f"Total Trades:    {len(results_df)}")
        print(f"Winning Trades:  {len(results_df[results_df['Profit'] > 0])}")
        print(f"Total Profit:    ${results_df['Profit'].sum():.2f}")
        print(f"Avg ROI per Trade: {results_df['ROI_%'].mean():.2f}%")
        print("=" * 30)

        # Save results to CSV
        results_df.to_csv('backtest_results.csv', index=False)
        print("\nDetailed trade log saved to 'backtest_results.csv'")
        return results_df
    else:
        print("No trades were triggered with these parameters.")
        return None


if __name__ == "__main__":
    # Ensure you have a 'stocks.csv' file with a 'ticker' column in the same directory
    # Or change the filename below
    FILE_NAME = 'resource/us_middle_3000.csv'
    run_stock_analysis(FILE_NAME)