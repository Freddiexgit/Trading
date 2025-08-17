import yfinance as yf
from datetime import datetime

# Define the stock symbol (e.g., AAPL for Apple)
stock_symbol = "AAPL"

# Get the stock data
stock = yf.Ticker(stock_symbol)

# Get today's date
today = datetime.today().strftime('%Y-%m-%d')

# Fetch the historical data for today (adjust if market is closed)
data = stock.history(period="6mo")

data.to_csv(f'resource/price_history_{stock_symbol}_{datetime.now().strftime('%Y-%m-%d')}.csv', index=True)

# Display the result
# if not data.empty:
#     print(f"Stock: {stock_symbol}")
#     print(f"Date: {data.index[0].date()}")
#     print(f"Open: {data['Open'][0]:.2f}")
#     print(f"High: {data['High'][0]:.2f}")
#     print(f"Low: {data['Low'][0]:.2f}")
#     print(f"Close: {data['Close'][0]:.2f}")
#     print(f"Volume: {int(data['Volume'][0])}")
# else:
#     print("No data available for today. The market may be closed.")