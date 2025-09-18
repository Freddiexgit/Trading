import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# Download stock data

def order_by_ema(input_file, output_file, span=60):
    ticker_and_slopes = {}
    df_tickers = pd.read_csv(input_file)
    for index, row in df_tickers.iterrows():
        ticker = row['symbol']
        val = order(ticker, span)
        ticker_and_slopes[ticker]=  val

    sorted_dict = dict(sorted(ticker_and_slopes.items(), key=lambda item: item[1],reverse=True))
    with open(output_file, 'w') as f:
        f.write('symbol\n')
        for key, value in sorted_dict.items():
            f.write(f'{key}\n')

def order(ticker, span=60):
    data = yf.download(ticker, period="2mo", interval="1d")

    # Compute EMA60
    data["EMA60"] = data["Close"].ewm(span=span, adjust=False).mean()

    # Rolling regression slope (20-day window)
    N = span
    ema = data["EMA60"].dropna().values
    slopes = []

    for i in range(N, len(ema)):
        xi = np.arange(N).reshape(-1, 1)
        yi = ema[i - N:i]
        model = LinearRegression().fit(xi, yi)
        slopes.append(model.coef_[0])

    # Align with dataframe
    data["EMA60_RegSlope"] = [None] * (len(data) - len(slopes)) + slopes

    data = data.iloc[-5:]
    val = data["EMA60_RegSlope"].mean()
    return val

if __name__ == "__main__":
    order("SNDK", 5)