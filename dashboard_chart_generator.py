import os
from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di
import five_days_and_20days as ema
import filter_by_volume5_and_volume10 as ft
from order_by_ema_60 import order_by_ema

s_str = datetime.now().strftime('%Y-%m-%d')

# df_tickers_inst = pd.read_csv(f"{output_folder}/institute_enter.csv")
# di.generate_pdf(df_tickers_inst, f"{output_folder}/institute_enter{date}.pdf", "No", "us")

# loc = f"resource/{s_str}/us/bottom"
loc = "output/2026-06-19/us_1d/us_top_5000/find_building_up_gpt_2026-06-19_2"
df_tickers = pd.read_csv(f"{loc}.csv").head(100)
df_tickers.drop_duplicates()
di.generate_pdf(df_tickers,f"output/2026-06-19/us_1d/us_top_5000/find_building_up_gpt_2_2026-06-19.pdf","No","holding")