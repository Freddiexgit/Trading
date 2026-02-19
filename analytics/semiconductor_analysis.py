import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1200)

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def safe_float(x):
    try:
        return float(x)
    except:
        return np.nan

def normalize(series):
    series = series.replace([np.inf, -np.inf], np.nan)
    if series.max() == series.min():
        return series.fillna(0)
    return 100 * (series - series.min()) / (series.max() - series.min())

def compute_revenue_growth(stock):
    try:
        fin = stock.financials.T
        rev = fin["Total Revenue"]
        if len(rev) >= 2:
            return (rev.iloc[0] - rev.iloc[1]) / rev.iloc[1]
    except:
        pass
    return np.nan

def compute_fcf_margin(stock):
    try:
        cf = stock.cashflow.T
        fin = stock.financials.T
        fcf = cf["Free Cash Flow"].iloc[0]
        rev = fin["Total Revenue"].iloc[0]
        return fcf / rev if rev != 0 else np.nan
    except:
        return np.nan

def compute_roic(stock):
    """ROIC = EBIT / (Total Assets - Current Liabilities)"""
    try:
        fin = stock.financials.T
        bs = stock.balance_sheet.T
        ebit = fin["Ebit"].iloc[0]
        invested_capital = bs["Total Assets"].iloc[0] - bs["Total Current Liabilities"].iloc[0]
        return ebit / invested_capital if invested_capital != 0 else np.nan
    except:
        return np.nan

def compute_ev_ebitda(stock, info):
    try:
        ebitda = safe_float(info.get("ebitda"))
        market_cap = safe_float(info.get("marketCap"))
        debt = safe_float(info.get("totalDebt"))
        cash = safe_float(info.get("totalCash"))
        ev = market_cap + debt - cash
        return ev / ebitda if ebitda and ebitda > 0 else np.nan
    except:
        return np.nan

def compute_peg(info):
    try:
        pe = safe_float(info.get("trailingPE"))
        growth = safe_float(info.get("earningsQuarterlyGrowth"))
        return pe / (growth * 100) if pe and growth else np.nan
    except:
        return np.nan

def compute_capex_intensity(stock):
    try:
        cf = stock.cashflow.T
        fin = stock.financials.T
        capex = abs(cf["Capital Expenditures"].iloc[0])
        rev = fin["Total Revenue"].iloc[0]
        return capex / rev if rev != 0 else np.nan
    except:
        return np.nan

def compute_inventory_cycle(stock):
    """Inventory growth YoY — useful for memory & WFE cycle."""
    try:
        bs = stock.balance_sheet.T
        inv = bs["Inventory"]
        if len(inv) >= 2:
            return (inv.iloc[0] - inv.iloc[1]) / inv.iloc[1]
    except:
        pass
    return np.nan

def compute_multi_momentum(stock):
    try:
        hist = stock.history(period="1y")["Close"]
        if len(hist) < 250:
            return np.nan, np.nan, np.nan, np.nan, np.nan

        m1 = hist.iloc[-1] / hist.iloc[-21] - 1
        m3 = hist.iloc[-1] / hist.iloc[-63] - 1
        m6 = hist.iloc[-1] / hist.iloc[-126] - 1
        m12 = hist.iloc[-1] / hist.iloc[0] - 1
        vol = hist.pct_change().std() * np.sqrt(252)

        return m1, m3, m6, m12, m12 / vol if vol > 0 else np.nan
    except:
        return np.nan, np.nan, np.nan, np.nan, np.nan

# ---------------------------------------------------------
# Load tickers
# ---------------------------------------------------------
tickers = pd.read_csv("../resource/industries/Semiconductors.csv")["symbol"]

# ---------------------------------------------------------
# Collect data
# ---------------------------------------------------------
rows = []

for t in tickers:
    stock = yf.Ticker(t)

    try:
        info = stock.get_info()
    except:
        continue

    name = info.get("longName")
    sector = info.get("sector")
    industry = info.get("industry")
    market_cap = safe_float(info.get("marketCap"))

    # Fundamentals
    rev_growth = compute_revenue_growth(stock)
    gross_margin = safe_float(info.get("grossMargins"))
    op_margin = safe_float(info.get("operatingMargins"))
    fcf_margin = compute_fcf_margin(stock)
    debt_to_equity = safe_float(info.get("debtToEquity"))

    # Advanced fundamentals
    roic = compute_roic(stock)
    ev_ebitda = compute_ev_ebitda(stock, info)
    peg = compute_peg(info)
    capex_intensity = compute_capex_intensity(stock)
    inventory_cycle = compute_inventory_cycle(stock)

    # Momentum
    m1, m3, m6, m12, risk_adj_mom = compute_multi_momentum(stock)

    # AI exposure (simple heuristic)
    ai_weight = 1.0
    if t in ["NVDA", "AMD", "AVGO", "TSM"]:
        ai_weight = 1.2

    # Memory cycle
    memory_weight = 1.0
    if t in ["MU", "WDC", "STX"]:
        memory_weight = 1.15

    # WFE cycle
    wfe_weight = 1.0
    if t in ["AMAT", "LRCX", "KLAC", "ASML"]:
        wfe_weight = 1.25

    cycle_weight = ai_weight * memory_weight * wfe_weight

    rows.append([
        t, name, sector, industry, market_cap,
        rev_growth, gross_margin, op_margin, fcf_margin,
        debt_to_equity, roic, ev_ebitda, peg,
        capex_intensity, inventory_cycle,
        m1, m3, m6, m12, risk_adj_mom,
        cycle_weight
    ])

# ---------------------------------------------------------
# Build DataFrame
# ---------------------------------------------------------
cols = [
    "symbol","Name","Sector","Industry","MarketCap",
    "RevenueGrowth","GrossMargin","OpMargin","FCFMargin",
    "DebtToEquity","ROIC","EV_EBITDA","PEG",
    "CapexIntensity","InventoryCycle",
    "M1","M3","M6","M12","RiskAdjMomentum",
    "CycleWeight"
]

df = pd.DataFrame(rows, columns=cols)

# ---------------------------------------------------------
# Factor scoring
# ---------------------------------------------------------
df["GrowthScore"] = normalize(df["RevenueGrowth"])
df["ProfitScore"] = normalize((df["GrossMargin"] + df["OpMargin"]) / 2)
df["CashScore"] = normalize(df["FCFMargin"])
df["ROICScore"] = normalize(df["ROIC"])
df["ValuationScore"] = normalize(-df["EV_EBITDA"])  # lower EV/EBITDA = better
df["PEGScore"] = normalize(-df["PEG"])  # lower PEG = better
df["CapexScore"] = normalize(-df["CapexIntensity"])  # lower capex intensity = better
df["InventoryScore"] = normalize(-df["InventoryCycle"])  # falling inventory = good
df["MomentumScore"] = normalize(df["RiskAdjMomentum"])

# ---------------------------------------------------------
# Total score
# ---------------------------------------------------------
df["TotalScore"] = (
    0.20*df["GrowthScore"] +
    0.15*df["ProfitScore"] +
    0.10*df["CashScore"] +
    0.15*df["ROICScore"] +
    0.10*df["ValuationScore"] +
    0.05*df["PEGScore"] +
    0.05*df["CapexScore"] +
    0.05*df["InventoryScore"] +
    0.15*df["MomentumScore"]
) * df["CycleWeight"]

df = df.sort_values("TotalScore", ascending=False)
df.to_csv(f"../resource/industries/Semiconductors_{datetime.now().strftime('%Y-%m-%d')}.csv", index=False)
