import yfinance as yf
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
def detect_ema_convergence_divergence(ticker, period="1mo", converge_thresh=0.5, diverge_thresh=2):
    # Download historical data
    df = yf.download(ticker, period=period, interval="1d")
    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    df.dropna(inplace=True)

    # Compute EMAs
    df["EMA5"] = df["Close"].ewm(span=5, adjust=False).mean()
    df["EMA10"] = df["Close"].ewm(span=10, adjust=False).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

    # Distance between EMAs
    df["EMA_range"] = df[["EMA5", "EMA10", "EMA20"]].max(axis=1) - df[["EMA5", "EMA10", "EMA20"]].min(axis=1)

    # Define conditions
    df["Converged"] = df["EMA_range"] < converge_thresh
    df["Diverged"] = df["EMA_range"] > diverge_thresh

    # Signal: converged yesterday, diverged today
    df["Converge_Diverge_Signal"] = df["Converged"].shift(1) & df["Diverged"]
    # print(df)
    return df[df["Converge_Diverge_Signal"]]

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

