# ============================================================
# Momentum + AVWAP Professional Screener (Single File)
# Combines:
# - Market regime filter
# - Relative strength leadership ranking
# - Volatility contraction detection
# - Anchored VWAP pullback execution
# - Risk-based position sizing
# ============================================================

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Optional, List, Tuple

import data_downloader

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1200)


# ============================================================
# DATA FETCH
# ============================================================

def fetch_price_data(ticker: str
                    ) -> pd.DataFrame:

    # df = yf.download(
    #     ticker,
    #     interval=interval,
    #     auto_adjust=False,
    #     progress=False
    # )
    df = data_downloader.get_transaction_df(ticker)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    if df.empty:
        raise ValueError(f"No data for {ticker}")

    df.index = pd.to_datetime(df.index)
    return df


# ============================================================
# MARKET REGIME FILTER
# ============================================================

def market_regime_ok(symbol="SPY") -> bool:
    spy = yf.download(symbol, period="1y", auto_adjust=True, progress=False)

    spy["MA50"] = spy["Close"].rolling(50).mean()
    spy["MA200"] = spy["Close"].rolling(200).mean()

    last_close = float(spy["Close"].iloc[-1])
    last_ma50 = float(spy["MA50"].iloc[-1])
    last_ma200 = float(spy["MA200"].iloc[-1])

    cond1 = last_close > last_ma50
    cond2 = last_ma50 > last_ma200

    return bool(cond1 and cond2)


# ============================================================
# LEADER SELECTION
# ============================================================

def relative_strength_score(df: pd.DataFrame) -> float:
    r3 = df["Close"].pct_change(63).iloc[-1]
    r6 = df["Close"].pct_change(126).iloc[-1]
    r12 = df["Close"].pct_change(252).iloc[-1]
    return 0.5 * r3 + 0.3 * r6 + 0.2 * r12


def is_leader(df: pd.DataFrame) -> bool:
    ma50 = df["Close"].rolling(50).mean()
    ma150 = df["Close"].rolling(150).mean()

    trend_ok = (
        df["Close"].iloc[-1] > ma50.iloc[-1] >
        ma150.iloc[-1]
    )

    near_high = (
        df["Close"].iloc[-1] >
        df["High"].rolling(60).max().iloc[-1] * 0.9
    )

    return bool(trend_ok and near_high)


def volatility_contracting(df: pd.DataFrame) -> bool:
    ranges = (df["High"] - df["Low"]) / df["Close"]
    recent = ranges.tail(5).mean()
    past = ranges.tail(30).mean()
    return bool(recent < past * 0.75)


# ============================================================
# AVWAP + INDICATORS
# ============================================================

def find_auto_anchor(df: pd.DataFrame, lookback_days: int = 252):
    recent_df = df.tail(lookback_days)
    if recent_df.empty:
        return df.index[0]
    return recent_df["Volume"].idxmax()


def anchored_vwap(df: pd.DataFrame, anchor_date: pd.Timestamp):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3.0
    tpv = tp * df["Volume"]

    mask = df.index >= anchor_date
    cum_tpv = tpv.where(mask).cumsum()
    cum_vol = df["Volume"].where(mask).cumsum()

    return cum_tpv.div(cum_vol)


def atr(df: pd.DataFrame, period=14):
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def compute_indicators(df: pd.DataFrame, anchor_date):
    df = df.copy()

    df["EMA_10"] = df["Close"].ewm(span=10, adjust=False).mean()
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["ATR_14"] = atr(df)
    df["AVWAP"] = anchored_vwap(df, anchor_date)

    return df


# ============================================================
# SETUP LOGIC (YOUR EDGE)
# ============================================================

