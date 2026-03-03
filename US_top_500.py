import AVWAP_strategy
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
import eam_analysis_with_trend as  eat
import pandas as pd
import glob
import  data_downloader as data
import traceback
import AI_buying_point as ai
import ema_angle_leaders as ea

data.global_period = "18mo"
data.global_interval ="1d"

#
# data.global_period = "2y"
# data.global_interval ="1wk"

date = datetime.now().strftime("%Y-%m-%d")
# ticker_file_name = "nzx_tickers"
# ticker_file_name = "my_vip"
# ticker_file_name = "my_watch_list"
ticker_file_name = "nyse_and_nasdaq_top_500"
# ticker_file_name ="leading_stocks_by_industry"
# ticker_file_name = "us_top_3000"
# ticker_file_name = "my_owned"
ticker_file_name_full = f"{ticker_file_name}.csv"
output_folder = f"output/{date}/us_{data.global_interval}/{ticker_file_name}"
if not os.path.exists(f"{output_folder}"):
    # Create the directory
    os.makedirs(f"{output_folder}")
try:
    print("running run_sector_rotation...")
    from sector_rotation import run_sector_rotation
    run_sector_rotation(output_file = f"{output_folder}/sector_rotation.csv")
    df_tickers_sr = pd.read_csv(f"{output_folder}/sector_rotation.csv")[["symbol"]]
    di.generate_pdf(df_tickers_sr, f"{output_folder}/sector_rotation.pdf", "No", "us")
except Exception as e:
    print("run_sector_rotation error:", e)
try:
    print("running run_converge_diverge...")
    run_converge_diverge(f"{ticker_file_name_full}",output_folder = f"{output_folder}" )
except Exception  as e:
    print("run_converge_diverge error:", e)
try:
    print("running run_last_day_volume_increase...")
    run_last_day_volume_increase(f"{ticker_file_name_full}",output_folder = f"{output_folder}" )
except Exception as e:
    print("run_last_day_volume_increase error:", e)
try:
    print("running run_volume_and_cvg_dvg...")
    run_volume_and_cvg_dvg(output_folder = f"{output_folder}" )
except Exception as e:
    print("run_volume_and_cvg_dvg error:", e)

try:
    qfa.run_quick_fundamental_analysis(input_file=f"resource/{ticker_file_name_full}", output_file = f"{output_folder}/quick_fundamental_analysis.csv")
    df_tickers_fqa = pd.read_csv(f"{output_folder}/quick_fundamental_analysis.csv")
    df_tickers_fqa.columns = df_tickers_fqa.columns.str.lower()
    di.generate_pdf(df_tickers_fqa[['symbol']], f"{output_folder}/quick_fundamental_analysis.pdf", "No", "us")
except Exception  as e:
    print("error:", e)

try:
    print("running ema_angle_leaders...")
    ea.main(f"resource/{ticker_file_name_full}", output_file = f"{output_folder}/ema_angle_leaders.csv")
    df_tickers_ea = pd.read_csv(f"{output_folder}/ema_angle_leaders.csv")
    di.generate_pdf(df_tickers_ea[["symbol"]].head(130), f"{output_folder}/ema_angle_leaders.pdf", "No", "us")
except Exception as e:
    print("ema_angle_leaders error:", e)
try:
    print("running ai entry point...")
    ai.run_ai_buying_point(f"resource/{ticker_file_name_full}", output_file = f"{output_folder}/ai_buy.csv")
    df_tickers_ai = pd.read_csv(f"{output_folder}/ai_buy.csv")
    di.generate_pdf(df_tickers_ai, f"{output_folder}/ai_buy.pdf", "yes", "us")
except Exception as e:
    print("ai entry point error:", e)

try:
    print("EMA trend...")
    df_tickers = pd.read_csv(f"resource/{ticker_file_name_full}")["symbol"].dropna().tolist()
    eat.run(df_tickers,output_file = f"{output_folder}/EMA_Trend.csv")
    x = pd.read_csv(  f"{output_folder}/EMA_Trend.csv")
    x = x[["symbol"]].head(130)
    di.generate_pdf( x, f"{output_folder}/EMA_Trend.pdf", "no", "us")
except Exception as e:
    print("EMA trend error:", e)
try:
    print("find AVWAP .....")
    AVWAP_strategy.run(f"resource/{ticker_file_name_full}", output_file = f"{output_folder}/avwap.csv")
    df_tickers_avwp = pd.read_csv(f"{output_folder}/avwap.csv")[["symbol"]]
    di.generate_pdf(df_tickers_avwp, f"{output_folder}/avwap.pdf", "yes", "us")
except Exception  as e:
    print("AVWAP error:", e)
try:

    print("running rsi_bottom...")
    rsi_bottom(f"resource/{ticker_file_name_full}", output_file = f"{output_folder}/bottom.csv")
    df_tickers_rsi = pd.read_csv(  f"{output_folder}/bottom.csv")
    di.generate_pdf(df_tickers_rsi, f"{output_folder}/bottom.pdf", "yes", "us")
except Exception  as  e:
    print("rsi_bottom error:", e)
try:
    print("running institute_enter...")
    institute_enter(f"resource/{ticker_file_name_full}",output_file = f"{output_folder}/institute_enter.csv")
    df_tickers_inst = pd.read_csv(f"{output_folder}/institute_enter.csv")
    di.generate_pdf(df_tickers_inst, f"{output_folder}/institute_enter.pdf", "No", "us")
except Exception as e:
    print("institute_enter error:", e)
try:
    print("running bid ask...")
    ask_bid.bid_ask_screener(f"resource/{ticker_file_name_full}",output_file = f"{output_folder}/bid_ask.csv")
    df_tickers_ba = pd.read_csv(f"{output_folder}/bid_ask.csv")
    di.generate_pdf(df_tickers_ba, f"{output_folder}/bid_ask.pdf", "No", "us")
except Exception as e:
    print("institute_enter error:", e)


def pd_read_pattern(pattern):
    files = glob.glob(pattern)

    df = pd.DataFrame()
    for f in files:
        df = pd.concat([df, pd.read_csv(f)], ignore_index=True)
    return df.reset_index(drop=True)

df_tickers = pd.read_csv(f"resource/{ticker_file_name_full}")

try:
    print("running find_cross...")
    find_cross(df_tickers,output_folder)
    df_tickers_result = pd_read_pattern(f'{output_folder}/find_cross_ema*')
    df_tickers_result = df_tickers_result.drop_duplicates()
    di.generate_pdf(df_tickers_result, f"{output_folder}/find_cross_ema.pdf", "No", "us")
except Exception as e:
    print("find_cross error:", e)


