from time import sleep

import requests
import pandas as pd
from datetime import datetime, timedelta
import requests
import pandas as pd
from bs4 import BeautifulSoup
from sqlalchemy.testing import future
pd.set_option('display.max_columns', None)
# --- Configuration ---
# Replace with your actual Finnhub API key (get it from finnhub.io)
FINNHUB_API_KEY = "d1jhfmhr01qvg5guio70d1jhfmhr01qvg5guio7g"

# Base URL for Finnhub's insider transactions API
FINNHUB_INSIDER_URL = "https://finnhub.io/api/v1/stock/insider-transactions"


def get_finnhub_insider_transactions(symbol, _from_date, _to_date):
    """
    Fetches insider transactions for a given stock symbol from Finnhub.
    _from_date and _to_date should be in 'YYYY-MM-DD' format.
    """
    params = {
        "symbol": symbol,
        "from": _from_date,
        "to": _to_date,
        "token": FINNHUB_API_KEY
    }
    try:
        response = requests.get(FINNHUB_INSIDER_URL, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data and 'data' in data:
            df = pd.DataFrame(data['data'])
            return df
        else:
            print(f"No insider trading data found for {symbol} between {_from_date} and {_to_date}.")
            return pd.DataFrame()  # Return empty DataFrame
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Finnhub API for {symbol}: {e}")
        return pd.DataFrame()


def download_nasdaq_insider_buying(symbols, days_back=30):
    """
    Downloads insider buying data for specified NASDAQ symbols.
    """
    today = datetime.now()
    from_date = (today - timedelta(days=days_back)).strftime('%Y-%m-%d')
    to_date = today.strftime('%Y-%m-%d')

    all_insider_data = []

    print(f"\n--- Downloading NASDAQ Insider Trading Data (Last {days_back} days) ---")
    for symbol in symbols:
        print(f"Fetching data for {symbol}...")
        df = get_finnhub_insider_transactions(symbol, from_date, to_date)
        sleep(1)
        if not df.empty:
            # Filter for buying transactions (assuming 'change' > 0 means buying)
            # You might need to adjust this based on the API's exact data structure
            # Common 'transactionCode' values: 'P' for purchase, 'S' for sale, 'G' for gift
            # Check Finnhub documentation for 'transactionCode' details.

            # For demonstration, let's assume 'transactionCode' 'P' (Purchase)
            # and 'share' (number of shares changed) > 0 for buying

            # The 'share' column in Finnhub indicates the change in shares.
            # A positive 'share' usually means an acquisition (buy).
            # The 'transactionCode' can further clarify (e.g., 'P' for Purchase).

            # insider_buying_df = df[(df['share'] > 0) & (df['transactionCode'] == 'P')]
            print(df)
            insider_buying_df = df[(df['share'] > 0)]
            if not df.empty:
                insider_buying_df['symbol'] = symbol  # Add symbol for clarity
                all_insider_data.append(insider_buying_df)

                print(f"Found {len(insider_buying_df)} buying transactions for {symbol}.")
            else:
                print(f"No insider buying transactions found for {symbol}.")
        else:
            print(f"Could not retrieve data for {symbol}.")

    if all_insider_data:
        final_df = pd.concat(all_insider_data, ignore_index=True)
        # Select and reorder relevant columns
        # final_df = final_df[
        #     ['symbol', 'name', 'share', 'change', 'transactionCode', 'filingDate', 'sharePrice', 'ownershipType']]
        print("\n--- Consolidated NASDAQ Insider Buying Data ---")
        print(final_df.head())
        # Save to CSV
        file_name = f"nasdaq_insider_buying_{from_date}_to_{to_date}.csv"
        final_df.to_csv(file_name, index=False)
        print(f"\nData saved to {file_name}")
    else:
        print("No insider buying data found for any of the specified NASDAQ symbols.")




def get_nasdaq_insider_buying():
    url = "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=30&fdr=&tdr=&fdlyl=&fdlyh=&daysago=30&xp=1&vl=&vh=&ocl=&och=&sic1=&sic2=&sortcol=0&maxresults=1000"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="tinytable")

    df = pd.read_html(str(table))[0]
    buying_df = df[df['Trade Type'].str.contains("P - Purchase", na=False)]
    return buying_df





def get_nzx_insider_buying():
    url = "https://www.nzx.com/announcements"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    announcements = soup.find_all("a", class_="announcement__title")
    insider_trades = [a.text.strip() for a in announcements if "director" in a.text.lower()]

    return insider_trades



if __name__ == "__main__":
    nasdaq_symbols=["ORCL"]
    # Example NASDAQ symbols
    # nasdaq_symbols = [
    #     "HSAI",
    #     "FUTU",
    #     "TIGR",
    #     "EH",
    #     "KC",
    #     "META",
    #     "GOOGL",
    #     "AMZN",
    #     "MSFT",
    #     "AAPL",
    #     "NVDA",
    #     "TSLA",
    #     "TSLQ",
    #     "LI",
    #     "XPEV",
    #     "NIO",
    #     "PLTU",
    #     "PLTD",
    #     "PLTR",
    #     "NVDA",
    #     "NVDL",
    #     "UGL",
    #     "GLL",
    #     "AMZD",
    #     "AMZZ",
    #     "AAPD",
    #     "AAPU",
    #     "YANG",
    #     "MSTZ",
    #     "MSTU",
    #     "US37001",
    #     "ORCL",
    #     "GBTC",
    #     "BITU",
    #     "SBIT",
    #     "DJT",
    #     "GDS",
    #     "RGTI",
    #     "RGTX",
    #     "CRWV",
    #     "US37030",
    #     "CAN",
    #     "MFI",
    #     "CRCL",
    #     "US37161",
    #     "MSTR",
    #     "BABX",
    #     "BABA",
    #     "MSFU",
    #     "MSFD",
    #     "AMD",
    #     "UVIX",
    #     "US37090",
    #     "JD",
    #     "YINN",
    #     "METD",
    #     "METU",
    #     "SMCI",
    #     "SMCZ",
    #     "SMCX",
    #     "WRD",
    #     "TSLL",
    #     "HSBC"]

    # Download NASDAQ insider buying data for the last 90 days
    download_nasdaq_insider_buying(nasdaq_symbols, days_back=10)
    # nasdaq_data = get_nasdaq_insider_buying()
    # print(nasdaq_data.head())

    # print(get_nzx_insider_buying())