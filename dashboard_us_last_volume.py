import os
from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di
import five_days_and_20days as ema
import filter_by_volume5_and_volume10 as ft
from order_by_ema_60 import order_by_ema

s_str = datetime.now().strftime("%Y-%m-%d")


if not os.path.exists(f"resource/{s_str}/us"):
    # Create the directory
    os.makedirs(f"resource/{s_str}/us")
ema.run('resource/nyse_and_nasdaq_top_500.csv', f'resource/{s_str}/us/us_stock_5days_above_20days_{s_str}.csv')

order_by_ema(f"resource/{s_str}/us/us_stock_5days_above_20days_{s_str}.csv", f"resource/{s_str}/us/us_order_by_ema_60_{s_str}.csv")
ft.order_by_last_1day_and10day_volume(f"resource/{s_str}/us/us_order_by_ema_60_{s_str}.csv",
          f"resource/{s_str}/us/us_stock_last_day_vol_{s_str}.csv")



df_tickers = pd.read_csv(f"resource/{s_str}/us/us_stock_last_day_vol_{s_str}.csv")

di.generate_pdf(df_tickers,f"resource/{s_str}/us/us_stock_Volume_{datetime.now().strftime('%Y-%m-%d-%H-%M')}.pdf","yes","day")