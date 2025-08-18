from time import sleep

import pandas as pd
import requests

# Source URLs hosting exchange listings
nasdaq_url = 'https://api.nasdaq.com/api/screener/stocks?exchange=NASDAQ&limit=100&offset=placeholder'
nyse_url = 'https://api.nasdaq.com/api/screener/stocks?exchange=NYSE&limit=100&offset=placeholder'
headers = {'User-Agent': 'Mozilla/5.0'}

def fetch_tickers(url):
    rows_total = []
    for i in range(200):
        urlx = url.replace("placeholder", str(i * 100))
        response = requests.get(urlx, headers=headers)
        data = response.json()
        sleep(1)

        rows = data['data']['table']['rows']
        if rows:
            rows_total.extend(rows)
        else:
            print(f"No rows found at index {i}")
            break

    return pd.DataFrame(rows_total)

# Fetch tickers
nasdaq_df = fetch_tickers(nasdaq_url)
nasdaq_tickers = nasdaq_df['symbol']
nasdaq_tickers.to_csv('resource/nasdaq_tickers.csv', index=False)
nasdaq_tickers = None
nyse_df = fetch_tickers(nyse_url)

# Extract ticker symbols

nyse_tickers = nyse_df['symbol']
nyse_tickers.to_csv('resource/nyse_tickers.csv', index=False)

# Combine


