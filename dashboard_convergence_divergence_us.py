import os
from datetime import datetime

import pandas as pd
import ema_convergence_divergence as ec
import dashboard_list_indicators as di
import  order_by_ema_60 as obe
import five_days_and_20days as ema


def run_converge_diverge(source_tickers="nyse_and_nasdaq_top_500.csv",output_folder =f"resource/{datetime.now().strftime("%Y-%m-%d")}/us" ):
    date = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(f"{output_folder}"):
        # Create the directory
        os.makedirs(f"{output_folder}")
    ec.call(source_tickers, f'{output_folder}/ema_cv_dv_{date}.csv')
    obe.order_by_ema(f'{output_folder}/ema_cv_dv_{date}.csv', f'{output_folder}/order_by_ema_{date}.csv', 5)
    df_tickers = pd.read_csv(f"{output_folder}/order_by_ema_{date}.csv")
    # df_tickers = df_tickers[0:110]
    di.generate_pdf(df_tickers,
                    f"{output_folder}/us_stock_cv_dv_indicators_{date}_{datetime.now().strftime('%H-%M')}.pdf",
                    "Yes", "us")



