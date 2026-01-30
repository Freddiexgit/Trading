import yfinance as yf
import pandas as pd
import data_downloader as data
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

### Copiot version
def detect_ema_converge_diverge(ticker, period="1mo", converge_thresh=0.002, diverge_thresh=0.01):
    try:
        df = data.get_transaction_df(ticker, period=period, interval="4h")
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")
        return pd.DataFrame()
    if df.empty:
        return pd.DataFrame()
    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df

    # --- Compute EMAs ---
    df["EMA5"] = df["Close"].ewm(span=5, adjust=False).mean()
    df["EMA10"] = df["Close"].ewm(span=10, adjust=False).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

    # --- EMA spread (max-min of the 3 EMAs) ---
    df["EMA_range"] = df[["EMA5", "EMA10", "EMA20"]].max(axis=1) - \
                      df[["EMA5", "EMA10", "EMA20"]].min(axis=1)

    # Remove first row (all EMAs equal)
    df = df.iloc[1:].copy()

    # --- Convergence & divergence conditions ---
    df["Converged"] = df["EMA_range"] < df["EMA10"] * converge_thresh
    df["Diverged"]  = df["EMA_range"] > df["EMA10"] * diverge_thresh

    # --- Must have at least one convergence ---
    if not df["Converged"].any():
        return pd.DataFrame()

    # --- Find last convergence ---
    last_converge_idx = df[df["Converged"]].index[-1]

    # --- Look ONLY after last convergence for divergence ---
    df_after = df.loc[last_converge_idx:]

    if not df_after["Diverged"].any():
        return pd.DataFrame()

    first_diverge_idx = df_after[df_after["Diverged"]].index[0]

    # --- Trend confirmation (bullish) ---
    latest_ema5 = df.iloc[-1]["EMA5"]
    latest_ema20 = df.iloc[-1]["EMA20"]

    if latest_ema5 > latest_ema20:
        return df.loc[last_converge_idx:first_diverge_idx]

    return pd.DataFrame()



# def detect_ema_converge_diverge(ticker, period="1mo", converge_thresh=0.005, diverge_thresh=0.03):
#     # Download historical data
#     try:
#         df = data.get_transaction_df(ticker, period=period, interval="4h")
#     except Exception as e:
#         print(f"Error downloading data for {ticker}: {e}")
#         return pd.DataFrame()
#     if df.empty:
#         return pd.DataFrame()
#     df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
#     # df.dropna(inplace=True)
#
#     # Compute EMAs
#     df["EMA5"] = df["Close"].ewm(span=5, adjust=False).mean()
#     df["EMA10"] = df["Close"].ewm(span=10, adjust=False).mean()
#     df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
#
#     # Distance between EMAs
#     df["EMA_range"] = df[["EMA5", "EMA10", "EMA20"]].max(axis=1) - df[["EMA5", "EMA10", "EMA20"]].min(axis=1)
#     df.drop(index=df.index[0], inplace=True) ## remove first row as ema have same values
#     # Define conditions
#     df["Converged"] = df["EMA_range"] < df["EMA10"] * converge_thresh
#     df["Diverged"] = df["EMA_range"] > df["EMA10"] * diverge_thresh
#     # print(df)
#     if len(df[df['Converged']])> 0 and len(df[df['Diverged']])>0:
#         last_converge = df[df['Converged']].index[-1]
#
#         print(last_converge)
#         # Filter only rows AFTER last convergence
#         df_after = df.loc[last_converge:]
#         first_diverge = None
#         # Now find divergence AFTER convergence
#         if df_after['Diverged'].any():
#             first_diverge = df_after[df_after['Diverged']].index[0]
#
#         # first_diverge = df[df['Diverged']].index[0]
#         latest_ema5 = df.iloc[-1]['EMA5']
#         latest_ema20 = df.iloc[-1]['EMA20']
#         if first_diverge is not None and last_converge < first_diverge and latest_ema5 > latest_ema20:
#              # print(df)
#             return df
#
#     return pd.DataFrame()



# Example usage
def call(input_file, output_file):
    df = pd.read_csv(f'resource/{input_file}')
    tickers = df['symbol'].dropna().tolist()
    result = []
    for ticker in tickers:
        df = detect_ema_converge_diverge(ticker)
        # print(df)
        if len(df) > 0:
            result.append(ticker)

    df2 = pd.DataFrame(result, columns=['symbol']).drop_duplicates()
    df2.to_csv(f'{output_file}', index=False)

if __name__ == "__main__":
    df = detect_ema_converge_diverge("WDC")
    print(df)