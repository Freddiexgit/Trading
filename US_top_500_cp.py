
from dashboard_convergence_divergence_us import run_converge_diverge
from dashboard_find_common_ema_volumn import run_volume_and_cvg_dvg
from dashboard_us_last_volume import run_last_day_volume_increase
import os
from datetime import datetime
import dashboard_list_indicators as di
import  ask_bid
from RSI_bottom_finder import rsi_bottom
from find_cross_ema_5_20_90 import find_cross
from institute_enter import institute_enter
from analytics import quick_fundamental_analysis as qfa
import pandas as pd
import glob
import  data_downloader as data
import traceback
import AI_buying_point as ai

data.global_period = "12mo"
data.global_interval ="1d"

date = datetime.now().strftime("%Y-%m-%d")
# ticker_file_name = "nzx_tickers"
ticker_file_name = "my_vip"
# ticker_file_name = "my_watch_list"
# ticker_file_name = "nyse_and_nasdaq_top_500"
# ticker_file_name = "us_top_3000"
# ticker_file_name = "my_owned"
ticker_file_name_full = f"{ticker_file_name}.csv"
output_folder = f"output/{date}/us/{ticker_file_name}"
if not os.path.exists(f"{output_folder}"):
    # Create the directory
    os.makedirs(f"{output_folder}")

df_tickers_fqa = pd.read_csv(f"{output_folder}/quick_fundamental_analysis.csv")
df_tickers_fqa.columns = df_tickers_fqa.columns.str.lower()
di.generate_pdf(df_tickers_fqa[['symbol']], f"{output_folder}/quick_fundamental_analysis.pdf", "No", "us")