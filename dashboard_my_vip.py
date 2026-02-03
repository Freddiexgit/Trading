import os
from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di
import five_days_and_20days as ema
import filter_by_volume5_and_volume10 as ft
from find_cross_ema_5_20_90 import find_cross
from order_by_ema_60 import order_by_ema

s_str = datetime.now().strftime('%Y-%m-%d')


from RSI_bottom_finder import rsi_bottom
from institute_enter import institute_enter
import glob

date = datetime.now().strftime("%Y-%m-%d")

def pd_read_pattern(pattern):
    files = glob.glob(pattern)

    df = pd.DataFrame()
    for f in files:
        df = pd.concat([df, pd.read_csv(f)], ignore_index=True)
    return df.reset_index(drop=True)


if not os.path.exists(f"output/{date}/us/myvip"):
    # Create the directory
    os.makedirs(f"output/{date}/us/myvip")


rsi_bottom("resource/myvip/my_vip.csv",   output_file = f"resource/{date}/us/myvip/bottom.csv")
institute_enter("resource/myvip/my_vip.csv",output_file = f"resource/{date}/us/myvip/institute_enter.csv")

df_tickers = pd.read_csv(f"resource/myvip/my_vip.csv")
# find_cross(df_tickers, f"resource/{date}/us/myvip/find_cross_ema_{s_str}")

df_tickers_result = pd_read_pattern(f'resource/{date}/us/myvip/find_cross_ema*')



di.generate_pdf(df_tickers_result, f"resource/{date}/us/myvip/find_cross_ema_{datetime.now().strftime('%Y-%m-%d-%H-%M')}.pdf", "No", "us")


di.generate_pdf(df_tickers,f"resource/{date}/us/myvip/report_{datetime.now().strftime('%Y-%m-%d')}.pdf","No","holding")