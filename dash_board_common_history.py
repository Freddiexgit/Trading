import os
from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di
import five_days_and_20days as ema
import filter_by_volume5_and_volume10 as ft
from order_by_ema_60 import order_by_ema

s_str = datetime.now().strftime('%Y-%m-%d')


list = [
"cv_dv_volume_stocks_2025-10-25_median.csv",
"cv_dv_volume_stocks_2025-10-25_top_500.csv"
]
for name in list:
    if os.path.exists(f"resource/cv_dv_volume_stocks/{name}"):
        df_tickers = pd.read_csv(f"resource/cv_dv_volume_stocks/{name}")
        di.generate_pdf(df_tickers, f"resource/cv_dv_volume_stocks/report_{name}.pdf", "No", "holding")



# df_tickers = pd.read_csv(f"resource/common_cross/myholding.csv")
#
# di.generate_pdf(df_tickers,f"resource/myholding/myholding_report_{datetime.now().strftime('%Y-%m-%d')}.pdf","No","holding")