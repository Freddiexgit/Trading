import yfinance as yf
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import linregress
from sklearn.preprocessing import MinMaxScaler

# =========================
# 参数配置
# =========================
STOCKS = ["NVDA", "AMD", "AVGO", "MU", "SMCI", "TSM", "AAPL"]
SECTOR_ETF = "SOXX"
MARKET = "SPY"
START_DATE = "2023-01-01"

SMOOTH_WINDOW = 5
PERSIST_DAYS = 3
PRE_BREAKOUT_LOOKBACK = 10


# =========================
# 核心工具类
# =========================
class LeaderRadar:
    @staticmethod
    def fast_slope(series):
        """比 polyfit 快 10 倍的斜率计算"""
        y = series.values
        if len(y) < 2 or np.isnan(y).any(): return 0
        slope, _, _, _, _ = linregress(np.arange(len(y)), y)
        return slope

    def __init__(self, tickers):
        self.tickers = tickers
        self.all_data = None

    def fetch_data(self):
        print(f"📥 正在获取 {len(self.tickers)} 只股票及市场数据...")
        symbols = list(set(self.tickers + [SECTOR_ETF, MARKET]))
        self.all_data = yf.download(symbols, start=START_DATE, progress=False)
        return self.all_data

    def get_market_regime(self):
        spy = self.all_data.xs(MARKET, axis=1, level=1)
        ma50 = spy["Close"].rolling(50).mean()
        ma200 = spy["Close"].rolling(200).mean()
        # 市场环境 OK: 价格 > MA200 且 短期 > 长期
        status = (spy["Close"].iloc[-1] > ma200.iloc[-1]) and (ma50.iloc[-1] > ma200.iloc[-1])

        sector = self.all_data.xs(SECTOR_ETF, axis=1, level=1)
        sector_rs = sector["Close"].pct_change(60).iloc[-1] - spy["Close"].pct_change(60).iloc[-1]
        return status, sector_rs

    def process_stock(self, ticker, market_ok, sector_rs):
        df = self.all_data.xs(ticker, axis=1, level=1).copy()

        # 1. 趋势与强度
        df["EMA10"] = df["Close"].ewm(span=10).mean()
        df["MA60"] = df["Close"].rolling(60).mean()
        df["slope10"] = df["EMA10"].rolling(10).apply(self.fast_slope, raw=False)
        df["slope60"] = df["MA60"].rolling(20).apply(self.fast_slope, raw=False)
        df["angle_strength"] = df["slope10"] - df["slope60"]

        # 2. 波动率压缩 (VCP)
        df["range"] = (df["High"] - df["Low"]) / df["Close"]
        df["vol_contract"] = df["range"] < df["range"].rolling(20).mean()
        df["near_high"] = df["Close"] > 0.85 * df["High"].rolling(120).max()

        # 3. 资金流 (OBV & Smart Money)
        change = df["Close"].diff()
        df["OBV"] = (np.sign(change).fillna(0) * df["Volume"]).cumsum()
        df["obv_slope"] = df["OBV"].rolling(20).apply(self.fast_slope, raw=False)

        up_v = df["Volume"].where(change > 0).rolling(20).mean()
        dn_v = df["Volume"].where(change < 0).rolling(20).mean()
        df["smart_money_ratio"] = (up_v / dn_v).replace([np.inf, -np.inf], 1).fillna(1)

        # 4. 评分与平滑
        struct_ok = (df["angle_strength"] > 0) & df["vol_contract"] & df["near_high"]
        df["RAW_SCORE"] = (25 * int(market_ok)) + (20 * int(sector_rs > 0)) + \
                          (25 * struct_ok.astype(int)) + (30 * (df["smart_money_ratio"] > 1.2).astype(int))

        df["SMOOTH_SCORE"] = df["RAW_SCORE"].ewm(span=SMOOTH_WINDOW).mean()
        df["PERSISTENCE"] = (df["SMOOTH_SCORE"] > 70).rolling(PERSIST_DAYS).sum()
        df["STABLE_SCORE"] = np.where(df["PERSISTENCE"] >= PERSIST_DAYS, df["SMOOTH_SCORE"], 0)

        # 5. 预警模块 (修正变量名错误)
        df["vol_contract_short"] = df["range"] < df["range"].rolling(10).mean()
        not_breakout = df["Close"] < 0.92 * df["High"].rolling(120).max()  # 尚未主升浪
        df["PRE_BREAKOUT"] = df["vol_contract_short"] & (df["smart_money_ratio"] > 1.1) & (
                    df["obv_slope"] > 0) & not_breakout
        df["PRE_SIGNAL"] = df["PRE_BREAKOUT"].rolling(PRE_BREAKOUT_LOOKBACK).max() > 0

        return df


# =========================
# 执行与可视化
# =========================
def main():
    radar = LeaderRadar(STOCKS)
    radar.fetch_data()
    m_ok, s_rs = radar.get_market_regime()

    results = []
    for t in STOCKS:
        try:
            res_df = radar.process_stock(t, m_ok, s_rs)
            last = res_df.iloc[[-1]].copy()
            last.insert(0, 'Ticker', t)
            results.append(last)
        except Exception as e:
            print(f"Error on {t}: {e}")

    report = pd.concat(results).sort_values(by="STABLE_SCORE", ascending=False)

    # 打印结果
    print("\n" + "=" * 60)
    print(f"🚀 LEADER RADAR | Market: {'ON' if m_ok else 'OFF'} | Sector RS: {s_rs:.2%}")
    print("=" * 60)
    print(report[['Ticker', 'STABLE_SCORE', 'smart_money_ratio', 'PRE_SIGNAL']].to_string(index=False))


if __name__ == "__main__":
    main()