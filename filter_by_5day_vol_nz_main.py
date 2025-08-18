import os
from datetime import datetime

import filter_by_volume5_and_volume10 as ft

if __name__ == "__main__":
    s_str = datetime.now().strftime('%Y-%m-%d')
    ft.filter(f"resource/{s_str}/nz/nz_stock_5days_above_20days_{s_str}.csv",
              f"resource/{s_str}/nz/nz_stock_5day_10day_vol_{s_str}.csv")