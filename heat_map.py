import yfinance as yf
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Your shortlisted tickers from the image
# tickers = ['JOE', 'SBLK', 'KNX', 'PPTA', 'AG', 'WPM', 'AEM', 'ROST', 'CLH', 'CTVA', 'NTR']

tickers = pd.read_csv(f"output/2026-02-28/us_1d/my_watch_list/quick_fundamental_analysis.csv")["symbol"].tolist()
# 1. Fetch the last 1 year of daily adjusted closing prices
print(f"Fetching data for {len(tickers)} tickers...")
data = yf.download(tickers, period='1y')['Close']

# Calculate daily percentage returns
returns = data.pct_change().dropna()

# 2. Generate the Correlation Matrix
correlation_matrix = returns.corr()

# Plotting the heatmap for visual analysis
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt=".2f")
plt.title("Correlation Matrix of Shortlisted Stocks")
plt.tight_layout()
plt.show()

# 3. Calculate Risk & Volatility Metrics
# Annualized Volatility (Daily standard deviation scaled to 252 trading days)
annual_volatility = returns.std() * np.sqrt(252)

# Maximum Drawdown (The largest percentage drop from a peak)
cumulative_returns = (1 + returns).cumprod()
rolling_max = cumulative_returns.cummax()
drawdown = (cumulative_returns - rolling_max) / rolling_max
max_drawdown = drawdown.min()

# 4. Compile and display the risk report
risk_metrics = pd.DataFrame({
    'Annual Volatility (%)': annual_volatility * 100,
    'Max Drawdown (%)': max_drawdown * 100
}).round(2).sort_values(by='Annual Volatility (%)')

print("\n--- Risk & Volatility Report ---")
print(risk_metrics)