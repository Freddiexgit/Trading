import yfinance as yf
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import linregress
from sklearn.preprocessing import MinMaxScaler
import os
import logging
import data_downloader as dd

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
# =========================
# 配置参数
# =========================
input_file = ""
START_DATE = "2023-01-01"  # 建议保留一年以上数据以保证指标稳定
SMOOTH_WINDOW = 5
PERSIST_DAYS = 2  # 降低持续天数要求，更灵敏
SCORE_THRESHOLD = 40  # 降低阈值以确保能看到分数排位


# =========================
# 核心工具类
# =========================
class PureLeaderRadar:
    @staticmethod
    def fast_slope(series):
        y = series.values
        if len(y) < 2 or np.isnan(y).any(): return 0
        slope, _, _, _, _ = linregress(np.arange(len(y)), y)
        return slope

    def load_tickers(self):
        return  pd.read_csv(f"{input_file}")['symbol'].tolist()

    def fetch_data(self, tickers):
        print(f"📥 正在获取 {len(tickers)} 只股票的数据...")
        # 批量下载以提高速度
        data = yf.download(tickers, start=START_DATE, progress=False)
        return data

    def process_stock(self, ticker, df):


        df.dropna(inplace=True)
        if len(df) < 60: return None

        # 1. 动量因子 (EMA & Slope)
        df["EMA10"] = df["Close"].ewm(span=10).mean()
        df["MA60"] = df["Close"].rolling(60).mean()
        df["slope10"] = df["EMA10"].rolling(10).apply(self.fast_slope, raw=False)
        df["slope60"] = df["MA60"].rolling(20).apply(self.fast_slope, raw=False)
        df["angle_strength"] = df["slope10"] - df["slope60"]

        # 2. 结构因子 (VCP & Highs)
        df["range"] = (df["High"] - df["Low"]) / df["Close"]
        df["vol_contract"] = df["range"] < df["range"].rolling(20).mean()
        df["near_high"] = df["Close"] > 0.80 * df["High"].rolling(120).max()

        # 3. 资金流因子 (OBV & Smart Money)
        change = df["Close"].diff()
        df["OBV"] = (np.sign(change).fillna(0) * df["Volume"]).cumsum()
        df["obv_slope"] = df["OBV"].rolling(20).apply(self.fast_slope, raw=False)

        up_v = df["Volume"].where(change > 0).rolling(20).mean()
        dn_v = df["Volume"].where(change < 0).rolling(20).mean()
        df["smart_money_ratio"] = (up_v / dn_v).replace([np.inf, -np.inf], 1).fillna(1)

        # 4. 纯净评分逻辑 (总分 100)
        # 移除了大盘和ETF加分，将权重分配给个股指标
        score = (
                30 * (df["angle_strength"] > 0).astype(int) +
                20 * (df["vol_contract"]).astype(int) +
                20 * (df["near_high"]).astype(int) +
                30 * (df["smart_money_ratio"] > 1.1).astype(int)
        )
        df['symbol'] = ticker
        df["RAW_SCORE"] = score
        df["SMOOTH_SCORE"] = df["RAW_SCORE"].ewm(span=SMOOTH_WINDOW).mean()

        # 5. 稳定信号处理
        df["PERSISTENCE"] = (df["SMOOTH_SCORE"] > SCORE_THRESHOLD).rolling(PERSIST_DAYS).sum()
        df["STABLE_SCORE"] = np.where(df["PERSISTENCE"] >= PERSIST_DAYS, df["SMOOTH_SCORE"], 0)

        # # 6. 预警模块
        # df["PRE_SIGNAL"] = (df["range"] < df["range"].rolling(10).mean()) & \
        #                    (df["smart_money_ratio"] > 1.05) & \
        #                    (df["Close"] < 0.95 * df["High"].rolling(120).max())
        # 1. Short term Volatility Contraction (Tightness)
        df["tightness"] = df["range"] < df["range"].rolling(10).mean()

        # 2. Accumulation Evidence (Smart Money is buying)
        df["accumulating"] = (df["smart_money_ratio"] > 1.02) & (df["obv_slope"] > 0)

        # 3. Base Building (Not in a vertical move yet, but near highs)
        # Looking for stocks 5% to 15% off their 120-day highs
        high_120 = df["High"].rolling(120).max()
        df["in_base"] = (df["Close"] < 0.98 * high_120) & (df["Close"] > 0.85 * high_120)

        # 4. Combined Trigger
        # We look for days where the stock is tight AND accumulating within a base
        df["PRE_SIGNAL_RAW"] = df["tightness"] & df["accumulating"] & df["in_base"]

        # 5. The "Lookback" Window
        # If the signal triggered ANYTIME in the last 5 days, return True
        df["PRE_SIGNAL"] = df["PRE_SIGNAL_RAW"].rolling(window=5).max() > 0

        return df


# =========================
# 执行主逻辑
# =========================
def main(input,output_file):
    global  input_file
    input_file = input
    radar = PureLeaderRadar()
    # tickers = radar.load_tickers()
    # full_data = radar.fetch_data(tickers)
    tickers = pd.read_csv(input_file)['symbol'].tolist()
    results = []
    print("🔍 正在计算量化因子...")
    for t in tickers:

        df = radar.process_stock(t, dd.get_transaction_df(t))
        if df is not None and not df.empty and df["STABLE_SCORE"].iloc[-1] > 0:
            last = df.iloc[[-1]].copy()
            results.append(last)

    if not results:
        print("❌ 未能获取有效计算结果。")
        return

    report = pd.concat(results).sort_values(by="STABLE_SCORE", ascending=False)
    report.to_csv(f"{output_file}", index=False)
    # 打印前 20 名
    # print("\n" + "=" * 70)
    # print(f"🚀 STOCK RADAR TOP 20 (Independent Analysis)")
    # print("=" * 70)
    # print(
    #     report.head(100).to_string(index=False))

    # 热力图展示前 15 名
    # top_n = report.head(15)
    # plot_cols = ['STABLE_SCORE', 'angle_strength', 'smart_money_ratio', 'obv_slope', 'range']
    # viz_data = top_n.set_index('Ticker')[plot_cols]
    #
    # # 归一化处理
    # scaled_viz = pd.DataFrame(MinMaxScaler().fit_transform(viz_data), columns=plot_cols, index=viz_data.index)
    #
    # plt.figure(figsize=(12, 8))
    # sns.heatmap(scaled_viz, annot=viz_data.values, fmt=".2f", cmap="RdYlGn", cbar=True)
    # plt.title(f"Factor Analysis Heatmap (Top 15 Ranking)", fontsize=15)
    # plt.tight_layout()
    # plt.show()

import os
if __name__ == "__main__":
    main(f"resource/my_vip.csv", output_file = "ema_angle_leaders.csv")
