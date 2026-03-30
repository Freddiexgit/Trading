import yfinance as yf
import pandas as pd
import numpy as np
from analytics import industry_score as iscore
from collections import defaultdict

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1500)
pd.options.display.max_colwidth = None
benchmark = "SPY"

# Reverse dict: {industry: ETF} → {ETF: industry}
ETF_TO_SECTOR = defaultdict(list)
for industry, etf in iscore.SECTOR_ETF.items():
    ETF_TO_SECTOR[etf].append(industry)

tickers = list(ETF_TO_SECTOR.keys()) + [benchmark]
def run_sector_rotation(output_file):
    print("Fetching sector data...")
    data = yf.download(tickers, period="6mo")

    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]

    # ------------------------------------------------------------
    # 2. RELATIVE STRENGTH (RS) AND MOMENTUM
    # ------------------------------------------------------------

    # RS = sector / SPY
    rs = close.div(close[benchmark], axis=0)

    # Smooth RS to reduce noise
    rs_smooth = rs.ewm(span=5).mean()

    # Momentum windows
    roc_2  = rs_smooth.pct_change(2).iloc[-1] * 100
    roc_5  = rs_smooth.pct_change(5).iloc[-1] * 100
    roc_10 = rs_smooth.pct_change(10).iloc[-1] * 100
    roc_20 = rs_smooth.pct_change(20).iloc[-1] * 100
    roc_60 = rs_smooth.pct_change(60).iloc[-1] * 100

    # ------------------------------------------------------------
    # 3. OBV AND CMF (VOLUME-BASED FLOWS)
    # ------------------------------------------------------------

    # OBV
    price_sign = np.sign(close.diff())
    obv = (price_sign * volume).fillna(0).cumsum()
    obv_20 = obv.pct_change(20).iloc[-1] * 100

    # CMF
    mfm = ((close - low) - (high - close)) / (high - low)
    mfm = mfm.replace([np.inf, -np.inf], np.nan).fillna(0)

    mfv = mfm * volume
    cmf = (mfv.rolling(20).sum() / volume.rolling(20).sum()).iloc[-1]
    cmf = cmf.replace([np.inf, -np.inf], np.nan).fillna(0)

    # ------------------------------------------------------------
    # 4. BUILD RAW FACTOR TABLE
    # ------------------------------------------------------------

    df = pd.DataFrame({
        "3M": roc_60,
        "1M": roc_20,
        "10D": roc_10,
        "5D": roc_5,
        "2D": roc_2,
        "OBV_20": obv_20,
        "CMF_20": cmf
    })

    df = df.drop(index=benchmark)  # remove SPY

    df["Accel"] = df["5D"] - df["10D"]

    # ------------------------------------------------------------
    # 5. NORMALIZATION (Z-SCORES)
    # ------------------------------------------------------------

    def zscore(s):
        return (s - s.mean()) / s.std()

    z = pd.DataFrame({
        "z60": zscore(df["3M"]),
        "z20": zscore(df["1M"]),
        "zacc": zscore(df["Accel"]),
        "zcmf": zscore(df["CMF_20"]),
        "zobv": zscore(df["OBV_20"])
    })

    # ------------------------------------------------------------
    # 6. WEIGHTED COMPOSITE SCORE
    # ------------------------------------------------------------

    df["Score"] = (
        0.40 * z["z60"] +
        0.20 * z["z20"] +
        0.20 * z["zacc"] +
        0.10 * z["zcmf"] +
        0.10 * z["zobv"]
    )

    # ------------------------------------------------------------
    # 7. ADD SECTOR NAMES
    # ------------------------------------------------------------

    df["Industry"] = df.index.map(lambda t: ETF_TO_SECTOR.get(t, t))

    # ------------------------------------------------------------
    # 8. FINAL RANKING
    # ------------------------------------------------------------

    ranked = df.sort_values("Score", ascending=False).round(2)

    ranked.to_csv(output_file, index=True)
    # print("\n--- Sector Rotation Ranking ---")
    # print(ranked)
