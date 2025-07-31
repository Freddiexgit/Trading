import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Step 1: Download historical stock data
ticker = 'AAPL'  # Replace with your desired stock symbol
df = yf.download(ticker, start='2023-01-01', end='2024-01-01')

# Step 2: Calculate EMAs
ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
ema_26 = df['Close'].ewm(span=26, adjust=False).mean()

# Step 3: Calculate MACD and Signal Line
macd = ema_12 - ema_26
signal = macd.ewm(span=9, adjust=False).mean()

# Step 4: Add to DataFrame
df['MACD'] = macd
df['Signal'] = signal
df['Histogram'] = df['MACD'] - df['Signal']

# Step 5: Plot
plt.figure(figsize=(12,6))
plt.plot(df.index, df['MACD'], label='MACD', color='blue')
plt.plot(df.index, df['Signal'], label='Signal Line', color='red')
plt.bar(df.index, df['Histogram'], label='Histogram', color='gray')
plt.title(f'MACD Indicator for {ticker}')
plt.legend()
plt.grid(True)
plt.show()