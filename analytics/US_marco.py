import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# -----------------------------
# CONFIG
# -----------------------------
start = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")

symbols = {
    "US10Y": "^TNX",      # 10-year yield (x10)
    "US02Y": "^IRX",      # 13-week T-bill (proxy for short rates)
    "DXY": "DX-Y.NYB",    # Dollar Index
    "VIX": "^VIX",        # Volatility Index
    "HYG": "HYG",         # High-yield credit ETF
    "CL": "CL=F",         # Crude oil futures
    "GC": "GC=F",         # Gold futures
    "HG": "HG=F",         # Copper futures
    "ES": "ES=F",         # S&P 500 futures
    "NQ": "NQ=F"          # Nasdaq futures
}

# -----------------------------
# DOWNLOAD DATA
# -----------------------------
def safe_download(ticker, start):
    """Always return a Series with a DateTime index."""
    df = yf.download(ticker, start=start)
    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    # If download failed → return empty Series with datetime index
    if df.empty or "Close" not in df:
        print(f"Warning: No data for {ticker}")
        return pd.Series(dtype=float)

    # Return the Close column as a proper Series
    return df["Close"].copy()

# Build dataset safely
data = {}
for name, ticker in symbols.items():
    s = safe_download(ticker, start)
    data[name] = s

# Combine into DataFrame (no scalar errors)
df = pd.concat(data, axis=1)

# Convert yields to proper % (TNX is x10)
df["US10Y"] = df["US10Y"] / 10

# Yield curve
df["YieldCurve"] = df["US10Y"] - df["US02Y"]

# -----------------------------
# MACRO REGIME SCORE
# -----------------------------
def score_series(series):
    if series.iloc[-1] > series.iloc[-20:].mean():
        return -1 if series.name in ["US10Y", "US02Y", "DXY", "VIX"] else 1
    else:
        return 1 if series.name in ["US10Y", "US02Y", "DXY", "VIX"] else -1

macro_score = sum([
    score_series(df["US10Y"]),
    score_series(df["US02Y"]),
    score_series(df["DXY"]),
    score_series(df["VIX"]),
    score_series(df["HYG"])
])

print(f"\nMACRO REGIME SCORE: {macro_score}")
print("Bullish" if macro_score > 0 else "Bearish" if macro_score < 0 else "Neutral")

# -----------------------------
# DASHBOARD LAYOUT
# -----------------------------
fig = make_subplots(
    rows=4, cols=2,
    subplot_titles=(
        "US10Y Yield", "US02Y Yield",
        "Yield Curve (10Y - 2Y)", "DXY",
        "VIX", "HYG (Credit)",
        "Commodities (Oil, Gold, Copper)", "ES & NQ Futures"
    )
)

# Row 1
fig.add_trace(go.Scatter(x=df.index, y=df["US10Y"], name="US10Y"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["US02Y"], name="US02Y"), row=1, col=2)

# Row 2
fig.add_trace(go.Scatter(x=df.index, y=df["YieldCurve"], name="Yield Curve"), row=2, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["DXY"], name="DXY"), row=2, col=2)

# Row 3
fig.add_trace(go.Scatter(x=df.index, y=df["VIX"], name="VIX"), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["HYG"], name="HYG"), row=3, col=2)

# Row 4: Commodities
commodities = df[["CL", "GC", "HG"]].copy()

normalized = (commodities - commodities.min()) / (commodities.max() - commodities.min())

# Plot normalized commodities
fig.add_trace(go.Scatter(
    x=df.index, y=normalized["CL"], name="Crude Oil (norm)"
), row=4, col=1)

fig.add_trace(go.Scatter(
    x=df.index, y=normalized["GC"], name="Gold (norm)"
), row=4, col=1)

fig.add_trace(go.Scatter(
    x=df.index, y=normalized["HG"], name="Copper (norm)"
), row=4, col=1)

# Row 4: ES/NQ
fig.add_trace(go.Scatter(x=df.index, y=df["ES"], name="ES"), row=4, col=2)
fig.add_trace(go.Scatter(x=df.index, y=df["NQ"], name="NQ"), row=4, col=2)

fig.update_layout(
    height=1400,
    width=1200,
    title_text="Macro Dashboard — Yields, Credit, Vol, Commodities, ES/NQ"
)

fig.show()
