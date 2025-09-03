import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

def detect_morning_star(ticker, period="6mo"):
    # Download OHLC data
    df = yf.download(ticker, period=period, interval="1d")
    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    df.dropna(inplace=True)

    # --- Morning Star Conditions ---
    df["Bearish1"] = df["Close"].shift(2) < df["Open"].shift(2)
    df["SmallBody2"] = abs(df["Close"].shift(1) - df["Open"].shift(1)) <= 0.3 * abs(df["Open"].shift(2) - df["Close"].shift(2))
    df["Bullish3"] = df["Close"] > df["Open"]
    df["CloseAboveHalf"] = df["Close"] >= (df["Open"].shift(2) + df["Close"].shift(2)) / 2

    df["Morning_Star"] = df["Bearish1"] & df["SmallBody2"] & df["Bullish3"] & df["CloseAboveHalf"]

    return df

def plot_morning_star(df, ticker):
    fig = go.Figure()

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="Price"
    ))
    print(df)
    # Highlight Morning Star signals
    ms = df[df["Morning_Star"]]
    fig.add_trace(go.Scatter(
        x=ms.index,
        y=ms["Close"],
        mode="markers",
        marker=dict(size=14, color="purple", symbol="star"),
        name="Morning Star"
    ))

    # Layout
    fig.update_layout(
        title=f"{ticker} - Morning Star Detection",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_white"
    )

    fig.show()


def morning_star(input_file, output_file):
    df = pd.read_csv(f'resource/{input_file}')
    tickers = df['symbol'].dropna().tolist()
    has_morning_star = []
    for ticker in tickers:
        df = detect_morning_star(ticker)
        df = df['Morning_Star'][df['Morning_Star'] == True]
        # print(df)
        if len(df) > 0:
            has_morning_star.append(ticker)

    df2 = pd.DataFrame(has_morning_star, columns=['symbol']).drop_duplicates()
    df2.to_csv(f'{output_file}', index=False)


# --- Example ---

# plot_morning_star(df, ticker)