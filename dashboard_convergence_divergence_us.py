import os
from datetime import datetime

import pandas as pd
import ema_convergence_divergence as ec
import dashboard_list_indicators as di
import  order_by_ema_60 as obe
import five_days_and_20days as ema

s_str = datetime.now().strftime("%Y-%m-%d")


if not os.path.exists(f"resource/{s_str}/us"):
    # Create the directory
    os.makedirs(f"resource/{s_str}/us")
ec.call('nyse_and_nasdaq_top_500.csv', f'resource/{s_str}/us/ema_cv_dv_{s_str}.csv')
ema.run(f'resource/{s_str}/us/ema_cv_dv_{s_str}.csv', f'resource/{s_str}/us/us_stock_5days_above_20days_{s_str}.csv')
obe.order_by_ema(f'resource/{s_str}/us/us_stock_5days_above_20days_{s_str}.csv', f'resource/{s_str}/us/order_by_ema_{s_str}.csv', 20)

df_tickers = pd.read_csv(f"resource/{s_str}/us/order_by_ema_{s_str}.csv")
# df_tickers = df_tickers[0:50]
di.generate_pdf(df_tickers,f"resource/{s_str}/us/us_stock_cv_dv_indicators_{datetime.now().strftime('%Y-%m-%d-%H-%M')}.pdf","Yes","us")
