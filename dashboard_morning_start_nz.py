import os
from datetime import datetime

import pandas as pd
import  morning_star as ms
import dashboard_list_indicators as di

s_str = datetime.now().strftime("%Y-%m-%d")


if not os.path.exists(f"resource/{s_str}/nz"):
    # Create the directory
    os.makedirs(f"resource/{s_str}/nz")
    os.makedirs(f"output/temp/nz/start")
# ms.morning_star('nzx_tickers.csv', f'resource/{s_str}/nz/morning_star_{s_str}.csv')


df_tickers = pd.read_csv(f'resource/{s_str}/nz/morning_star_{s_str}.csv')
# df_tickers = df_tickers[0:110]
di.generate_pdf(df_tickers,f"resource/{s_str}/nz/nz_morning_start_{datetime.now().strftime('%Y-%m-%d-%H-%M')}.pdf","Yes","")


