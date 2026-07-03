import datetime

import yfinance as yf
import pandas as pd
import numpy as np
from numpy.ma.extras import average
from scipy.stats import linregress


import data_downloader as dd

pd.set_option("display.width", 1000)
pd.set_option("display.max_rows", 1000)
pd.set_option("display.max_columns", 1000)

def ema_trend(df, lookback):
    ema = df["Close"].ewm(span=lookback, adjust=False).mean()
    recent = ema.tail(lookback).values

    # % increase over lookback
    raised_pct = (recent[-1] - recent[0]) / recent[0] * 100

    # regression on log EMA (more stable)
    log_vals = np.log(recent)
    x = np.arange(len(log_vals))
    slope, intercept, r, p, se = linregress(x, log_vals)

    return {
        "slope": slope,
        "r2": r*r,
        "raised_pct": raised_pct,
        "avg_log": log_vals.mean()
    }
class EMAResult:
    def __init__(self, average_log_ema, is_rising, r_squared, raised_percentage):
        self.average_log_ema = average_log_ema
        self.is_rising = is_rising
        self.r_squared = r_squared
        self.raised_percentage = raised_percentage

def get_trends(ticker):
    try:
        df = dd.get_transaction_df(
            ticker, period="31mo", interval="1wk",
            is_back_test=False, start_date=None, end_date=None
        ).dropna()

        results = {}
        for lb in [60, 20, 5]:
            if len(df) > lb:
                results[lb] = ema_trend(df, lb)
            else:
                results[lb] = None

        return results

    except Exception:
        return None


# =====================================================
# Main Screener
# =====================================================

def main(input_file=None, output_folder=None, date=None, tickers_to_scan=None):

    if tickers_to_scan is None:
        tickers_to_scan = pd.read_csv(input_file)["symbol"].dropna().tolist()

    rows_60, rows_20, rows_5 = [], [], []

    for ticker in tickers_to_scan:
        res = get_trends(ticker)
        if res is None:
            continue

        if res[60]:
            rows_60.append({"symbol": ticker, **{
                "slope_60": res[60]["slope"],
                "r2_60": res[60]["r2"],
                "raised_60": res[60]["raised_pct"],
                "avg_log_60": res[60]["avg_log"]
            }})

        if res[20]:
            rows_20.append({"symbol": ticker, **{
                "slope_20": res[20]["slope"],
                "r2_20": res[20]["r2"],
                "raised_20": res[20]["raised_pct"],
                "avg_log_20": res[20]["avg_log"]
            }})

        if res[5]:
            rows_5.append({"symbol": ticker, **{
                "slope_5": res[5]["slope"],
                "r2_5": res[5]["r2"],
                "raised_5": res[5]["raised_pct"],
                "avg_log_5": res[5]["avg_log"]
            }})

    df60 = pd.DataFrame(rows_60)
    df20 = pd.DataFrame(rows_20)
    df5 = pd.DataFrame(rows_5)
    if not df60.empty:
        df60 = df60[df60["r2_60"] > 0.7]
        df60 = df60.sort_values(
            ["raised_60", "r2_60", "slope_60"],
            ascending=[False, False, False]
        ).head(200)
        df60.to_csv(f"{output_folder}/result_60_{date}.csv", index=False)
    if not df20.empty:
        df20 = df20[df20["r2_20"] > 0.7]
        df20 = df20.sort_values(
            ["raised_20", "r2_20", "slope_20"],
            ascending=[False, False, False]
        ).head(200)
        df20.to_csv(f"{output_folder}/result_20_{date}.csv", index=False)
    if not df5.empty:
        df5 = df5[df5["r2_5"] > 0.7]
        df5 = df5.sort_values(
            ["raised_5", "r2_5", "slope_5"],
            ascending=[False, False, False]
        ).head(200)
        df5.to_csv(f"{output_folder}/result_5_{date}.csv", index=False)
    if not df5.empty and not df60.empty:
        df5_in_60 = df5[df5["symbol"].isin(df60["symbol"])]
        df5_in_60 = df5_in_60.sort_values("r2_5", ascending=False)
        df5_in_60.to_csv(f"{output_folder}/result_5_in_60_{date}.csv", index=False)
if __name__ == "__main__":
    main(tickers_to_scan = ["STM"])