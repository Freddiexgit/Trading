import os
from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di
import five_days_and_20days as ema
import filter_by_volume5_and_volume10 as ft
from order_by_ema_60 import order_by_ema


def run_last_day_volume_increase(source_tickers):
    date = datetime.now().strftime("%Y-%m-%d")
    s_str = date
    if source_tickers.find("500") > 0:
        s_str = date + "_top_500"
    else:
        s_str = date + "_median"
    if not os.path.exists(f"resource/{date}/us"):
        # Create the directory
        os.makedirs(f"resource/{date}/us")
    ema.run(f'resource/{source_tickers}', f'resource/{date}/us/us_stock_5days_above_20days_{s_str}.csv')

    order_by_ema(f"resource/{date}/us/us_stock_5days_above_20days_{s_str}.csv", f"resource/{date}/us/us_order_by_ema_60_{s_str}.csv")
    ft.order_by_last_1day_and10day_volume(f"resource/{date}/us/us_order_by_ema_60_{s_str}.csv",
                                          f"resource/{date}/us/us_stock_last_day_vol_{s_str}.csv")
    df_tickers = pd.read_csv(f"resource/{date}/us/us_stock_last_day_vol_{s_str}.csv")
    di.generate_pdf(df_tickers,
                    f"resource/{date}/us/us_stock_Volume_{s_str}_{datetime.now().strftime('%H-%M')}.pdf.pdf", "yes",
                    "day")




