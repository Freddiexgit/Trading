import yfinance as yf
import pandas as pd

# --- Fetch Intraday Data ---
symbol = 'AAPL'
df = yf.download(tickers=symbol, period='5d', interval='5m')
print(df.head())
# --- Estimate Buying Volume ---
# If the close is higher than open, consider the volume as buying volume

# def safe_buy_volume(row):
#     try:
#         if row['Close'][0] > row['Open'][0]:
#             return row['Volume'][0]
#         else:
#             return 0
#     except Exception as e:
#         print(f"Error on row: {row}\nError: {e}")
#         return 0
#
# df['BuyVolume'] = df.apply(safe_buy_volume, axis=1)
df['BuyVolume'] = df.apply(lambda row: row['Volume'][0] if row['Close'][0] > row['Open'][0] else 0, axis=1)
df['SellVolume'] = df.apply(lambda row: row['Volume'][0] if row['Close'][0] < row['Open'][0] else 0, axis=1)

# --- Show Summary ---
total_buy = df['BuyVolume'].sum()
total_sell = df['SellVolume'].sum()

print(f"Estimated Buying Volume (last 5 days): {total_buy:,}")
print(f"Estimated Selling Volume (last 5 days): {total_sell:,}")

# Optional: Save to CSV
# df.to_csv('aapl_volume_analysis.csv')