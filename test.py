import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# response = requests.get("https://scanner.tradingview.com/newzealand/scan?label-product=markets-screener")
# response = requests.get("https://www.tradingview.com/markets/stocks-new-zealand/market-movers-all-stocks/")

# print(response.json())
#
# soup = BeautifulSoup(response.content, 'html.parser')
#
# table = soup.find('table')


# ticker = "AAPL"  # example: Apple Inc.
# data = yf.download(ticker, period="7d", interval="1d")
# data['Raw_Change'] = data['Close'].diff()
# print(data)

import os
def rename_files_recursively(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
                old_path = os.path.join(root, filename)
                if filename.endswith('.txt'):  #or filename.endswith('.txt'):
                    base = filename.rsplit('.', 1)[0]  # Remove last two extensions

                    new_path = os.path.join(root, base)
                    os.rename(old_path, new_path)
                    print(f"Renamed: {old_path} → {new_path}")
    for dir in dirs:
        rename_files_recursively(dir)

# Example usage
rename_files_recursively('/Users/freddie/Documents/code/nztdai-nexus-backend - Copy')