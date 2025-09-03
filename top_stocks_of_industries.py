from time import sleep

import yfinance as yf
import pandas as pd

# Example: get a batch of tickers (you can extend this list or load from NasdaqTrader)
# Full list: ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt

# df = pd.read_csv(f'resource/us_tickers.csv')
# tickers = df['symbol'].dropna().tolist()
# data = []
# for t in tickers:
#     print(t)
#     sleep(1)
#     try:
#         info  = yf.Ticker(t).info
#         data.append({
#             "ticker": t,
#             "name": info.get("longName"),
#             "sector": info.get("sector"),
#             "industry": info.get("industry"),
#             "marketCap": info.get("marketCap")
#         })
#     except Exception as e:
#         print(f"Error fetching {t}: {e}")
#
# df = pd.DataFrame(data)
#
# # Drop rows without industry
# df = df.dropna(subset=["industry", "marketCap"])
# df.to_csv("stocks_by_industry.csv", index=False)
# For each industry, get the stock with max market cap
df = pd.read_csv('stocks_by_industry.csv')
# leaders = df.loc[df.groupby("industry")["marketCap"].nlargest(5)].reset_index(drop=True)
df["rank"] = df.groupby("industry")["marketCap"].rank("first", ascending=False)
leaders = (df[df["rank"] <= 5]
         .sort_values(["industry", "rank"])
         .reset_index(drop=True))
print(leaders)

# Save to CSV if needed
leaders.to_csv("leading_stocks_by_industry.csv", index=False)