import traceback

from dashboard_find_common_ema_volumn import run_volume_and_cvg_dvg
from dashboard_us_last_volume import run_last_day_volume_increase
import os
from datetime import datetime

import dashboard_list_indicators as di

from find_cross_ema_5_20_90 import find_cross

import pandas as pd
import glob
import  data_downloader as data

import last_ema_weekly_angle as  lew
#

data.to_be_removed_tickers
#

now = datetime.now()
# if now.weekday()== 6 or now.weekday()== 0:  # Saturday or Sunday US Time
date = f"{now.strftime("%Y-%m-%d")}_weekend"
data.global_period = "2y"
data.global_interval ="1wk"
ticker_file_name = "us_top_5000"
# else:
# date = now.strftime("%Y-%m-%d")
# data.global_period = "12mo"
# data.global_interval = "1d"
# ticker_file_name = "my_watch_list"
# data.global_period = "2y"
# data.global_interval ="1wk"
# ticker_file_name = "nzx_tickers"
# ticker_file_name = "my_vip"
# ticker_file_name = "my_watch_list"
# ticker_file_name = "nyse_and_nasdaq_top_500"
# ticker_file_name ="leading_stocks_by_industry"
# ticker_file_name = "us_top_5000"
# ticker_file_name = "vip_industries"


# ticker_file_name = "my_owned"
ticker_file_name_full = f"{ticker_file_name}.csv"
output_folder = f"output/{date}/us_{data.global_interval}/{ticker_file_name}"
if not os.path.exists(f"{output_folder}"):
    # Create the directory
    os.makedirs(f"{output_folder}")

try:
    lew.main(input_file=f"resource/{ticker_file_name_full}", output_folder = f"{output_folder}",date = date)
    df_tickers_result = pd.read_csv(f"{output_folder}/result_5_{date}.csv")
    di.generate_pdf(df_tickers_result, f"{output_folder}/result_5.pdf", "No", "us")
    df_tickers_result = pd.read_csv(f"{output_folder}/result_20_{date}.csv")
    di.generate_pdf(df_tickers_result, f"{output_folder}/result_20.pdf", "No", "us")
    df_tickers_result = pd.read_csv(f"{output_folder}/result_60_{date}.csv")
    di.generate_pdf(df_tickers_result, f"{output_folder}/result_60.pdf", "No", "us")
    df_tickers_result = pd.read_csv(f"{output_folder}/result_5_in_60_{date}.csv")
    di.generate_pdf(df_tickers_result, f"{output_folder}/result_5_in_60.pdf", "No", "us")
except Exception  as e:
    print("building-up run failed:", e)
    traceback.print_exc()

# try:
#     print(f"running run_last_day_volume_increase....{datetime.now()}")
#     run_last_day_volume_increase(f"{ticker_file_name_full}",output_folder = f"{output_folder}" )
# except Exception as e:
#     print("run_last_day_volume_increase error:", e)
# try:
#     print(f"running run_volume_and_cvg_dvg....{datetime.now()}")
#     run_volume_and_cvg_dvg(output_folder = f"{output_folder}" )
# except Exception as e:
#     print("run_volume_and_cvg_dvg error:", e)
#
#
#
# def pd_read_pattern(pattern):
#     files = glob.glob(pattern)
#
#     df = pd.DataFrame()
#     for f in files:
#         df = pd.concat([df, pd.read_csv(f)], ignore_index=True)
#     return df.reset_index(drop=True)
#
#
#
# try:
#     print(f"running find_cross....{datetime.now()}")
#     df_tickers = pd.read_csv(f"resource/{ticker_file_name_full}")
#     find_cross(df_tickers,output_folder)
#     df_tickers_result = pd_read_pattern(f'{output_folder}/find_cross_ema*')
#     df_tickers_result = df_tickers_result.drop_duplicates()
#     di.generate_pdf(df_tickers_result, f"{output_folder}/find_cross_ema.pdf", "No", "us")
# except Exception as e:
#     print("find_cross error:", e)
#
# if len(data.to_be_removed_tickers) > 0 :
#     print(f"tickers to be removed: {data.to_be_removed_tickers}")
#     with open("resource/to_be_removed_tickers.txt", "w") as f:
#         f.write("symbol\n")
#         for ticker in data.to_be_removed_tickers:
#             f.write(f"{ticker}\n")
