import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import linregress
from datetime import datetime

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)


# =========================================================
# 1. ROBUST HELPERS
# =========================================================
def safe_get(df, keys, default=0):
    """Try multiple keys in a dataframe index to find the data."""
    for key in keys:
        if key in df.index:
            return df.loc[key]
    return pd.Series([default] * 4)


def safe_div(n, d):
    return n / d if d and d != 0 and not np.isnan(d) else np.nan


def compute_trend_slope(series):
    if series is None or len(series.dropna()) < 2: return 0
    y = series.dropna().values[::-1]
    x = np.arange(len(y))
    try:
        slope, _, _, _, _ = linregress(x, y)
        return slope / (abs(y.mean()) + 1e-6)
    except:
        return 0


def sector_normalize(df, column, reverse=False):
    if df.empty or column not in df.columns: return pd.Series(0, index=df.index)

    def z_score(x):
        if len(x) <= 1 or x.std() == 0: return 0.0
        return (x - x.mean()) / x.std()

    z_vals = df.groupby("Sector")[column].transform(z_score).fillna(0).clip(-3, 3)
    if reverse: z_vals = -z_vals
    min_v, max_v = z_vals.min(), z_vals.max()
    if max_v == min_v: return z_vals.map(lambda x: 50.0)
    return 100 * (z_vals - min_v) / (max_v - min_v)


# =========================================================
# 2. ANALYSIS ENGINE
# =========================================================
def analyze_earnings_quality(q_fin, q_cf, q_bs):
    try:
        ni = safe_get(q_fin, ["Net Income", "Net Income Common Stockholders"])
        cfo = safe_get(q_cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
        assets = safe_get(q_bs, ["Total Assets"])

        accrual_ratio = safe_div((ni.iloc[0] - cfo.iloc[0]), assets.iloc[0])
        ni_slope = compute_trend_slope(ni.head(4))
        cfo_slope = compute_trend_slope(cfo.head(4))

        if ni_slope > 0.05 and cfo_slope < -0.05:
            return accrual_ratio, "🚨 DANGER (Divergence)", 0.50
        elif accrual_ratio > 0.10:
            return accrual_ratio, "⚠️ LOW (Accruals)", 0.85
        return accrual_ratio, "✅ HIGH", 1.0
    except:
        return 0.0, "❓ N/A", 1.0


class UniversalRadar:
    def __init__(self, tickers):
        self.tickers = tickers
        self.results = []

    def run_scan(self):
        print(f"📡 Scanning {len(self.tickers)} symbols...")
        for t in self.tickers:
            try:
                stock = yf.Ticker(t)
                q_fin = stock.quarterly_financials
                q_cf = stock.quarterly_cashflow
                q_bs = stock.quarterly_balance_sheet
                info = stock.info
                if q_fin.empty: raise ValueError("No Financials")

                sector = info.get("sector", "Other")

                # --- 1. Sector-Adaptive Quality ---
                if sector == "Financial Services":
                    quality_val = info.get("returnOnEquity", 0)
                    q_label = "ROE"
                else:
                    # Use soft-search for Operating Income
                    ebit_series = safe_get(q_fin, ["EBIT", "Operating Income"])
                    assets_series = safe_get(q_bs, ["Total Assets"])
                    liab_series = safe_get(q_bs, ["Total Current Liabilities"])
                    quality_val = safe_div(ebit_series.iloc[0], (assets_series.iloc[0] - liab_series.iloc[0]))
                    q_label = "ROIC"

                # --- 2. Trends & Value ---
                accrual_val, eq_flag, penalty = analyze_earnings_quality(q_fin, q_cf, q_bs)
                fcf_series = safe_get(q_cf, ["Free Cash Flow"])
                fcf_vel = compute_trend_slope(fcf_series.head(4))

                self.results.append({
                    "Symbol": t, "Sector": sector, "EQ_Flag": eq_flag, "Penalty": penalty,
                    "Quality_Val": quality_val, "Quality_Type": q_label,
                    "FCF_Velocity": fcf_vel, "PE": info.get("trailingPE", np.nan),
                    "EV_FCF": safe_div(info.get("enterpriseValue", 0), fcf_series.head(4).mean() * 4)
                })
                print(f"   Done: {t.ljust(5)} | {q_label}: {str(round(quality_val * 100, 1)) + '%':>6} | {eq_flag}")
            except Exception as e:
                print(f"   Skipped {t}: {e}")

        return self.process_rankings()

    def process_rankings(self):
        if not self.results: return pd.DataFrame()
        df = pd.DataFrame(self.results)
        df["Score_Quality"] = sector_normalize(df, "Quality_Val")
        df["Score_Trend"] = sector_normalize(df, "FCF_Velocity")
        df["Score_Value"] = (sector_normalize(df, "PE", reverse=True) + sector_normalize(df, "EV_FCF",
                                                                                         reverse=True)) / 2
        df["TotalScore"] = (0.40 * df["Score_Trend"] + 0.35 * df["Score_Quality"] + 0.25 * df["Score_Value"]) * df[
            "Penalty"]
        return df.sort_values("TotalScore", ascending=False)


if __name__ == "__main__":
    ticker_list = ["AAPL", "MSFT", "NVDA", "JPM", "GS", "COST", "WMT", "XOM", "PFE", "LLY"]
    final_df = UniversalRadar(ticker_list).run_scan()
    if not final_df.empty:
        print("\n" + "=" * 95)
        print(f"🏆 UNIVERSAL FUNDAMENTAL RADAR: TOP PICKS")
        print("=" * 95)
        print(final_df.groupby("Sector").head(1)[
                  ["Symbol", "Sector", "Quality_Type", "Quality_Val", "TotalScore"]].to_string(index=False))