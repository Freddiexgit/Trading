import os
from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di
import five_days_and_20days as ema
import filter_by_volume5_and_volume10 as ft
from order_by_ema_60 import order_by_ema

s_str = datetime.now().strftime('%Y-%m-%d')





# loc = f"resource/{s_str}/us/bottom"
loc = f"resource/{s_str}/us/insti_enter"
df_tickers = pd.read_csv(f"{loc}.csv")
df_tickers.drop_duplicates()
di.generate_pdf(df_tickers,f"{loc}_{datetime.now().strftime('%Y-%m-%d')}.pdf","No","holding")