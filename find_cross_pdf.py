
import os
from datetime import datetime
import filter_by_volume5_and_volume10 as ft
import dashboard_list_indicators as di

s_str = datetime.now().strftime("%Y-%m-%d")


import glob
import pandas as pd

def pd_read_pattern(pattern):
    files = glob.glob(pattern)

    df = pd.DataFrame()
    for f in files:
        df = pd.concat([df, pd.read_csv(f)], ignore_index=True)
    return df.reset_index(drop=True)


if not os.path.exists(f"resource/{s_str}/us"):
    # Create the directory
    os.makedirs(f"resource/{s_str}/us")
    os.makedirs(f"resource/temp/us/start")
# ms.morning_star('nzx_tickers.csv', f'resource/{s_str}/nz/morning_star_{s_str}.csv')
#
# find_cross_ema_2025-10-03-19-16_5_20.csv
# find_cross_ema_2025-10-03-19-16_5_90.csv
# find_cross_ema_2025-10-03-19-16_20_90

import yfinance as yf
import pandas as pd
import os
from find_cross_ema_5_20_90 import find_cross


# df_tickers = pd.read_csv("resource/us_top_3000.csv")
df_tickers = pd.read_csv("resource/nyse_and_nasdaq_top_500.csv")
find_cross( df_tickers)
df_tickers = pd_read_pattern(f'resource/{s_str}/us/find_cross_ema*')
# df_tickers = df_tickers[0:110]
ft.order(df_tickers, f"resource/{s_str}/us/ema_break_order_by_vol_{s_str}.csv")
df_tickers = pd.read_csv(f"resource/{s_str}/us/ema_break_order_by_vol_{s_str}.csv")
di.generate_pdf(df_tickers, f"resource/{s_str}/us/ema_break_{datetime.now().strftime('%Y-%m-%d-%H-%M')}.pdf", "No", "us")


