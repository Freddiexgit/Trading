import yfinance as yf
import pandas as pd
import numpy as np
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
# -----------------------------
# Helper functions
# -----------------------------
def safe_float(x):
    try:
        return float(x)
    except:
        return np.nan

def normalize(series):
    if series.max() == series.min():
        return series.fillna(0)
    return 100 * (series - series.min()) / (series.max() - series.min())

# -----------------------------
# Major US semiconductor tickers
# -----------------------------
df = pd.read_csv("../resource/industries/Semiconductors.csv")

# SOXX ETF for relative momentum
soxx = yf.Ticker("SOXX")
soxx_hist = soxx.history(period="6mo")["Close"]
soxx_return = soxx_hist.iloc[-1]/soxx_hist.iloc[0] - 1

# -----------------------------
# Collect stock data
# -----------------------------
rows = []

for t in df["symbol"]:
    try:
        stock = yf.Ticker(t)
        info = stock.info
    except Exception as e:
        print(f"Error fetching {t}: {e}")
        continue
    name= info.get("longName")
    sector= info.get("sector")
    industry= info.get("industry")
    marketCap= info.get("marketCap")
    # --- Core fundamental metrics ---
    rev_growth = safe_float(info.get("revenueGrowth"))
    gross_margin = safe_float(info.get("grossMargins"))
    op_margin = safe_float(info.get("operatingMargins"))
    fcf = safe_float(info.get("freeCashflow"))
    market_cap = safe_float(info.get("marketCap"))
    debt_to_equity = safe_float(info.get("debtToEquity"))

    # --- Fallback: compute revenue growth from quarterly financials if missing ---
    if np.isnan(rev_growth):
        try:
            fin = stock.financials.T  # columns = Revenue, Net Income, etc.
            rev_this = fin["Total Revenue"].iloc[0]
            rev_last = fin["Total Revenue"].iloc[1]
            rev_growth = (rev_this - rev_last) / rev_last
        except:
            rev_growth = 0

    # --- FCF margin ---
    fcf_margin = fcf / market_cap if fcf and market_cap else 0

    # --- Momentum vs SOXX ---
    try:
        price = stock.history(period="6mo")["Close"]
        momentum = (price.iloc[-1]/price.iloc[0] - 1) - soxx_return
    except:
        momentum = 0

    # --- EPS revision score ---
    try:
        eps_rev = stock.recommendations
        eps_rev = eps_rev.tail(30)
        upgrades = sum(eps_rev["To Grade"].str.contains("Buy|Outperform", na=False))
        downgrades = sum(eps_rev["To Grade"].str.contains("Sell|Underperform", na=False))
        eps_revision_score = upgrades - downgrades
    except:
        eps_revision_score = 0

    # --- Cycle weight (simplified) ---
    cycle_weight = 1
    if t in ["AMAT","LRCX","KLAC"]:
        cycle_weight = 1.2  # early-cycle equipment surge
    elif t in ["NVDA","AMD"]:
        cycle_weight = 1.1  # AI/data-center growth
    elif t in ["MU"]:
        cycle_weight = 1.0
    marketCap_str = str(round(market_cap / 1_000_000_000, 3)) + "B"
    rows.append([
        t,name,sector,industry,marketCap,marketCap_str , rev_growth, gross_margin, op_margin, fcf_margin,
        debt_to_equity, momentum, eps_revision_score, cycle_weight
    ])

# -----------------------------
# Build DataFrame
# -----------------------------
df = pd.DataFrame(rows, columns=[
    "Symbol","name","sector","industry","marketCap","marketCap_str","RevenueGrowth","GrossMargin","OpMargin",
    "FCFMargin","DebtToEquity","Momentum","EPSRevision","CycleWeight"
])

# -----------------------------
# Compute factor scores
# -----------------------------
df["GrowthScore"] = normalize(df["RevenueGrowth"].fillna(0))
df["ProfitScore"] = normalize((df["GrossMargin"].fillna(0) + df["OpMargin"].fillna(0))/2)
df["CashScore"] = normalize(df["FCFMargin"].fillna(0))
df["BalanceScore"] = normalize(-df["DebtToEquity"].fillna(100))  # penalize missing debt
df["MomentumScore"] = normalize(df["Momentum"].fillna(0))
df["EPSRevisionScore"] = normalize(df["EPSRevision"].fillna(0))

# -----------------------------
# Total weighted score with cycle adjustment
# -----------------------------
df["TotalScore"] = (
    0.25*df["GrowthScore"] +
    0.20*df["ProfitScore"] +
    0.15*df["CashScore"] +
    0.10*df["BalanceScore"] +
    0.15*df["MomentumScore"] +
    0.10*df["EPSRevisionScore"]
) * df["CycleWeight"].fillna(1)

# -----------------------------
# Sort and display
# -----------------------------
df = df.sort_values("TotalScore", ascending=False)
df.to_csv("../resource/industries/Semiconductors.csv", index=False)
