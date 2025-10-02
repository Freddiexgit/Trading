from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di


def run_volume_and_cvg_dvg(top500 = True):
    date = datetime.now().strftime("%Y-%m-%d")
    if top500:
        s_str = date + "_top_500"
    else:
        s_str = date + "_median"

    # Load the two CSV files
    # Assume each CSV has a column called "stock" with stock tickers/names
    df1 = pd.read_csv(f'resource/{date}/us/ema_cv_dv_{s_str}.csv')
    df2 = pd.read_csv(f"resource/{date}/us/us_stock_last_day_vol_{s_str}.csv")
    # Find the intersection
    common_stocks = pd.merge(df1, df2, on="symbol")
    # Display results
    print("Common stocks:")
    print(common_stocks)
    common_stocks.to_csv(f'resource/common_cross/common_cross_{s_str}.csv', index=False)
    di.generate_pdf(common_stocks, f"resource/{date}/us/volume_and_CD_{s_str}_{datetime.now().strftime('%H-%M')}.pdf",
                    "Yes", "holding")



