import pandas as pd
import numpy as np
import yfinance as yf
import data_downloader as dd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)


def compute_rsi_ema(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing = EMA with alpha = 1/period
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi




def compute_momentum(series, window=20):
    return series.pct_change(window)


def rsi_momentum_combo(df,
                       rsi_period=14,
                       mom_window=20,
                       rsi_threshold=50):
    # --- Indicators ---
    df["RSI"] = compute_rsi_ema(df["Close"], period=rsi_period)
    df["MOM"] = compute_momentum(df["Close"], window=mom_window)

    # --- Signal Logic ---
    # Long when:
    #   1. RSI > midpoint (trend strength)
    #   2. Momentum > 0 (acceleration)
    df["Signal"] = 0
    df.loc[(df["RSI"] > rsi_threshold) & (df["MOM"] > 0), "Signal"] = 1

    # Exit when either condition breaks
    df.loc[(df["RSI"] < rsi_threshold) | (df["MOM"] < 0), "Signal"] = 0

    # --- Position (carry forward) ---
    df["Position"] = df["Signal"].replace(0, np.nan).ffill().fillna(0)

    # --- Returns ---
    df["Market_Return"] = df["Close"].pct_change()
    df["Strategy_Return"] = df["Position"] * df["Market_Return"]
    df["Equity_Curve"] = (1 + df["Strategy_Return"]).cumprod()
    df["Market_Curve"] = (1 + df["Close"].pct_change().fillna(0)).cumprod()
    return df


def run_momentum(file_name,output_file):

    df = pd.read_csv(file_name)
    tickers = df['symbol'].dropna().tolist()
    result = []
    for ticker in tickers:
        df1 = dd.get_transaction_df(ticker,period="10mo", interval="4h")


        if ~len(df1) > 20:
           continue

        df_r = rsi_momentum_combo(df1.copy())
        if (df_r["Position"].iloc[-1] ==1 and df_r["Position"].iloc[-2]==0):
            result.append(ticker)

    if len(result) > 0:
        df2 = pd.DataFrame(result, columns=['symbol']).drop_duplicates()
        df2.to_csv(f'{output_file}', index=False)

if __name__ == "__main__":
    # ticker = "SIDU"
    # start_date = "2023-11-01"
    # df = yf.download(ticker, start=start_date)
    #
    # result_df = rsi_momentum_combo(df)
    #
    # print(result_df.tail())

    run_momentum(f"resource/my_watch_list.csv",
                 output_file = f"output/2026-2-01/us/my_vip/momentum_combo.csv")