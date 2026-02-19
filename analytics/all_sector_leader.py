import yfinance as yf
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from scipy.stats import linregress

# =========================
# 配置参数
# =========================
STOCKS = ["NVDA", "AMD", "AVGO", "MU", "SMCI", "TSM", "ARM"]
SECTOR_ETF = "SOXX"
MARKET = "SPY"
START_DATE = "2023-01-01"

SMOOTH_WINDOW = 5
PERSIST_DAYS = 3


# =========================
# 核心计算引擎
# =========================
class LeaderRadarSystem:
    def __init__(self, tickers, sector, market, start):
        self.tickers = tickers
        self.sector_ticker = sector
        self.market_ticker = market
        self.start = start
        self.raw_data = None

    def fast_slope(self, series):
        """线性回归斜率快速计算"""
        y = series.values
        if len(y) < 2 or np.isnan(y).any():
            return 0
        x = np.arange(len(y))
        slope, _, _, _, _ = linregress(x, y)
        return slope

    def download_data(self):
        print(f"📥 正在获取数据...")
        all_symbols = list(set(self.tickers + [self.sector_ticker, self.market_ticker]))
        self.raw_data = yf.download(all_symbols, start=self.start, progress=False)
        return self.raw_data

    def get_market_context(self):
        """计算大盘和行业背景"""
        spy = self.raw_data.xs(self.market_ticker, axis=1, level=1)
        sec = self.raw_data.xs(self.sector_ticker, axis=1, level=1)

        # 大盘趋势
        ma50 = spy["Close"].rolling(50).mean()
        ma200 = spy["Close"].rolling(200).mean()
        market_ok = (spy["Close"].iloc[-1] > ma200.iloc[-1]) and (ma50.iloc[-1] > ma200.iloc[-1])

        # 行业相对强度 (RS)
        spy_ret = spy["Close"].pct_change(60).iloc[-1]
        sec_ret = sec["Close"].pct_change(60).iloc[-1]
        sector_rs = sec_ret - spy_ret

        return market_ok, sector_rs

    def compute_metrics(self, ticker, market_ok, sector_rs):
        """计算单只个股的所有因子"""
        df = self.raw_data.xs(ticker, axis=1, level=1).copy()

        # 1. 趋势因子
        df["EMA10"] = df["Close"].ewm(span=10, adjust=False).mean()
        df["MA60"] = df["Close"].rolling(60).mean()
        df["slope10"] = df["EMA10"].rolling(10).apply(self.fast_slope, raw=False)
        df["slope60"] = df["MA60"].rolling(20).apply(self.fast_slope, raw=False)
        df["angle_strength"] = df["slope10"] - df["slope60"]

        # 2. 波动压缩 (VCP特征)
        df["range"] = (df["High"] - df["Low"]) / df["Close"]
        df["vol_contract"] = df["range"] < df["range"].rolling(20).mean()

        # 3. 价格位置
        high_120 = df["High"].rolling(120).max()
        df["near_high"] = df["Close"] > (0.85 * high_120)

        # 4. 资金流因子
        change = df["Close"].diff()
        df["OBV"] = (np.sign(change).fillna(0) * df["Volume"]).cumsum()
        df["obv_slope"] = df["OBV"].rolling(20).apply(self.fast_slope, raw=False)

        up_vol = df["Volume"].where(change > 0).rolling(20).mean()
        down_vol = df["Volume"].where(change < 0).rolling(20).mean()
        df["smart_money_ratio"] = (up_vol / down_vol).replace([np.inf, -np.inf], 1).fillna(1)

        # 5. 评分系统
        struct_ok = (df["angle_strength"] > 0) & df["vol_contract"] & df["near_high"]
        money_ok = (df["smart_money_ratio"] > 1.1) | (df["obv_slope"] > 0)

        df["RAW_SCORE"] = (25 * int(market_ok)) + \
                          (20 * int(sector_rs > 0)) + \
                          (25 * struct_ok.astype(int)) + \
                          (30 * money_ok.astype(int))

        # 6. 信号平滑
        df["SMOOTH_SCORE"] = df["RAW_SCORE"].ewm(span=SMOOTH_WINDOW).mean()
        df["PERSISTENCE"] = (df["SMOOTH_SCORE"] > 70).rolling(PERSIST_DAYS).sum()
        df["STABLE_SCORE"] = np.where(df["PERSISTENCE"] >= PERSIST_DAYS, df["SMOOTH_SCORE"], 0)

        return df


# =========================
# 可视化与主程序
# =========================
def main():
    radar = LeaderRadarSystem(STOCKS, SECTOR_ETF, MARKET, START_DATE)
    radar.download_data()
    market_ok, sector_rs = radar.get_market_context()

    all_rows = []
    for ticker in STOCKS:
        try:
            df = radar.compute_metrics(ticker, market_ok, sector_rs)
            last_row = df.iloc[[-1]].copy()
            last_row.insert(0, 'Ticker', ticker)
            all_rows.append(last_row)
        except Exception as e:
            print(f"❌ {ticker} 出错: {e}")

    # 合并报表
    report_df = pd.concat(all_rows, ignore_index=True)
    report_df = report_df.sort_values(by="STABLE_SCORE", ascending=False)

    # 打印文字版简报
    print("\n" + "=" * 50)
    print(f"🚀 LEADER RADAR REPORT | Market: {'Bull' if market_ok else 'Bear'}")
    print("=" * 50)
    print(report_df[['Ticker', 'Close', 'STABLE_SCORE', 'smart_money_ratio', 'vol_contract']].to_string(index=False))

    # # --- 热力图可视化 ---
    # plot_cols = ['STABLE_SCORE', 'slope10', 'angle_strength', 'obv_slope', 'smart_money_ratio', 'range']
    # heatmap_data = report_df.set_index('Ticker')[plot_cols]
    #
    # # 数据归一化用于颜色映射
    # scaler = MinMaxScaler()
    # scaled_values = scaler.fit_transform(heatmap_data)
    # scaled_df = pd.DataFrame(scaled_values, columns=plot_cols, index=heatmap_data.index)
    #
    # plt.figure(figsize=(12, 7))
    # sns.heatmap(
    #     scaled_df,
    #     annot=heatmap_data.values,
    #     fmt=".2f",
    #     cmap="RdYlGn",
    #     linewidths=.5,
    #     cbar_kws={'label': 'Relative Strength (0-1)'}
    # )
    #
    # plt.title(f"Factor Analysis Heatmap (Market: {'Bullish' if market_ok else 'Bearish'})", fontsize=15)
    # plt.tight_layout()
    # plt.show()


if __name__ == "__main__":
    # 设置显示限制
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    main()