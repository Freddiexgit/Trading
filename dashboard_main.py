from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di

s_str = datetime.now().strftime('%Y-%m-%d')

df_tickers = pd.read_csv(f"resource/{s_str}/nz/nz_stock_5day_10day_vol_2025-08-18.csv")

di.generate_pdf(df_tickers,f"resource/{s_str}/nz/stock_indicators_{datetime.now().strftime('%Y-%m-%d')}.pdf")