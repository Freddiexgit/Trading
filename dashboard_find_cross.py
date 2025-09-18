from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di

s_str = datetime.now().strftime("%Y-%m-%d")






# Load the two CSV files
# Assume each CSV has a column called "stock" with stock tickers/names
df1 = pd.read_csv(f'resource/{s_str}/us/ema_cv_dv_{s_str}.csv')
df2 = pd.read_csv(f"resource/{s_str}/us/us_stock_5day_10day_vol_{s_str}.csv")

# Find the intersection
common_stocks = pd.merge(df1, df2, on="symbol")

# Display results
print("Common stocks:")
print(common_stocks)
common_stocks.to_csv(f'resource/common_cross/common_cross_{s_str}.csv', index=False)
di.generate_pdf(common_stocks,f"resource/{s_str}/us/volume_and_CD_{datetime.now().strftime('%Y-%m-%d')}.pdf","Yes","holding")