import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# === 1. Select representative tickers for each sector ===
sector_tickers = {
    "Technology": ["AAPL", "MSFT", "NVDA", "ORCL", "CRM"],
    "Financials": ["JPM", "BAC", "WFC", "GS", "MS"],
    "Healthcare": ["UNH", "JNJ", "PFE", "MRK", "ABBV"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
    "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE"],
    "Consumer Staples": ["PG", "KO", "PEP", "WMT", "COST"],
    "Industrials": ["CAT", "GE", "BA", "UPS", "DE"],
    "Utilities": ["NEE", "DUK", "SO", "EXC", "AEP"],
    "Real Estate": ["PLD", "O", "AMT", "EQIX", "SPG"],
    "Materials": ["LIN", "APD", "SHW", "ECL", "NEM"]
}

# === 2. Download recent data ===
data = yf.download(sum(sector_tickers.values(), []), period="5d", interval="1d", group_by="ticker")

# === 3. Compute average sector return and volume change ===
sector_flows = []

for sector, tickers in sector_tickers.items():
    returns = []
    vols = []
    for t in tickers:
        df = data[t]
        df["PctChange"] = df["Close"].pct_change()
        df["VolChange"] = df["Volume"].pct_change()
        returns.append(df["PctChange"].iloc[-1])
        vols.append(df["VolChange"].iloc[-1])
    avg_ret = np.nanmean(returns)
    avg_vol = np.nanmean(vols)
    flow_strength = avg_ret * (1 + avg_vol)
    sector_flows.append((sector, avg_ret, avg_vol, flow_strength))

df_flow = pd.DataFrame(sector_flows, columns=["Sector", "AvgReturn", "AvgVolChange", "FlowStrength"])
df_flow = df_flow.sort_values("FlowStrength", ascending=False)

# === 4. Display as bar chart ===
plt.figure(figsize=(10,6))
sns.barplot(x="FlowStrength", y="Sector", data=df_flow, palette="coolwarm")
plt.title("💵 U.S. Stock Sector Money Flow (Approximation)")
plt.xlabel("Flow Strength = AvgReturn × (1 + AvgVolChange)")
plt.tight_layout()
plt.show()

# === 5. Optional: print summary ===
print(df_flow)
