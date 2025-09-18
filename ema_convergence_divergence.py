import yfinance as yf
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
def detect_ema_convergence_divergence(ticker, period="1mo", converge_thresh=0.005, diverge_thresh=0.03):
    # Download historical data
    try:
        df = yf.download(ticker, period=period, interval="1d")
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")
        return pd.DataFrame()
    if df.empty:
        return pd.DataFrame()
    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    df.dropna(inplace=True)

    # Compute EMAs
    df["EMA5"] = df["Close"].ewm(span=5, adjust=False).mean()
    df["EMA10"] = df["Close"].ewm(span=10, adjust=False).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

    # Distance between EMAs
    df["EMA_range"] = df[["EMA5", "EMA10", "EMA20"]].max(axis=1) - df[["EMA5", "EMA10", "EMA20"]].min(axis=1)
    df.drop(index=df.index[0], inplace=True) ## remove first row as ema have same values
    # Define conditions
    df["Converged"] = df["EMA_range"] < df["EMA10"] * converge_thresh
    df["Diverged"] = df["EMA_range"] > df["EMA10"] * diverge_thresh
    # print(df)
    if len(df[df['Converged']])> 0 and len(df[df['Diverged']])>0:
        last_converge = df[df['Converged']].index[-1]
        first_diverge = df[df['Diverged']].index[0]
        latest_ema5 = df.iloc[-1]['EMA5']
        latest_ema20 = df.iloc[-1]['EMA20']
        if last_converge < first_diverge and latest_ema5 > latest_ema20:
             # print(df)
            return df

    return pd.DataFrame()



# Example usage
def call(input_file, output_file):
    df = pd.read_csv(f'resource/{input_file}')
    tickers = df['symbol'].dropna().tolist()
    result = []
    for ticker in tickers:
        df = detect_ema_convergence_divergence(ticker)
        # print(df)
        if len(df) > 0:
            result.append(ticker)

    df2 = pd.DataFrame(result, columns=['symbol']).drop_duplicates()
    df2.to_csv(f'{output_file}', index=False)

if __name__ == "__main__":
    df = detect_ema_convergence_divergence("UI")
    print(df)