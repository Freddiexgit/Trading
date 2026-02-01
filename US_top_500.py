from sys import exception

from dashboard_convergence_divergence_us import run_converge_diverge
from dashboard_find_common_ema_volumn import run_volume_and_cvg_dvg
from dashboard_us_last_volume import run_last_day_volume_increase
import os
from datetime import datetime
import dashboard_list_indicators as di

from RSI_bottom_finder import rsi_bottom
from find_cross_ema_5_20_90 import find_cross
from institute_enter import institute_enter
from RSI_Momentum_Combo_Strategy_copilot import run_momentum

date = datetime.now().strftime("%Y-%m-%d")

# ticker_file_name = "my_vip"
ticker_file_name = "my_watch_list"
# ticker_file_name = "nyse_and_nasdaq_top_500"
# ticker_file_name = "us_top_3000"
ticker_file_name_full = f"{ticker_file_name}.csv"
output_folder = f"output/{date}/us/{ticker_file_name}"
if not os.path.exists(f"{output_folder}"):
    # Create the directory
    os.makedirs(f"{output_folder}")

try:
    rsi_bottom(f"resource/{ticker_file_name_full}", output_file = f"{output_folder}/bottom.csv")
except Exception  as  e:
    print("rsi_bottom error:", e)
try:
    institute_enter(f"resource/{ticker_file_name_full}",output_file = f"{output_folder}/institute_enter.csv")
except Exception as e:
    print("institute_enter error:", e)
try:
    run_momentum(f"resource/{ticker_file_name_full}",output_file = f"{output_folder}/momentum.csv" )
except Exception as e:
    print("run_momentum error:", e)
try:
    run_converge_diverge(f"{ticker_file_name_full}",output_folder = f"{output_folder}" )
except Exception  as e:
    print("run_converge_diverge error:", e)
try:
    run_last_day_volume_increase(f"{ticker_file_name_full}",output_folder = f"{output_folder}" )
except Exception as e:
    print("run_momentum error:", e)
try:
    run_volume_and_cvg_dvg(output_folder = f"{output_folder}" )
except Exception as e:
    print("run_volume_and_cvg_dvg error:", e)

import pandas as pd
import glob
def pd_read_pattern(pattern):
    files = glob.glob(pattern)

    df = pd.DataFrame()
    for f in files:
        df = pd.concat([df, pd.read_csv(f)], ignore_index=True)
    return df.reset_index(drop=True)

df_tickers = pd.read_csv(f"resource/{ticker_file_name_full}")

try:
    find_cross(df_tickers,output_folder)
    df_tickers_result = pd_read_pattern(f'{output_folder}/find_cross_ema*')
    df_tickers_result = df_tickers_result.drop_duplicates()
    di.generate_pdf(df_tickers_result, f"{output_folder}/find_cross_ema_{datetime.now().strftime('%Y-%m-%d-%H-%M')}.pdf", "No", "us")
except Exception as e:
    print("find_cross error:", e)