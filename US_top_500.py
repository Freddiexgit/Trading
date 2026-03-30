import AVWAP_strategy
from dashboard_convergence_divergence_us import run_converge_diverge
from dashboard_find_common_ema_volumn import run_volume_and_cvg_dvg
from dashboard_us_last_volume import run_last_day_volume_increase
import os
from datetime import datetime
import  uptrend
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
#
data.global_period = "12mo"
data.global_interval ="1d"
data.to_be_removed_tickers
#
# data.global_period = "2y"
# data.global_interval ="1wk"
now = datetime.now()
if now.weekday()>=5:  # Saturday or Sunday
    date = f"{now.strftime("%Y-%m-%d")}_weekend"
else:
    date = now.strftime("%Y-%m-%d")
# ticker_file_name = "nzx_tickers"
# ticker_file_name = "my_vip"
# ticker_file_name = "my_watch_list"
# ticker_file_name = "nyse_and_nasdaq_top_500"
# ticker_file_name ="leading_stocks_by_industry"
ticker_file_name = "us_top_5000"

# ticker_file_name = "my_owned"
ticker_file_name_full = f"{ticker_file_name}.csv"
output_folder = f"output/{date}/us_{data.global_interval}/{ticker_file_name}"
if not os.path.exists(f"{output_folder}"):
    # Create the directory
    os.makedirs(f"{output_folder}")
try:
    print("running run_sector_rotation...")
    from sector_rotation import run_sector_rotation
    run_sector_rotation(output_file = f"{output_folder}/sector_rotation_{date}.csv")
    df_tickers_sr = pd.read_csv(f"{output_folder}/sector_rotation_{date}.csv")
    df_tickers_sr = df_tickers_sr.rename(columns={'Ticker': 'symbol'})
    di.generate_pdf(df_tickers_sr, f"{output_folder}/sector_rotation.pdf", "No", "us")

except Exception as e:
    print("run_sector_rotation error:", e)
try:
    print(f"running run_converge_diverge...{datetime.now()}")
    run_converge_diverge(f"{ticker_file_name_full}",output_folder = f"{output_folder}" )
except Exception  as e:
    print("run_converge_diverge error:", e)
try:
    print(f"running uptrend....{datetime.now()}")
    uptrend.run(f"resource/{ticker_file_name_full}",output_file = f"{output_folder}/uptrend_{date}.csv" )
    df_tickers_trend = pd.read_csv(f"{output_folder}/uptrend_{date}.csv")
    di.generate_pdf(df_tickers_trend[['symbol']].drop_duplicates().head(130), f"{output_folder}/uptrend.pdf",
                    "No", "us")
    df_tickers_trend1 = df_tickers_trend.sort_values("price", ascending=True).head(130)
    di.generate_pdf(df_tickers_trend1, f"{output_folder}/uptrend_price_asc.pdf",
                    "No", "us")
except Exception as e:
    print("trend error:", e)
try:
    print(f"running run_last_day_volume_increase....{datetime.now()}")
    run_last_day_volume_increase(f"{ticker_file_name_full}",output_folder = f"{output_folder}" )
except Exception as e:
    print("run_last_day_volume_increase error:", e)
try:
    print(f"running run_volume_and_cvg_dvg....{datetime.now()}")
    run_volume_and_cvg_dvg(output_folder = f"{output_folder}" )
except Exception as e:
    print("run_volume_and_cvg_dvg error:", e)

try:
    print(f"running quick fundamental ....{datetime.now()}")
    qfa.run_quick_fundamental_analysis(input_file=f"resource/{ticker_file_name_full}", output_file = f"{output_folder}/quick_fundamental_analysis_{date}.csv")
    df_tickers_fqa = pd.read_csv(f"{output_folder}/quick_fundamental_analysis_{date}.csv")
    df_tickers_fqa.columns = df_tickers_fqa.columns.str.lower()
    di.generate_pdf(df_tickers_fqa[['symbol']].drop_duplicates().head(100), f"{output_folder}/quick_fundamental_analysis.pdf", "No", "us")
    di.generate_pdf(df_tickers_fqa.sort_values("price", ascending=True)[['symbol']].drop_duplicates().head(100),
                    f"{output_folder}/quick_fundamental_analysis_price_asc.pdf", "No", "us")
except Exception  as e:
    print("error:", e)



try:
    print(f"EMA trend....{datetime.now()}")
    df_tickers = pd.read_csv(f"resource/{ticker_file_name_full}")["symbol"].dropna().tolist()
    eat.run(df_tickers,output_file = f"{output_folder}/EMA_Trend_{date}.csv")
    x = pd.read_csv(  f"{output_folder}/EMA_Trend_{date}.csv").query('accumulation_signal == "HEAVY_ACCUMULATION"')
    x = x[["symbol"]].head(130)
    di.generate_pdf( x, f"{output_folder}/EMA_Trend.pdf", "no", "us")
except Exception as e:
    traceback.print_exc()
    print("EMA trend error:", e)



def pd_read_pattern(pattern):
    files = glob.glob(pattern)

    df = pd.DataFrame()
    for f in files:
        df = pd.concat([df, pd.read_csv(f)], ignore_index=True)
    return df.reset_index(drop=True)



try:
    print(f"running find_cross....{datetime.now()}")
    df_tickers = pd.read_csv(f"resource/{ticker_file_name_full}")
    find_cross(df_tickers,output_folder)
    df_tickers_result = pd_read_pattern(f'{output_folder}/find_cross_ema*')
    df_tickers_result = df_tickers_result.drop_duplicates()
    di.generate_pdf(df_tickers_result, f"{output_folder}/find_cross_ema.pdf", "No", "us")
except Exception as e:
    print("find_cross error:", e)

if len(data.to_be_removed_tickers) > 0 :
    print(f"tickers to be removed: {data.to_be_removed_tickers}")
    with open("resource/to_be_removed_tickers.txt", "w") as f:
        f.write("symbol\n")
        for ticker in data.to_be_removed_tickers:
            f.write(f"{ticker}\n")
