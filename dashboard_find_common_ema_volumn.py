from datetime import datetime

import pandas as pd
import  dashboard_list_indicators as di


def run_volume_and_cvg_dvg(output_folder =f"resource/{datetime.now().strftime('%Y-%m-%d')}/us" ):
    date = datetime.now().strftime("%Y-%m-%d")

    # Load the two CSV files
    # Assume each CSV has a column called "stock" with stock tickers/names
    df1 = pd.read_csv(f'{output_folder}/ema_cv_dv_ordered_by_20ema.csv')
    df2 = pd.read_csv(f"{output_folder}/volume_last1day_and10.csv")
    # Find the intersection
    cv_dv_volume_stocks = pd.merge(df1, df2, on="symbol")
    # Display results
    print("ema_cv_dv and volume stocks:")
    # print(cv_dv_volume_stocks)
    cv_dv_volume_stocks.to_csv(f'{output_folder}/cv_dv_volume_stocks.csv', index=False)
    di.generate_pdf(cv_dv_volume_stocks, f"{output_folder}/volume_and_CD.pdf",
                    "Yes", "holding")



