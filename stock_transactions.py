import pandas as pd
import matplotlib.pyplot as plt
from alpaca.data import StockHistoricalDataClient, StockTradesRequest
from alpaca.data.timeframe import TimeFrame
import os

# --- Set your Alpaca API key ---
os.environ["APCA_API_KEY_ID"] = "PKNW0F5816WRZ5JM6UYP"
os.environ["APCA_API_SECRET_KEY"] = "deaiyhCRhthLfMK8q0oG9qkN1PJt9OuEbflxMxU9"

client = StockHistoricalDataClient(
    os.getenv("APCA_API_KEY_ID"),
    os.getenv("APCA_API_SECRET_KEY")
)

# --- Get intraday trades ---
request = StockTradesRequest(
    symbol_or_symbols=("COST"),
    start="2025-12-20T13:30:00Z",  # market open UTC
    end="2025-12-20T20:00:00Z",    # market close UTC
)
trades = client.get_stock_trades(request)
print(trades)
# Convert to DataFrame
df = pd.DataFrame([t.__dict__ for t in trades])
df["timestamp"] = pd.to_datetime(df["timestamp"])
df.set_index("timestamp", inplace=True)

# --- Tag buy/sell initiated trades ---
# If trade price >= ask → buyer-initiated
# If trade price <= bid → seller-initiated
df["buy_volume"] = df.apply(lambda x: x.size if x.price >= x.ask_price else 0, axis=1)
df["sell_volume"] = df.apply(lambda x: x.size if x.price <= x.bid_price else 0, axis=1)

# Aggregate per minute
agg = df.resample("1min").sum()[["buy_volume", "sell_volume"]]
agg["delta"] = agg["buy_volume"] - agg["sell_volume"]

print(agg.tail())

# --- Plot volume delta ---
plt.figure(figsize=(12,6))
plt.bar(agg.index, agg["delta"], color=agg["delta"].apply(lambda x: "green" if x > 0 else "red"))
plt.title("Intraday Volume Delta (AAPL)")
plt.ylabel("Buy - Sell Volume")
plt.show()