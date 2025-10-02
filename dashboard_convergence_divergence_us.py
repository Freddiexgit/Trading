import os
from datetime import datetime

import pandas as pd
import ema_convergence_divergence as ec
import dashboard_list_indicators as di
import  order_by_ema_60 as obe
import five_days_and_20days as ema


def run_converge_diverge(source_tickers="nyse_and_nasdaq_top_500.csv"):
    date = datetime.now().strftime("%Y-%m-%d")
    # source_tickers ="nyse_and_nasdaq_median.csv";
    if source_tickers.find("500") > 0:
        s_str = date + "_top_500"
    else:
        s_str = date+"_median"


    if not os.path.exists(f"resource/{date}/us"):
        # Create the directory
        os.makedirs(f"resource/{date}/us")
    ec.call(source_tickers, f'resource/{date}/us/ema_cv_dv_{s_str}.csv')
    obe.order_by_ema(f'resource/{date}/us/ema_cv_dv_{s_str}.csv', f'resource/{date}/us/order_by_ema_{s_str}.csv', 5)
    df_tickers = pd.read_csv(f"resource/{date}/us/order_by_ema_{s_str}.csv")
    # df_tickers = df_tickers[0:110]
    di.generate_pdf(df_tickers,
                    f"resource/{date}/us/us_stock_cv_dv_indicators_{s_str}_{datetime.now().strftime('%H-%M')}.pdf",
                    "Yes", "us")



