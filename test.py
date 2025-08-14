import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# response = requests.get("https://scanner.tradingview.com/newzealand/scan?label-product=markets-screener")
# response = requests.get("https://www.tradingview.com/markets/stocks-new-zealand/market-movers-all-stocks/")

# print(response.json())
#
# soup = BeautifulSoup(response.content, 'html.parser')
#
# table = soup.find('table')


# ticker = "AAPL"  # example: Apple Inc.
# data = yf.download(ticker, period="7d", interval="1d")
# data['Raw_Change'] = data['Close'].diff()
# print(data)

# import os
# def rename_files_recursively(directory):
#     for root, dirs, files in os.walk(directory):
#         for filename in files:
#                 old_path = os.path.join(root, filename)
#                 if filename.endswith('.txt'):  #or filename.endswith('.txt'):
#                     base = filename.rsplit('.', 1)[0]  # Remove last two extensions
#
#                     new_path = os.path.join(root, base)
#                     os.rename(old_path, new_path)
#                     print(f"Renamed: {old_path} → {new_path}")
#     for dir in dirs:
#         rename_files_recursively(dir)
#
# # Example usage
# rename_files_recursively('/Users/freddie/Documents/code/nztdai-nexus-backend - Copy')

import pandas as pd

# s = pd.Series([10, 20, 30], index=['a', 'b', 'c'])
# print(s)
# df = pd.DataFrame({
#     'Open': [100, 105, 102],
#     'Close': [98, 107, 101],
#     'Volume': [2000, 1500, 1800]
# })
# print(df['Open'])
#
# x = df.loc[df['Close'] < df['Open'], 'Volume']
# print(x)

import pandas as pd

# url = "https://snowflake-workshop-lab.s3.amazonaws.com/japan/citibike-trips/japan/citibike-trips/trips_2013_0_4_0.csv.gz"
#
# # Local file name to save
# local_filename = "2021-01.csv"
#



# import boto3
# from botocore import UNSIGNED
# from botocore.config import Config
#
# # Create the client with unsigned config
# s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))

# List objects in the folder
# response = s3.list_objects_v2(
#     Bucket='snowflake-workshop-lab',
#     Prefix='weather-nyc'
# )
#
# # Print file names
# for obj in response.get('Contents', []):
#     print(obj['Key'])

# s3.download_file(
#     Bucket='snowflake-workshop-lab',
#     Key='weather-nyc/weather_0_0_0.json.gz',
#     Filename='weather_0_0_0.json.gz'
# )



import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
# Data dictionary


# Create DataFrame with MultiIndex columns
index = pd.to_datetime([
    "2025-07-18",
    "2025-07-21",
    "2025-07-22",
    "2025-07-23",
    "2025-07-24"
])

columns = pd.MultiIndex.from_tuples([

    ("Close", "TSLA"),
    ("High",  "TSLA"),
    ("Low",   "TSLA"),
    ("Open",  "TSLA"),
    ("Volume","TSLA"),

])



# Add MA50 to the data dictionary
df = pd.DataFrame(
    [
        [329.649994, 330.899994, 321.420013, 321.660004, 94255000],
        [328.489990, 338.000000, 326.880005, 334.399994, 75768800],
        [332.109985, 335.410004, 321.549988, 329.739990, 77370400],
        [332.559998, 336.200012, 328.670013, 330.899994, 92553800],
        [305.299988, 310.149994, 300.410004, 310.000000,156966000],
    ],
    index=pd.Index(index, name="Date"),
    columns=columns
)
df.columns.names = ["Price", "Ticker"]

# print(df)
# ticker = "TSLA"
# print(df["Open",ticker])
# print("=======")
# print(df.loc[:, ("Open", slice(None))])


# Price            Close        High         Low        Open     Volume
# Ticker            TSLA        TSLA        TSLA        TSLA       TSLA
# Date
# 2025-07-14  316.899994  322.600006  312.670013  317.730011   78043400
# 2025-07-15  310.779999  321.200012  310.500000  319.679993   77556300
# 2025-07-16  321.670013  323.500000  312.619995  312.799988   97284800
# 2025-07-17  319.410004  324.339996  317.059998  323.149994   73922900
# 2025-07-18  329.649994  330.899994  321.420013  321.660004   94255000
# 2025-07-21  328.489990  338.000000  326.880005  334.399994   75768800
# 2025-07-22  332.109985  335.410004  321.549988  329.739990   77370400
# 2025-07-23  332.559998  336.200012  328.670013  330.899994   92553800


