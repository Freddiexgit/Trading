import os
from datetime import datetime

import pandas as pd
import  morning_star as ms


s_str = datetime.now().strftime("%Y-%m-%d")


if not os.path.exists(f"resource/{s_str}/us"):
    # Create the directory
    os.makedirs(f"resource/{s_str}/us")
ms.morning_star('nzx_tickers.csv', f'resource/{s_str}/nz/morning_star_{s_str}.csv')

