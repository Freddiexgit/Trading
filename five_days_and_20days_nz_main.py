import os
from datetime import datetime

import five_days_and_20days as ema

if __name__ == "__main__":
    s_str = datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(f"resource/{s_str}/us"):
        # Create the directory
        os.makedirs(f"resource/{s_str}/us")
    ema.run('nzx_tickers.csv', f'resource/{s_str}/nz_stock_5days_above_20days_{s_str}.csv')
