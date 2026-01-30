import os
from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di
import five_days_and_20days as ema
import filter_by_volume5_and_volume10 as ft
from order_by_ema_60 import order_by_ema


def run_last_day_volume_increase(source_tickers,output_folder =f"resource/{datetime.now().strftime('%Y-%m-%d')}/us" ):
    date = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(f"{output_folder}"):
        # Create the directory
        os.makedirs(f"{output_folder}")
    ema.run(f'resource/{source_tickers}', f'{output_folder}/us_stock_5days_above_20days_{date}.csv')

    order_by_ema(f"{output_folder}/us_stock_5days_above_20days_{date}.csv", f"{output_folder}/us_order_by_ema_60_{date}.csv")
    ft.order_by_last_1day_and10day_volume(f"{output_folder}/us_order_by_ema_60_{date}.csv",
                                          f"{output_folder}/us_stock_last_day_vol_{date}.csv")
    df_tickers = pd.read_csv(f"{output_folder}/us_stock_last_day_vol_{date}.csv")
    di.generate_pdf(df_tickers,
                    f"{output_folder}/us_stock_Volume_{date}_{datetime.now().strftime('%H-%M')}.pdf", "yes",
                    "day")




