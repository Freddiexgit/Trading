import os
from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di
import five_days_and_20days as ema
import filter_by_volume5_and_volume10 as ft


def run_last_day_volume_increase(source_tickers,output_folder =f"resource/{datetime.now().strftime('%Y-%m-%d')}/us" ):

    ft.order_by_last_1day_and10day_volume(f"{output_folder}/ema_cv_dv_ordered_by_20ema_{datetime.now().strftime('%Y-%m-%d')}.csv",
                                          f"{output_folder}/volume_last1day_and10_{datetime.now().strftime('%Y-%m-%d')}.csv")
    df_tickers = pd.read_csv(f"{output_folder}/volume_last1day_and10_{datetime.now().strftime('%Y-%m-%d')}.csv")
    di.generate_pdf(df_tickers,
                    f"{output_folder}/volume_last1day_and10.pdf", "yes",
                    "day")




