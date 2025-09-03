import requests
import pandas as pd

# Replace with your actual API key from a service like Quiver or Finnhub
api_key = "YOUR_API_KEY_HERE"
base_url = "https://api.quiverquant.com/api/v1/beta/historical/congresstrading"

# Define the parameters for your request (e.g., specific politician or stock)
# Quiver's API is just an example, a real-world implementation might need different parameters
params = {
    'ticker': 'AAPL',  # Example: download transactions for Apple (AAPL)
    'start': '2023-01-01',
    'end': '2024-01-01',
    'token': api_key
}

try:
    response = requests.get(base_url, params=params)
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

    data = response.json()
    if data:
        df = pd.DataFrame(data)
        print("Successfully downloaded data:")
        print(df.head())
    else:
        print("No data found for the given parameters.")

except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
