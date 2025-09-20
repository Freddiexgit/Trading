import os
from datetime import datetime

import pandas as pd
import  morning_star as ms
import dashboard_list_indicators as di

s_str = datetime.now().strftime("%Y-%m-%d")


if not os.path.exists(f"resource/{s_str}/us"):
    # Create the directory
    os.makedirs(f"resource/{s_str}/us")
    os.makedirs(f"resource/temp/us/start")
ms.morning_star('nyse_and_nasdaq_top_500.csv', f'resource/{s_str}/us/morning_star_{s_str}.csv')
df_tickers = pd.read_csv(f'resource/{s_str}/us/morning_star_{s_str}.csv')
# df_tickers = df_tickers[0:110]
di.generate_pdf(df_tickers,f"resource/{s_str}/us/us_stock_morning_start_{datetime.now().strftime('%Y-%m-%d-%H-%M')}.pdf","Yes","us")


