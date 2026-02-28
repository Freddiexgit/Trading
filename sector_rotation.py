import yfinance as yf
import pandas as pd
from analytics import industry_score as iscore
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
# 1. Define the 11 Major SPDR Sector ETFs and the Benchmark (S&P 500)
# sectors = {
#     'XLE': 'Energy',
#     'XLB': 'Materials',
#     'XLI': 'Industrials',
#     'XLF': 'Financials',
#     'XLU': 'Utilities',
#     'XLP': 'Consumer Staples',
#     'XLRE': 'Real Estate',
#     'XLV': 'Health Care',
#     'XLC': 'Communication Services',
#     'XLK': 'Technology',
#     "ITA":"Aerospace & Defense",
#     "IYW": "Information Technology Services",
#     "XBI": "Diagnostics & Research",
#     "SOXX": "Electronic Components",
#     "GDX": "Gold",
#     "FDN": "Internet Content & Information",
#     "IGV": "Software - Application",
#     "URA": "Uranium",
#     'XLY': 'Consumer Discretionary'
# }
benchmark = 'SPY'
tickers = list(set(iscore.SECTOR_ETF.values()))+[benchmark]


# 2. Fetch the last 6 months of daily adjusted closing prices
print("Fetching sector data...")
data = yf.download(tickers, period='6mo')['Close']

# 3. Calculate Relative Strength (RS)
# This is the ratio of the Sector ETF price to the SPY price
rs_df = pd.DataFrame()
for ticker in tickers:
    rs_df[ticker] = data[ticker] / data[benchmark]

# 4. Calculate Capital Flow Momentum (Rate of Change of RS)
# A positive ROC means the sector is outperforming the S&P 500 over that timeframe
roc_5 = rs_df.pct_change(periods=5).iloc[-1] * 100  # 1-Month Momentum (~5 trading days)
roc_10 = rs_df.pct_change(periods=10).iloc[-1] * 100  # 1-Month Momentum (~10 trading days)
roc_20 = rs_df.pct_change(periods=20).iloc[-1] * 100  # 1-Month Momentum (~20 trading days)
roc_60 = rs_df.pct_change(periods=60).iloc[-1] * 100  # 3-Month Momentum (~60 trading days)

# 5. Compile the results into a clean DataFrame
flow_summary = pd.DataFrame({
    'Sector': [iscore.SECTOR_ETF.get(ticker, ticker) for ticker in tickers],
    '3-Month Momentum (%)': roc_60.values,
    '1-Month Momentum (%)': roc_20.values,
    '10-Day Momentum (%)': roc_10.values,
    '5-Day Momentum (%)': roc_5.values
})

# 1. Calculate Trend Acceleration
# (How much better is the last 5 days compared to the last month?)
flow_summary['Acceleration Delta'] = flow_summary['5-Day Momentum (%)'] - flow_summary['10-Day Momentum (%)']

# 2. Sort by the Acceleration Delta (highest positive change at the top)
ranked_flow = flow_summary.sort_values(by='5-Day Momentum (%)', ascending=False).round(2)

print("\n--- Current Capital Flow / Sector Rotation Ranking ---")
print(ranked_flow)