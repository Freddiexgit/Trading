import yfinance as yf
import pandas as pd
import numpy as np
import traceback

def calculate_avwap(df, anchor_date):
    """Calculates Anchored VWAP starting from a specific date."""
    df_anchored = df.loc[anchor_date:].copy()
    df_anchored['Cum_Vol'] = df_anchored['Volume'].cumsum()
    df_anchored['Cum_Vol_Price'] = (df_anchored['Close'] * df_anchored['Volume']).cumsum()
    return df_anchored['Cum_Vol_Price'] / df_anchored['Cum_Vol']


def scan_for_breakout(tickers):
    results = []

    for ticker in tickers:
        try:
            # Fetch 1 year of daily data
            df = yf.download(ticker, period="1y", progress=False)
            if df.empty or len(df) < 126:
                continue
            df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
            # 1. Calculate EMAs
            df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
            df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

            # 2. Calculate 20-day Volume Average
            df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()

            # 3. Find the Anchor Event (Highest Volume Day in the last 6 months)
            recent_half_year = df.iloc[-126:]
            anchor_date = recent_half_year['Volume'].idxmax()

            # Calculate AVWAP
            df['AVWAP'] = np.nan
            df.update({"AVWAP": calculate_avwap(df, anchor_date)})

            # 4. Extract the latest daily closing data
            latest = df.iloc[-1]

            # --- THE BREAKOUT LOGIC ---

            # Condition A: The Squeeze (EMAs are still relatively tight, < 3% spread)
            max_ema = max(latest['EMA_10'], latest['EMA_21'], latest['EMA_50'])
            min_ema = min(latest['EMA_10'], latest['EMA_21'], latest['EMA_50'])
            ema_spread_pct = (max_ema - min_ema) / latest['Close']
            is_converged = ema_spread_pct < 0.03

            # Condition B: Price Breakout (Closing above the highest EMA and the AVWAP)
            price_breakout = (latest['Close'] > max_ema) and (latest['Close'] > latest['AVWAP'])

            # Condition C: Volume Surge (Today's volume is > 1.5x the 20-day average)
            volume_surge =df['Volume'].rolling(window=3).mean() > (1.3 * latest['Vol_SMA_20'])

            # If all conditions are met, we have a confirmed momentum ignition
            if is_converged and price_breakout and volume_surge:
                results.append({
                    'Ticker': ticker,
                    'Close': round(latest['Close'], 2),
                    'Volume_Surge': f"{round((latest['Volume'] / latest['Vol_SMA_20']), 2)}x Normal",
                    'AVWAP': round(latest['AVWAP'], 2),
                    'EMA_Spread_%': round(ema_spread_pct * 100, 2)
                })

        except Exception as e:
            traceback.print_exc()
            continue

    return pd.DataFrame(results)



def run_backtest(tickers, hold_period=10):
    all_trades = []

    for ticker in tickers:
        try:
            # Fetch 2 years of daily data to give us enough history to test
            df = yf.download(ticker, period="2y", progress=False)
            if df.empty or len(df) < 200:
                continue
            df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
            # 1. Vectorized Indicator Calculations
            df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
            df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()

            # 2. To avoid lookahead bias, we find the highest volume day in the FIRST 6 months
            # and use that as our anchor for the rest of the testing period.
            setup_period = df.iloc[:126]
            anchor_date = setup_period['Volume'].idxmax()

            # Calculate AVWAP from that anchor date forward
            df_test = df.loc[anchor_date:].copy()
            df_test['Cum_Vol'] = df_test['Volume'].cumsum()
            df_test['Cum_Vol_Price'] = (df_test['Close'] * df_test['Volume']).cumsum()
            df_test['AVWAP'] = df_test['Cum_Vol_Price'] / df_test['Cum_Vol']

            # 3. Calculate Signal Conditions for every day in the test period
            # Condition A: Convergence
            df_test['Max_EMA'] = df_test[['EMA_10', 'EMA_21', 'EMA_50']].max(axis=1)
            df_test['Min_EMA'] = df_test[['EMA_10', 'EMA_21', 'EMA_50']].min(axis=1)
            df_test['EMA_Spread_Pct'] = (df_test['Max_EMA'] - df_test['Min_EMA']) / df_test['Close']
            df_test['Is_Converged'] = df_test['EMA_Spread_Pct'] < 0.03

            # Condition B & C: Price Breakout & Volume Surge
            df_test['Price_Breakout'] = (df_test['Close'] > df_test['Max_EMA']) & (df_test['Close'] > df_test['AVWAP'])
            df_test['Volume_Surge'] = df_test['Volume'] > (1.5 * df_test['Vol_SMA_20'])

            # 4. Generate the Buy Signal (Boolean mask)
            df_test['Buy_Signal'] = df_test['Is_Converged'] & df_test['Price_Breakout'] & df_test['Volume_Surge']

            # 5. Extract trades and calculate forward returns
            signal_dates = df_test[df_test['Buy_Signal']].index

            for date in signal_dates:
                # Find the index position of the signal date
                idx = df_test.index.get_loc(date)

                # Ensure we have enough days left in the dataset to calculate the hold period
                if idx + hold_period < len(df_test):
                    entry_price = float(df_test.iloc[idx]['Close'].iloc[0]) if isinstance(df_test.iloc[idx]['Close'],
                                                                                          pd.Series) else float(
                        df_test.iloc[idx]['Close'])
                    exit_price = float(df_test.iloc[idx + hold_period]['Close'].iloc[0]) if isinstance(
                        df_test.iloc[idx + hold_period]['Close'], pd.Series) else float(
                        df_test.iloc[idx + hold_period]['Close'])

                    pct_return = ((exit_price - entry_price) / entry_price) * 100

                    all_trades.append({
                        'Ticker': ticker,
                        'Entry_Date': date.strftime('%Y-%m-%d'),
                        'Entry_Price': round(entry_price, 2),
                        'Exit_Price': round(exit_price, 2),
                        'Return_%': round(pct_return, 2)
                    })

        except Exception as e:
            continue

    return pd.DataFrame(all_trades)





if __name__ == "__main__":
    # --- Run the Scanner ---
    watchlist = ["ENLT"]

    print("Scanning for AVWAP/EMA convergence breakouts...")
    breakout_candidates = scan_for_breakout(watchlist)

    if not breakout_candidates.empty:
        print("\nConfirmed Breakout Setups Found:")
        print(breakout_candidates.to_string(index=False))
    else:
        print("\nNo breakouts found today in the current watchlist.")

    # --- Run the Backtest ---


    # print("Running historical backtest (10-day holding period)...")
    # trades_df = run_backtest(watchlist, hold_period=10)
    #
    # if not trades_df.empty:
    #     print("\nHistorical Trades Generated:")
    #     print(trades_df.to_string(index=False))
    #
    #     # Calculate System Metrics
    #     win_rate = (len(trades_df[trades_df['Return_%'] > 0]) / len(trades_df)) * 100
    #     avg_return = trades_df['Return_%'].mean()
    #
    #     print("\n--- Strategy Performance Metrics ---")
    #     print(f"Total Trades: {len(trades_df)}")
    #     print(f"Win Rate: {round(win_rate, 2)}%")
    #     print(f"Average Return per Trade (10 days): {round(avg_return, 2)}%")
    # else:
    #     print("\nNo historical signals found for the given parameters.")