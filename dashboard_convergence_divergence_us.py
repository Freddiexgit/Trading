import os
from datetime import datetime

import pandas as pd
import ema_convergence_divergence as ec
import dashboard_list_indicators as di
import  order_by_ema_60 as obe
import five_days_and_20days as ema


def run_converge_diverge(source_tickers="my_watch_list.csv",output_folder =f"resource/{datetime.now().strftime("%Y-%m-%d")}/us" ):
    date = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(f"{output_folder}"):
        # Create the directory
        os.makedirs(f"{output_folder}")
    ec.call(source_tickers, f'{output_folder}/ema_cv_dv.csv')
    obe.order_by_ema(f'{output_folder}/ema_cv_dv.csv', f'{output_folder}/ema_cv_dv_ordered_by_20ema.csv', 5)
    df_tickers = pd.read_csv(f"{output_folder}/ema_cv_dv_ordered_by_20ema.csv")
    # df_tickers = df_tickers[0:110]
    di.generate_pdf(df_tickers,
                    f"{output_folder}/ema_cv_dv_indicator.pdf",
                    "No", "us")

if __name__ == "__main__":
    run_converge_diverge()


