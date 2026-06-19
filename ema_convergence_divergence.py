import pandas as pd
import numpy as np
import data_downloader as dd


def calculate_adx(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm = np.where(
        (plus_dm > minus_dm) & (plus_dm > 0),
        plus_dm,
        0
    )

    minus_dm = np.where(
        (minus_dm > plus_dm) & (minus_dm > 0),
        minus_dm,
        0
    )

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder's Smoothing Technique is standard for ATR/ADX,
    # but keeping rolling mean for consistency with your original logic
    atr = tr.rolling(period).mean()

    plus_di = (
            100 *
            pd.Series(plus_dm, index=df.index).rolling(period).mean()
            / atr
    )

    minus_di = (
            100 *
            pd.Series(minus_dm, index=df.index).rolling(period).mean()
            / atr
    )

    # Prevent division by zero errors if plus_di + minus_di is 0
    di_sum = plus_di + minus_di
    dx = np.where(di_sum != 0, (abs(plus_di - minus_di) / di_sum) * 100, 0)
    dx = pd.Series(dx, index=df.index)

    adx = dx.rolling(period).mean()

    return adx


def detect_ema_convergence_divergence(
        ticker,
        period="18mo",
        min_score=7):
    try:
        # Download Asset Data
        df = dd.get_transaction_df(ticker, period=period)
        if df.empty or len(df) < 200:
            return pd.DataFrame()

        spy_df = dd.get_transaction_df("SPY", period=period)

        hyg_df = dd.get_transaction_df("HYG", period=period)


    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")
        return pd.DataFrame()

    # ---------------------------
    # EMA Calculations
    # ---------------------------
    df["EMA5"] = df["Close"].ewm(span=5).mean()
    df["EMA10"] = df["Close"].ewm(span=10).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    ema_cols = ["EMA5", "EMA10", "EMA20"]
    df["EMA_range"] = df[ema_cols].max(axis=1) - df[ema_cols].min(axis=1)

    # ---------------------------
    # ATR & Alignment Calculations
    # ---------------------------
    tr1 = df["High"] - df["Low"]
    tr2 = abs(df["High"] - df["Close"].shift())
    tr3 = abs(df["Low"] - df["Close"].shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    df["ATR20"] = tr.rolling(20).mean()
    df["EMA_range_ATR"] = df["EMA_range"] / df["ATR20"]

    df["Converged"] = df["EMA_range_ATR"] < 0.30
    df["Diverged"] = df["EMA_range_ATR"] > 0.80

    if not df["Converged"].any():
        return pd.DataFrame()

    last_converge = df[df["Converged"]].index[-1]
    after = df.loc[last_converge:]

    if not after["Diverged"].any():
        return pd.DataFrame()

    first_diverge = after[after["Diverged"]].index[0]

    # ---------------------------
    # Technical Indicators (RSI, ADX, BBW)
    # ---------------------------
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / 14).mean()
    avg_loss = loss.ewm(alpha=1 / 14).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    df["ADX"] = calculate_adx(df)

    ma20 = df["Close"].rolling(20).mean()
    std20 = df["Close"].rolling(20).std()
    df["BBW"] = ((ma20 + 2 * std20) - (ma20 - 2 * std20)) / ma20
    df["BBW_pctile"] = df["BBW"].rolling(252).rank(pct=True)

    # ---------------------------
    # Market & Sector Relative Strength
    # ---------------------------
    df["RS"] = df["Close"] / spy_df["Close"].reindex(df.index)
    risk_ratio = (hyg_df["Close"] / spy_df["Close"]).reindex(df.index)

    # ---------------------------
    # Scoring Signals Logic
    # ---------------------------
    momentum_ok = df["Close"].pct_change(20).iloc[-1] > 0
    rsi_ok = df["RSI"].iloc[-1] > 30
    bull_stack = df["EMA5"].iloc[-1] > df["EMA10"].iloc[-1] > df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1]
    price_above_20 = df["Close"].iloc[-1] > df["EMA10"].iloc[-1]
    breakout = df["Close"].iloc[-1] > df["High"].rolling(20).max().shift(1).iloc[-1]

    volume_surge = df["Volume"].iloc[-1] > 1.5 * df["Volume"].rolling(20).mean().iloc[-1]
    volume_dryup = df["Volume"].iloc[-10:-1].mean() < 0.8 * df["Volume"].rolling(50).mean().iloc[-1]

    # Bugfix: Handle edge-case where no down-days exist in past 10 periods
    down_days = df.loc[df["Close"] < df["Close"].shift(), "Volume"]
    down_volume_max = down_days.tail(10).max() if not down_days.empty else 0
    if pd.isna(down_volume_max):
        down_volume_max = 0

    pocket_pivot = (df["Volume"].iloc[-1] > down_volume_max) and (df["Close"].iloc[-1] > df["EMA10"].iloc[-1])
    rs_ok = df["RS"].iloc[-1] > df["RS"].rolling(20).mean().iloc[-1]
    risk_on = risk_ratio.iloc[-1] > risk_ratio.rolling(20).mean().iloc[-1]
    squeeze_ok = df["BBW_pctile"].iloc[-1] < 0.20

    adx_ok = df["ADX"].iloc[-10] < 20 and df["ADX"].iloc[-1] > df["ADX"].iloc[-5]
    recent = (df.index[-1] - first_diverge).days <= 10

    # ---------------------------
    # Final Compilation & Scoring
    # ---------------------------
    # ---------------------------
    # 1. Map Weights to Signals
    # ---------------------------
    signal_weights = {
        # Tier 1: Alpha Execution Triggers (High Weight)
        "pocket_pivot": {"val": pocket_pivot, "weight": 3.0},
        "breakout": {"val": breakout, "weight": 3.0},
        "volume_surge": {"val": volume_surge, "weight": 2.5},

        # Tier 2: Trend & Strength Confirmations (Medium Weight)
        "bull_stack": {"val": bull_stack, "weight": 1.5},
        "rs_ok": {"val": rs_ok, "weight": 1.5},
        "adx_ok": {"val": adx_ok, "weight": 1.5},
        "squeeze_ok": {"val": squeeze_ok, "weight": 1.0},
        "volume_dryup": {"val": volume_dryup, "weight": 1.0},

        # Tier 3: Environmental Baselines (Low Weight)
        "price_above_20": {"val": price_above_20, "weight": 0.5},
        "rsi_ok": {"val": rsi_ok, "weight": 0.5},
        "momentum_ok": {"val": momentum_ok, "weight": 0.5},
        "risk_on": {"val": risk_on, "weight": 0.5},
    }

    # ---------------------------
    # 2. Compute Dynamic Score
    # ---------------------------
    score = 0.0
    for signal_name, data in signal_weights.items():
        if data["val"]:
            score += data["weight"]

    # Rounding to prevent floating point anomalies (e.g., 7.0000000004)
    score = round(score, 2)

    # ---------------------------
    # 3. Result Compilation
    # ---------------------------
    # Adjust your min_score threshold to match your new max possible score (~16.5)
    if score >= min_score and recent:
        result = pd.DataFrame({
            "symbol": [ticker],
            "score": [score],
            "volumeRatio": [
                round(df["Volume"].iloc[-1] / df["Volume"].rolling(20).mean().iloc[-1], 2)
            ],
            "RSI": [round(df["RSI"].iloc[-1], 1)],
            "ADX": [round(df["ADX"].iloc[-1], 1)],
            "open": [round(df["Open"].iloc[-1], 2)],
            "close": [round(df["Close"].iloc[-1], 2)],

        })
        return result

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
    df2 = pd.DataFrame()
    for ticker in tickers:
        df = detect_ema_convergence_divergence(ticker)
        if not df.empty:
           df2 = pd.concat([df2, df], ignore_index=True)
    if not df2.empty:
        df2 = df2.sort_values(
            by=["score", "volumeRatio", "RSI"],
            ascending=[False, False, False]
        ).reset_index(drop=True)
        df2.to_csv(f'{output_file}', index=False)

if __name__ == "__main__":
    tickers = ["DRI",
               "SMBC",
               "HBAN",
               "HMN",
               "NMR",
               "FULT",
                "WSFS",
                "EWBC",
                "IPAR",
                "AIR",
                "DGX",
                "WBI"]
    df2 = pd.DataFrame()
    for ticker in tickers:
        df = detect_ema_convergence_divergence(ticker)
        df2 = pd.concat([df2, df], ignore_index=True).drop_duplicates()
    df2 = df2.sort_values(
        by=["score", "volumeRatio", "RSI"],
        ascending=[False, False, False]
    ).reset_index(drop=True)
    print(df2)