import yfinance as yf
import pandas as pd


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def daily_screener_v2(tickers):
    results = []
    for symbol in tickers:
        try:
            # Get 40 days to support 14-day indicators
            df = yf.download(symbol, period="40d", interval="1d", progress=False)
            if len(df) < 20: continue

            # 1. Standard Metrics
            last_close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            pct_change = ((last_close - prev_close) / prev_close) * 100

            # 2. Relative Volume
            rel_vol = df['Volume'].iloc[-1] / df['Volume'].tail(20).mean()

            # 3. RSI (using the correct EWM method)
            df['RSI'] = calculate_rsi(df['Close'])
            current_rsi = df['RSI'].iloc[-1]

            # 4. Buying Pressure Proxy (Closing Position)
            # High value means buyers dominated the 'Ask' all day
            day_high = df['High'].iloc[-1]
            day_low = df['Low'].iloc[-1]
            buy_pressure = (last_close - day_low) / (day_high - day_low) if day_high != day_low else 0

            results.append({
                "Ticker": symbol,
                "Price": round(float(last_close), 2),
                "Change %": round(float(pct_change), 2),
                "Rel Vol": round(float(rel_vol), 2),
                "RSI": round(float(current_rsi), 2),
                "Buy Pressure": round(float(buy_pressure), 2)  # 0 to 1 scale
            })
        except:
            continue

    res_df = pd.DataFrame(results)

    # --- UPDATED SCREENING CRITERIA ---
    # Change > 2%, Rel Vol > 1.5, RSI < 70, Buy Pressure > 0.7 (Closed in top 30% of day)
    picks = res_df[
        (res_df['Change %'] > 2.0) &
        (res_df['Rel Vol'] > 1.5) &
        (res_df['RSI'] < 70) &
        (res_df['Buy Pressure'] > 0.7)
        ]

    return picks.sort_values(by="Buy Pressure", ascending=False)


# Test
watchlist = ["TSLA", "NVDA", "AMD", "AAPL", "MSFT", "COIN", "MARA"]
print(daily_screener_v2(watchlist))