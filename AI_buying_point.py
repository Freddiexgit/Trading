import pandas as pd
import numpy as np
import  data_downloader as dd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

def identify_buy_signals(df) -> pd.DataFrame:

    # --- Technical Indicators ---
    # Use EMA for faster reaction to recent price changes
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()

    # MACD Setup
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_DIF'] = exp1 - exp2
    df['MACD_DEA'] = df['MACD_DIF'].ewm(span=9, adjust=False).mean()

    # Event: MACD Bullish Crossover
    df['MACD_Cross'] = (df['MACD_DIF'] > df['MACD_DEA']) & (df['MACD_DIF'].shift(1) <= df['MACD_DEA'].shift(1))

    # RSI (Wilder's Smoothing)
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    df['RSI'] = 100 - (100 / (1 + (avg_gain / avg_loss)))

    # --- New Improvement: Volatility Filter (ATR or Bollinger) ---
    # Avoid signals during 'Squeeze' or 'Extremely High Volatility'
    df['Std_Dev'] = df['Close'].rolling(20).std()
    df['Upper_Band'] = df['EMA20'] + (df['Std_Dev'] * 2)

    # Only buy if there's room to grow (Price is not already touching the Upper Band)
    df['Room_To_Grow'] = df['Close'] < df['Upper_Band']

    # --- Signal Logic Integration ---
    # Added: Check if MACD is actually below 0 (Oversold start) for higher probability
    buy_conditions = (
            (df['EMA20'] > df['SMA50']) &  # Trend Alignment
            (df['MACD_Cross']) &  # Momentum Event
            (df['RSI'].between(30, 70)) &  # Healthy Momentum (not overbought)
            (df['Volume'] > df['Volume'].rolling(20).mean()) &  # Volume Support
            (df['SMA50'] > df['SMA50'].shift(1)) &  # Upward Sloping Trend
            (df['Room_To_Grow'])  # Volatility Check
    )

    df['Buy_Signal'] = buy_conditions.astype(int)
    df['Entry_Point'] = (df['Buy_Signal'] == 1) & (df['Buy_Signal'].shift(1) == 0)
    df = df.iloc[-3:].copy()
    df['Signal_Active'] = df['Entry_Point'].rolling(window=3).max().fillna(0).astype(bool)

    active_signals = df[df['Signal_Active'] == True]
    return active_signals


def run_ai_buying_point(input_file, output_file):
    df = pd.read_csv(input_file)
    result = []
    tickers = df['symbol'].dropna().tolist()
    for ticker in tickers:
        df = dd.get_transaction_df(ticker).copy()
        ind = identify_buy_signals(df)
        if len(ind) > 0:
            result.append(ticker)
    if len(result)> 0:
        df2 = pd.DataFrame(result, columns=['symbol']).drop_duplicates()
        df2.to_csv(f'{output_file}', index=False)

if __name__ == "__main__":
    # Example usage

    run_ai_buying_point("resource/nyse_and_nasdaq_top_500.csv", "output/2026-02-10/us/nyse_and_nasdaq_top_500/ai_buying_points.csv")
