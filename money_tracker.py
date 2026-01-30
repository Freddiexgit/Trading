# sector_rotation_detector.py
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")

# 1) Configure ETFs
SECTOR_ETFS = {
    "XLK":"Technology",
    "XLE":"Energy",
    "XLF":"Financials",
    "XLY":"ConsumerDiscretionary",
    "XLP":"ConsumerStaples",
    "XLI":"Industrials",
    "XLB":"Materials",
    "XLU":"Utilities",
    "XLV":"HealthCare",
    "XLC":"CommunicationServices",
    "XBI":"Biotech"
}

end = datetime.today()
start = end - timedelta(days=365*2)  # 2 years of history

# 2) Download price history
tickers = list(SECTOR_ETFS.keys())
df_prices = yf.download(tickers, start=start, end=end)['Close']

# 3) Compute returns (period returns)
def period_return(prices, days):
    return prices.pct_change(periods=days)

# Example periods: 63 trading days ~ 3m, 126 ~ 6m, 252 ~ 12m
periods = {"3m":63, "6m":126, "12m":252}
momentum = pd.DataFrame(index=df_prices.index)

for name, days in periods.items():
    momentum[name] = df_prices.apply(lambda col: col.pct_change(periods=days))

# take the last available value
latest_mom = momentum.dropna().iloc[-1]

# 4) Z-score across sectors for each period
z_scores = {}
for p in periods:
    s = momentum[p].dropna()
    z = (s.iloc[-1] - s.mean(axis=0)) / s.std(axis=0)
    z_scores[p] = z

z_df = pd.DataFrame(z_scores)

# 5) Simple combined score (weighted)
weights = {"3m":0.4, "6m":0.3, "12m":0.3}
combined = sum(z_df[col]*w for col,w in weights.items())
combined = combined.sort_values(ascending=False)

# 6) ETF flows / AUM proxy (optional)
# yfinance sometimes provides 'totalAssets' in info for ETFs
aum = {}
for t in tickers:
    try:
        info = yf.Ticker(t).info
        aum[t] = info.get("totalAssets", np.nan)
    except Exception:
        aum[t] = np.nan

aum_series = pd.Series(aum).sort_values(ascending=False)

# 7) Identify rotation candidates
top_n = 3
top_sectors = combined.index[:top_n].tolist()
bottom_sectors = combined.index[-top_n:].tolist()

print("Top sectors (by combined momentum z-score):", top_sectors)
print("Bottom sectors:", bottom_sectors)
print("\nCombined scores:\n", combined)

# 8) Simple plotting
plt.figure(figsize=(12,6))
combined.plot(kind='bar')
plt.title("Combined Momentum Z-Score by Sector ETF")
plt.ylabel("Z-Score")
plt.axhline(0, color='k', linewidth=0.5)
plt.tight_layout()
plt.show()

# 9) Heatmap of momentum periods
plt.figure(figsize=(10,6))
sns.heatmap(z_df.loc[combined.index], annot=True, cmap='coolwarm', center=0)
plt.title("Z-scores by period (sectors sorted by combined score)")
plt.tight_layout()
plt.show()

# 10) If you have external ETF flow CSV (provider), merge and use:
# flows.csv expected columns: date,ticker,net_flow_usd
# flows = pd.read_csv("flows.csv", parse_dates=["date"])
# latest_flows = flows[flows.date == flows.date.max()].set_index("ticker")["net_flow_usd"]
# combined_with_flows = pd.DataFrame({"score":combined, "aum":aum_series, "flows": latest_flows})
# combined_with_flows.sort_values("score", ascending=False)
