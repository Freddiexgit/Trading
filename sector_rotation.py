import yfinance as yf
import pandas as pd
import numpy as np
from analytics import industry_score as iscore
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

benchmark = 'SPY'
tickers = list(set(iscore.SECTOR_ETF.values()))+[benchmark]


# 2. Fetch the last 6 months of daily adjusted closing prices
print("Fetching sector data...")
data = yf.download(tickers, period='6mo')
close = data['Close']
high = data['High']
low = data['Low']
volume = data['Volume']

# 1. Calculate On-Balance Volume (OBV)
# If close > prev close, add volume. If close < prev close, subtract volume.
price_change_sign = np.sign(close.diff())
obv = (price_change_sign * volume).fillna(0).cumsum()

# Because raw OBV numbers are arbitrary, calculate the 20-day % change
obv_20_trend = obv.pct_change(periods=20).iloc[-1] * 100

# 2. Calculate Chaikin Money Flow (CMF) - standard 20-day period
# Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low)
mfm = ((close - low) - (high - close)) / (high - low)
mfm = mfm.fillna(0) # Handle potential division by zero

# Money Flow Volume = MFM * Volume
mfv = mfm * volume

# CMF = 20-day sum of MFV / 20-day sum of Volume
cmf = mfv.rolling(window=20).sum() / volume.rolling(window=20).sum()
current_cmf = cmf.iloc[-1]



# 3. Calculate Relative Strength (RS)
# This is the ratio of the Sector ETF price to the SPY price
rs_df = pd.DataFrame()
for ticker in tickers:
    rs_df[ticker] = close[ticker] / close[benchmark]

# 4. Calculate Capital Flow Momentum (Rate of Change of RS)
roc_5 = rs_df.pct_change(periods=5).iloc[-1] * 100
roc_10 = rs_df.pct_change(periods=10).iloc[-1] * 100
roc_20 = rs_df.pct_change(periods=20).iloc[-1] * 100
roc_60 = rs_df.pct_change(periods=60).iloc[-1] * 100

# 5. Compile the results safely by passing the Series directly (Pandas will auto-align the indices)
flow_summary = pd.DataFrame({
    '3-Month Momentum (%)': roc_60,
    '1-Month Momentum (%)': roc_20,
    '10-Day Momentum (%)': roc_10,
    '5-Day Momentum (%)': roc_5,
    'OBV 20-Day Trend (%)': obv_20_trend,
    'CMF (20-Day)': current_cmf
})



# 6. Calculate Trend Acceleration
flow_summary['Acceleration Delta'] = flow_summary['5-Day Momentum (%)'] - flow_summary['10-Day Momentum (%)']

# Add the Sector names using the sorted index from the DataFrame to ensure a 1-to-1 match
flow_summary['Sector'] = [iscore.SECTOR_ETF.get(ticker, ticker) for ticker in flow_summary.index]

# 7. Sort by the 5-Day Momentum (or Acceleration Delta)
ranked_flow = flow_summary.sort_values(by='5-Day Momentum (%)', ascending=False).round(2)

print("\n--- Current Capital Flow / Sector Rotation Ranking ---")
print(ranked_flow)