import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Example: create a second dataset (pretend TSLA and AAPL)
df1 = df.copy()
df1.columns = df1.columns.droplevel("Ticker")

df2 = df.copy() * 1.05  # fake different stock data
df2.columns = df2.columns.droplevel("Ticker")

# Create 2-row subplot layout (shared x-axis optional)
# fig = make_subplots(
#     rows=2, cols=1,
#     shared_xaxes=True,
#     vertical_spacing=0.05,
#     subplot_titles=("TSLA", "AAPL")
# )
#
# # TSLA chart
# fig.add_trace(
#     go.Candlestick(
#         x=df1.index,
#         open=df1["Open"],
#         high=df1["High"],
#         low=df1["Low"],
#         close=df1["Close"],
#         name="TSLA"
#     ),
#     row=1, col=1
# )
#
# # AAPL chart
# fig.add_trace(
#     go.Candlestick(
#         x=df2.index,
#         open=df2["Open"],
#         high=df2["High"],
#         low=df2["Low"],
#         close=df2["Close"],
#         name="AAPL"
#     ),
#     row=2, col=1
# )
#
# fig.update_layout(
#     height=800,
#     title="Multiple Candlestick Charts",
#     xaxis_rangeslider_visible=False,
#    xaxis2_rangeslider_visible = False  # also turn off for second subplot
# )
#
# fig.show()

df_plot = df.copy()
df_plot.columns = df_plot.columns.droplevel("Ticker")

# --- Technical Indicators ---

# EMA
df_plot["EMA20"] = df_plot["Close"].ewm(span=20, adjust=False).mean()
df_plot["EMA50"] = df_plot["Close"].ewm(span=50, adjust=False).mean()

# MACD
ema12 = df_plot["Close"].ewm(span=12, adjust=False).mean()
ema26 = df_plot["Close"].ewm(span=26, adjust=False).mean()
df_plot["MACD"] = ema12 - ema26
df_plot["Signal"] = df_plot["MACD"].ewm(span=9, adjust=False).mean()

# df_plot['Histogram'] = df_plot['MACD'] - df['Signal']

# plt.plot(df.index, df['MACD'], label='MACD', color='blue')
# plt.plot(df.index, df['Signal'], label='Signal Line', color='red')
# plt.bar(df.index, df['Histogram'], label='Histogram', color='gray')
# df['Turning Point'] = ((df['Histogram'] < 0) & (df['Histogram'].shift(-1) > 0)).astype(int)
# df['blow_0'] = np.where(df['Turning Point'] > 0, 1, 0)
# plt.plot(df['MACD'][df['blow_0'] == 1].index, df['MACD'][df['blow_0'] == 1], '^', markersize=10, color='g',
#      label='Buy Signal')
# RSI
delta = df_plot["Close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df_plot["RSI"] = 100 - (100 / (1 + rs))

# --- Build Subplots ---
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    row_heights=[0.5, 0.25, 0.25],
    subplot_titles=("Candlestick + EMA", "MACD", "RSI")
)

# Candlestick
fig.add_trace(go.Candlestick(
    x=df_plot.index,
    open=df_plot["Open"],
    high=df_plot["High"],
    low=df_plot["Low"],
    close=df_plot["Close"],
    name="Candlestick"
), row=1, col=1)

# EMA lines
fig.add_trace(go.Scatter(
    x=df_plot.index, y=df_plot["EMA20"], mode="lines",
    name="EMA20", line=dict(color="blue")
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=df_plot.index, y=df_plot["EMA50"], mode="lines",
    name="EMA50", line=dict(color="orange")
), row=1, col=1)

# MACD & Signal
fig.add_trace(go.Scatter(
    x=df_plot.index, y=df_plot["MACD"], mode="lines",
    name="MACD", line=dict(color="green")
), row=2, col=1)

fig.add_trace(go.Scatter(
    x=df_plot.index, y=df_plot["Signal"], mode="lines",
    name="Signal", line=dict(color="red")
), row=2, col=1)

# RSI
fig.add_trace(go.Scatter(
    x=df_plot.index, y=df_plot["RSI"], mode="lines",
    name="RSI", line=dict(color="purple")
), row=3, col=1)

# RSI overbought/oversold lines
fig.add_hline(y=70, line_dash="dash", line_color="gray", row=3, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="gray", row=3, col=1)

# Layout tweaks
fig.update_layout(
    height=900,
    title="TSLA Technical Analysis",
    xaxis_rangeslider_visible=False,
    xaxis2_rangeslider_visible=False,
    xaxis3_rangeslider_visible=False
)

fig.show()