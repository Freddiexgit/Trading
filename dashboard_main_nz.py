import os
from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di
import five_days_and_20days as ema
import filter_by_volume5_and_volume10 as ft

s_str = datetime.now().strftime('%Y-%m-%d')


if not os.path.exists(f"resource/{s_str}/nz"):
    # Create the directory
    os.makedirs(f"resource/{s_str}/nz")
ema.run('nzx_tickers.csv', f'resource/{s_str}/nz/nz_stock_5days_above_20days_{s_str}.csv')


ft.sort_by_3day_10day_volume(f"resource/{s_str}/nz/nz_stock_5days_above_20days_{s_str}.csv",
          f"resource/{s_str}/nz/nz_stock_5day_10day_vol_{s_str}.csv")


df_tickers = pd.read_csv(f"resource/{s_str}/nz/nz_stock_5day_10day_vol_{s_str}.csv")

di.generate_pdf(df_tickers,f"resource/{s_str}/nz/nz_stock_indicators_{datetime.now().strftime('%Y-%m-%d-%H-%M')}.pdf","nz")