import os
from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di
import five_days_and_20days as ema
import filter_by_volume5_and_volume10 as ft
from order_by_ema_60 import order_by_ema

s_str = datetime.now().strftime('%Y-%m-%d')

import pandas as pd
from pathlib import Path


def read_all_csv_in_folder(folder_path):
    """
    Reads all CSV files in a folder and combines them into one DataFrame.
    """
    path = Path(folder_path)

    # Use rglob to find all csv files (recursive search)
    # Use glob('*.csv') if you only want the top-level folder
    csv_files = list(path.glob('*.csv'))

    # List comprehension to read all files
    for f in csv_files:
        df_tickers = pd.read_csv(f"{f}")[["symbol"]]
        for t in df_tickers["symbol"].tolist():
            print(t)
        if not os.path.exists(f"output/{s_str}/us"):
            # Create the directory
            os.makedirs(f"output/{s_str}/us")
        di.generate_pdf(df_tickers, f"output/{s_str}/us/{f.stem}_{datetime.now().strftime('%Y-%m-%d')}.pdf", "No",
                        "holding")

if __name__ == "__main__":
    read_all_csv_in_folder("resource/vip")


