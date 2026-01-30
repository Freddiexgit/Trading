import requests
import datetime
import csv
import pytz

# BASE = "https://arkfunds.io/api/v2/stock/trades"  # base URL for this API
BASE = "https://arkfunds.io/api/v2"



# Define the New York timezone
# new_york_tz = pytz.timezone('America/New_York')
#
# # Get the current time in New York
# new_york_date = datetime.now(new_york_tz).strftime('%Y-%m-%d')


from datetime import datetime, timedelta

# Current date and time
current_date = datetime.now()

# Subtract one day
yesterday = current_date - timedelta(days=1)
str = yesterday.strftime('%Y-%m-%d')
today = current_date.strftime('%Y-%m-%d')
def get_etf_trades(etf_symbol: str):
    """
    Get trades for a specific ARK ETF via API.
    Returns list of trade dicts (or empty list).
    """
    url = f"{BASE}/etf/trades"
    params = {
        "symbol": etf_symbol,
        "date_from": str,
        "date_to": today,
        "limit": 1000
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    # The response likely has fields like data, total, etc.
    return resp.json()["trades"]



def trades_to_csv(trades, output_file: str):
    """
    Write list of trade dicts to CSV (flattened).
    """
    if not trades:
        print("No trades to write.")
        return
    keys = sorted(trades[0].keys())
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(trades)



def get_etf_holdings(etf_symbol: str, page: int = 1, limit: int = 100):
    url = f"{BASE}/etf/holdings"
    params = {
        "symbol": etf_symbol,
        "date_from": "2025-09-22",
         "date_to": "2025-09-24",
        "limit": 1000
    }
    resp = requests.get(url, params=params)
    print(resp.url)
    resp.raise_for_status()
    return resp.json()["holdings"]

def get_current_holdings(etf_symbol: str):
    return get_etf_holdings(etf_symbol, page=1, limit=500)

if __name__ == "__main__":
    etfs = ["ARKK","ARKQ","ARKW","ARKG","ARKF","ARKX"]
    # one of A RK’s ETFs
    all_trades = []
    for etf in etfs:
        all_trades.extend(get_etf_trades(etf))
    print(all_trades)
    trades_to_csv(all_trades, f"{today}_trades.csv")

    # x = get_current_holdings(etf)
    # print(x)