def generate_signals(df: pd.DataFrame, avwap_tolerance=0.02):
    df = df.copy()

    df["Uptrend"] = df["EMA_10"] > df["EMA_20"]

    mask_avwap = df["AVWAP"].notna()

    df["Pullback_Zone"] = (
        (df["Low"] <= df["EMA_10"]) |
        (mask_avwap & (df["Low"] <= df["AVWAP"]))
    )

    df["Distance_to_AVWAP"] = np.where(
        mask_avwap,
        (df["Close"] - df["AVWAP"]).abs() / df["AVWAP"],
        np.nan
    )

    df["Close_Coiled"] = df["Distance_to_AVWAP"] <= avwap_tolerance

    df["Setup_Signal"] = (
        df["Uptrend"] &
        df["Pullback_Zone"] &
        df["Close_Coiled"]
    )

    return df


# ============================================================
# POSITION SIZING
# ============================================================

def position_sizing(df: pd.DataFrame,
                    capital=10000,
                    risk_per_trade=0.01,
                    stop_multiplier_atr=1.5):

    df = df.copy()

    dollar_risk = capital * risk_per_trade
    df["Proposed_Entry"] = df["Open"].shift(-1).fillna(df["Close"])

    atr_stop = df["Proposed_Entry"] - df["ATR_14"] * stop_multiplier_atr
    hard_stop = df["Proposed_Entry"] * 0.98

    df["Stop_Loss"] = np.maximum(atr_stop, hard_stop)

    df["Per_Share_Risk"] = (
        df["Proposed_Entry"] - df["Stop_Loss"]
    ).clip(lower=1e-6)

    df["Shares_to_Buy"] = np.floor(dollar_risk / df["Per_Share_Risk"])
    df.loc[~df["Setup_Signal"], "Shares_to_Buy"] = 0

    return df


# ============================================================
# FULL PIPELINE
# ============================================================

def run_avwap_strategy(ticker: str,
                       capital: float,
                       risk_per_trade: float):

    df = fetch_price_data(ticker)

    anchor = find_auto_anchor(df)

    df = compute_indicators(df, anchor)
    df = generate_signals(df)
    df = position_sizing(df, capital, risk_per_trade)

    return df


# ============================================================
# MAIN EXECUTION
# ============================================================

def run(source_file="resource/my_watch_list.csv", output_file = "avwap_setups.csv"):

    # if not market_regime_ok():
    #     print("Market regime weak — skipping scan.")
    #     exit()

    tickers = pd.read_csv(source_file)["symbol"].tolist()

    leader_pool: List[Tuple[str, float]] = []

    print("Scanning leaders...")

    for ticker in tickers:
        try:
            raw_df = fetch_price_data(ticker)

            if len(raw_df) < 252:
                continue

            if not is_leader(raw_df):
                continue

            if not volatility_contracting(raw_df):
                continue

            rs = relative_strength_score(raw_df)
            leader_pool.append((ticker, rs))

        except Exception as e:
            print(f"Leader scan error {ticker}: {e}")

    leader_pool.sort(key=lambda x: x[1], reverse=True)
    top_tickers = [t[0] for t in leader_pool[:20]]

    print(f"\nTop Leaders: {top_tickers}\n")
    result_df = None
    for ticker in top_tickers:
        try:
            results = run_avwap_strategy(
                ticker,
                capital=50000,
                risk_per_trade=0.015
            )

            setups = results[
                (results["Setup_Signal"]) &
                (results["Shares_to_Buy"] > 0)
            ]

            if not setups.empty:
                latest_setup_date = setups.index.max().tz_localize(None)
                today = pd.Timestamp.today().tz_localize(None)
                days_since_last_setup = (today - latest_setup_date).days

                # Updated condition
                if days_since_last_setup <= 5:
                    print(f"Latest setup was {days_since_last_setup} days ago. Displaying recent triggers:")
                    setups["symbol"] = ticker
                    if result_df is None:
                        result_df = setups.tail(1)
                    else:
                        result_df = pd.concat([result_df, setups.tail(1)], ignore_index=False)
                    # print(setups.tail(5))

        except Exception as e:
            print(f"Execution error {ticker}: {e}")
    if result_df is not None:
        result_df.to_csv(output_file,  index=False)
if __name__  =="__main__":
    run()