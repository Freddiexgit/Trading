import yfinance as yf
import pandas as pd
import numpy as np
from numpy.ma.extras import average
from scipy.stats import linregress

import data_downloader as dd

pd.set_option("display.width", 1000)
pd.set_option("display.max_rows", 1000)
pd.set_option("display.max_columns", 1000)

def check_smooth_ema_uptrend(ticker, lookback_periods=60, min_r2=0.90):
    """
    Checks if the EMA20 is rising smoothly using Linear Regression.

    Parameters:
    ticker (str): The stock symbol.
    lookback_periods (int): How many recent periods to measure for smoothness.
    min_r2 (float): The minimum R-squared value (0.0 to 1.0). 0.90+ is very smooth.
    """
    try:
        # Fetch data (using daily here, but you can change interval="1wk")
        df = dd.get_transaction_df(ticker, period="2y", interval="1wk", is_back_test=False,start_date = None, end_date = None)
        df = df.dropna()

        if len(df) < 20 + lookback_periods:
            return None, "Not enough data"

        # 1. Calculate the EMA20
        df['EMA60'] = df['Close'].ewm(span=60, adjust=False).mean()

        # 2. Isolate the most recent EMA values for our lookback window
        recent_ema = df['EMA60'].tail(lookback_periods).values
        df["raised_percentage"] = (df["EMA60"] - df["EMA60"].shift(lookback_periods)) / df["EMA60"].shift(lookback_periods) * 100
        raised_percentage = df["raised_percentage"].iloc[-1]

        # 3. Create an X-axis array (representing time: 0, 1, 2, 3...)
        x = np.arange(lookback_periods)

        # 4. Perform Linear Regression
        slope, intercept, r_value, p_value, std_err = linregress(x, recent_ema)
        log_ema = np.log(recent_ema)
        average_log_ema = average(log_ema)
        # Calculate R-squared (r_value squared)
        r_squared = r_value ** 2

        # 5. Check our conditions: Must be pointing UP and be SMOOTH
        is_rising = slope > 0
        is_smooth = r_squared >= min_r2

        passed = is_rising and is_smooth
        return passed, average_log_ema, r_squared,raised_percentage

    except Exception as e:
        return None, 0, 0,0


# =====================================================
# Main Screener
# =====================================================

def main(input_file, output_file):


    # We want to look at the last 15 days, and require a 90% smoothness rating
    LOOKBACK = 60
    MIN_R2_SCORE = 0.80

    passed_tickers = []
    # tickers_to_scan = pd.read_csv(input_file)["symbol"].dropna().tolist()
    tickers_to_scan = [ "SNDK"]
    for ticker in tickers_to_scan:
        try:
            passed, log_average_slope, r2,raised_percentage = check_smooth_ema_uptrend(
                ticker,
                lookback_periods=LOOKBACK,
                min_r2=MIN_R2_SCORE
            )
        except Exception  as e:
            print(f"Error processing {ticker}: {e}")
            continue
        print(f"{ticker} - Passed: {passed}, log_average_slope: {log_average_slope}, R^2: {r2:.4f}, Raised %: {raised_percentage:.2f}%")
        if passed :
            result_dict =  { "symbol" : ticker, "log_average_slope": log_average_slope, "r_squared": r2,"raised_percentage": raised_percentage }
            passed_tickers.append(result_dict)
    results_df = pd.DataFrame(passed_tickers)

    results_df.sort_values(["log_average_slope","raised_percentage", "r_squared"],
    ascending=[False,False, False], # False for raised_percentage, True for another_column
    inplace=True)
    print(results_df)
    # results_df.to_csv(output_file, index=False)

if __name__ == "__main__":
    main(input_file="resource/my_watch_list.csv", output_file="last_200_day_angle.csv")