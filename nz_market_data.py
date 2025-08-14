import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

# Sample DataFrame



# Load ticker symbols from CSV
df = pd.read_csv('resource/nzx_tickers.csv')
tickers = df['Ticker'].dropna().tolist()
# tickers =['2CC.NZ']
# Set date range
# end_date = datetime.today().date() - timedelta(days=1)
# start_date = end_date - timedelta(days=365)

start_date = datetime.today().date()- timedelta(days=3)
end_date = datetime.today().date()- timedelta(days=2)
file_name =f"resource/nzx_{end_date}.xlsx"

# Container for historical data
all_data = {}
os.makedirs(f'resource/nzx_{end_date}', exist_ok=True)
for ticker in tickers:
    try:
        print(f"Fetching: {ticker}")
        data = yf.download(ticker, start=start_date, end=end_date)
        print(data)
        data.columns = ['close', 'high', 'low', 'open', 'volume']
        data = data.reset_index()
        data['Prev_Value'] = data['close'].shift(1)  # previous row
        data['Price_Diff'] = data['close'] - data['Prev_Value']  # difference
        data['Prev_Value_volume'] = data['volume'].shift(1)  # previous row
        data['Volume_Diff'] = data['volume'] - data['Prev_Value_volume']  # difference
        data = data.drop('Prev_Value', axis=1)
        data = data.drop('Prev_Value_volume', axis=1)

        data.to_csv((f'resource/nzx_{end_date}/{ticker}.csv'), index=False)
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")

# Optional: save to Excel with a sheet per ticker
# with pd.ExcelWriter(file_name) as writer:
#     for ticker, data in all_data.items():
#         print(data)
#         data.columns = ['close', 'hight', 'low', 'open', 'volume']
#         data.to_excel(writer, sheet_name=ticker[:31])  # sheet names must be ≤ 31 chars

