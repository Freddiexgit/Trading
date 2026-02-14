import yfinance as yf
import pandas as pd
import data_downloader as  dd

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

def bid_ask_screener(file_name, output_file=None):
    df = pd.read_csv(file_name)
    tickers = df['symbol'].dropna().tolist()
    results = []
    for symbol in tickers:
        try:
            # Setting auto_adjust=True helps keep column names simple
            df = dd.get_transaction_df(symbol).copy()

            if df.empty or len(df) < 20:
                continue

            # Ensure we are working with 1D Series (handles multi-index if it occurs)
            close_series = df['Close'].squeeze()
            high_series = df['High'].squeeze()
            low_series = df['Low'].squeeze()
            vol_series = df['Volume'].squeeze()

            # 1. Standard Metrics
            last_close = float(close_series.iloc[-1])
            prev_close = float(close_series.iloc[-2])
            pct_change = ((last_close - prev_close) / prev_close) * 100

            # 2. Relative Volume
            rel_vol = float(vol_series.iloc[-1] / vol_series.tail(20).mean())

            # 3. RSI
            rsi_series = calculate_rsi(close_series)
            current_rsi = float(rsi_series.iloc[-1])

            # 4. Buying Pressure Proxy
            day_high = float(high_series.iloc[-1])
            day_low = float(low_series.iloc[-1])

            # Avoid division by zero if High == Low
            buy_pressure = (last_close - day_low) / (day_high - day_low) if day_high != day_low else 0

            results.append({
                "Ticker": symbol,
                "Price": round(last_close, 2),
                "Change %": round(pct_change, 2),
                "Rel Vol": round(rel_vol, 2),
                "RSI": round(current_rsi, 2),
                "Buy Pressure": round(buy_pressure, 2)
            })
        except Exception as e:
            print(f"Skipping {symbol}: {e}")
            continue

    # Create DataFrame
    res_df = pd.DataFrame(results)

    # Check if we actually found any data before filtering
    if res_df.empty:
        print("No data found for the provided tickers.")
        return res_df

    # --- UPDATED SCREENING CRITERIA ---
    picks = res_df[
        (res_df['Change %'] > 2.0) &
        (res_df['Rel Vol'] > 1.2) &
        (res_df['RSI'] < 70) &
        (res_df['Buy Pressure'] > 0.6)
        ]
    picks = picks.sort_values(by="Buy Pressure", ascending=False)
    return_tickers = picks['Ticker'].tolist()
    df2 = pd.DataFrame(return_tickers, columns=['symbol']).drop_duplicates()
    df2.to_csv(f'{output_file}', index=False)
    return picks



if __name__ == "__main__":
    df = pd.read_csv("resource/my_watch_list.csv")
    tickers = df['symbol'].dropna().tolist()
    picks = bid_ask_screener(tickers)
    print(picks)