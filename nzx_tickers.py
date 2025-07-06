import requests
from bs4 import BeautifulSoup
import pandas as pd

# NZX URL
url = "https://www.nzx.com/markets/NZSX"

# Set up headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0'
}

# Fetch page content
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Parse the page to find securities (may need adjustment based on actual structure)
tickers = []
for link in soup.find_all('a', href=True):
    href = link['href']
    if href.startswith('/instruments/') and '.NZ' not in link.text:
        ticker = link.text.strip()
        if ticker.isupper():
            tickers.append(ticker + '.NZ')

# Display result
df = pd.DataFrame(tickers, columns=['Ticker'])
df.to_csv('resource/nzx_tickers.csv', index=False)