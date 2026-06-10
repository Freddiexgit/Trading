# pip install finvizfinance
from finvizfinance.group.valuation import Valuation
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1200)

# This pulls a dataframe of all industries and their median valuation metrics
finviz_val = Valuation()
industry_df = finviz_val.screener_view(group='Industry')

industry_df.to_csv("industry_fundamental_values.csv", index=False)
