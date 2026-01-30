#
# Run daily or hourly (depending on data freshness).
#
# When rate_regime='rate_up' and vol_regime='low_vol' → overweight value/cyclicals.
#
# When rate_regime='rate_down' & vol_regime='low_vol' → overweight growth / tech.
#
# Combine macro signal with the sector momentum detector from part (1) to pick sectors that both fit the macro regime and have positive momentum + flows.
#
# Putting 1 + 2 together (recommended flow)
#
# Run the sector detector to get momentum + flow ranks.
#
# Run the macro dashboard to get regime and recommended sector buckets.
#
# Intersect: recommended = top sectors by momentum ∩ macro-recommended buckets ∩ positive latest flows.
#
# Apply portfolio sizing rules (risk parity, max weight, stop loss).
#
# Practical tips & data sources
#
# Sector ETF tickers: XLK (tech), XLE (energy), XLF (financials), XLY (cons disc), XLP (staples), XLI (industrials), XLB (materials), XLU (utilities), XLV (health), XLC (comm), XBI (biotech).
#
# ETF flows / AUM: Some ETF issuers (BlackRock, State Street) publish flows; providers like EPFR and iFlow provide institutional flow data (paid). You can often purchase or ingest CSVs from them.
#
# Macro series: Use FRED via pandas_datareader for Fed funds and Treasury yields; yfinance for VIX and equity indexes.
#
# Backtesting: Backtest rotation strategy with transaction costs; rules that simply rotate each month between top sectors often show decent returns but require risk management.
#
# Databricks: run these notebooks in Databricks; store outputs (signals, recommended weights) in Delta tables for downstream ingestion.
 # macro_dashboard.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()

sns.set(style="whitegrid")
end = pd.Timestamp.today()
start = end - pd.DateOffset(years=3)

# 1) Fetch macro series (FRED via pandas-datareader)
import pandas_datareader.data as web
try:
    dgs10 = web.DataReader('DGS10', 'fred', start, end).rename(columns={'DGS10':'10Y'})
    fedfunds = web.DataReader('FEDFUNDS', 'fred', start, end).rename(columns={'FEDFUNDS':'FedFunds'})
    vix = yf.download("^VIX", start=start, end=end)['Adj Close'].rename("VIX")
    # USD index might be from FRED 'DTWEXBGS' or other tickers; example:
    usd = web.DataReader('DTWEXBGS', 'fred', start, end).rename(columns={'DTWEXBGS':'USD_Index'})
except Exception as e:
    print("Data fetch issue; ensure network access and that pandas-datareader is configured:", e)
    raise

# 2) Align series
df = pd.concat([dgs10, fedfunds, vix, usd], axis=1).dropna()

# 3) Feature engineering - short-term changes and z-scores
df['10Y_3m_delta'] = df['10Y'].pct_change(63)
df['VIX_20d_ma'] = df['VIX'].rolling(20).mean()
df['USD_20d_z'] = (df['USD_Index'] - df['USD_Index'].rolling(63).mean()) / df['USD_Index'].rolling(63).std()

# 4) Macro regime signal (simple rule-based)
# Rate regime: if 10Y_3m_delta > 0.05 -> rates rising
df['rate_regime'] = np.where(df['10Y_3m_delta'] > 0.05, 'rate_up',
                    np.where(df['10Y_3m_delta'] < -0.05, 'rate_down', 'neutral'))

# Volatility regime
df['vol_regime'] = np.where(df['VIX'] > df['VIX'].rolling(63).mean()*1.15, 'high_vol', 'low_vol')

# 5) Map regime to sector preference (example mapping)
regime_map = {
    ('rate_up','high_vol'): ["XLF","XLE","XLI"],  # financials, energy, industrials
    ('rate_up','low_vol'): ["XLF","XLE","XLB"],
    ('rate_down','low_vol'): ["XLK","XBI","XLY"],
    ('rate_down','high_vol'): ["XLK","XLV","XLP"],
    ('neutral','low_vol'): ["XLK","XLI","XLF"],
    ('neutral','high_vol'): ["XLV","XLU","XLP"]
}

latest = df.iloc[-1]
key = (latest['rate_regime'], latest['vol_regime'])
recommended = regime_map.get(key, ["XLK","XLF"])

print("Latest macro regime:", key)
print("Recommended sector ETFs:", recommended)

# 6) Plot dashboard elements
fig, axes = plt.subplots(3,1, figsize=(12,10))
axes[0].plot(df['10Y']); axes[0].set_title("10Y Treasury Yield")
axes[1].plot(df['VIX']); axes[1].set_title("VIX")
axes[2].plot(df['USD_Index']); axes[2].set_title("USD Index")
plt.tight_layout()
plt.show()

# 7) Optional: create an interactive Dash/Plotly app showing time series + recommended sectors
# (Dash code omitted for brevity — can be provided if you'd like a Jupyter/Dash app)
