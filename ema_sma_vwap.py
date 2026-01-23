import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Download 6 months of Apple stock data
ticker = "AAPL"
data = yf.download(ticker, period="6mo", interval="1d")
data = data.droplevel(axis=1, level=1) if isinstance(data.columns, pd.MultiIndex) else data
# --- Moving Averages ---
data["SMA_50"] = data["Close"].rolling(window=50).mean()
data["EMA_12"] = data["Close"].ewm(span=12, adjust=False).mean()
data["EMA_26"] = data["Close"].ewm(span=50, adjust=False).mean()

# --- VWAP Calculation ---
# VWAP = cumulative(sum(price * volume)) / cumulative(sum(volume))
data["Typical_Price"] = (data["High"] + data["Low"] + data["Close"]) / 3
data["VWAP"] = (data["Typical_Price"] * data["Volume"]).cumsum() / data["Volume"].cumsum()

fig, ax1 = plt.subplots(figsize=(14,7))

# Price + indicators
ax1.plot(data.index, data["Close"], label="Close Price", alpha=0.7)
ax1.plot(data.index, data["SMA_50"], label="50-day SMA", linestyle="--")
ax1.plot(data.index, data["EMA_12"], label="12-day EMA")
ax1.plot(data.index, data["EMA_26"], label="26-day EMA")
ax1.plot(data.index, data["VWAP"], label="VWAP", linestyle=":")

ax1.set_title(f"{ticker} - Price, SMA, EMA, VWAP with Volume")
ax1.set_ylabel("Price (USD)")
ax1.legend(loc="upper left")
ax1.grid(True)

# Volume on secondary axis
ax2 = ax1.twinx()
ax2.bar(data.index, data["Volume"], color="lightgray", alpha=0.4, label="Volume")
ax2.set_ylabel("Volume")
ax2.legend(loc="upper right")

plt.show()