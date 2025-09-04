import os

from datetime import datetime

import pandas as pd
import dashboard_list_indicators as di
df = pd.read_csv(f'resource/leading_stocks_by_industry.csv' )
# df=pd.DataFrame({"symbol": ["CCCX"]})



s_str = datetime.now().strftime("%Y-%m-%d")
if not os.path.exists(f"resource/{s_str}/us"):
    # Create the directory
    os.makedirs(f"resource/{s_str}/us")

di.generate_pdf(df,f"resource/{s_str}/us/industry_leading_stocks_{datetime.now().strftime('%Y-%m-%d-%H-%M')}.pdf","No","us")
