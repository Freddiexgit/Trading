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
START_DATE = "2025-01-01"  # 建议保留一年以上数据以保证指标稳定
SMOOTH_WINDOW = 5
PERSIST_DAYS = 2  # 降低持续天数要求，更灵敏
SCORE_THRESHOLD = 40  # 降低阈值以确保能看到分数排位


# =========================
# 核心工具类
# =========================
class PureLeaderRadar:
    import numpy as np
    import pandas as pd
    from scipy.stats import linregress

    # Tunable constants
    SMOOTH_WINDOW = 5
    SCORE_THRESHOLD = 50  # on 0-100 scale after weighting
    PERSIST_DAYS = 3

    @staticmethod
    def _log_slope_array(arr):
        # returns slope of log(price) per period (approx daily log-return)
        n = len(arr)
        if n < 2 or np.isnan(arr).any():
            return np.nan
        y = np.log(arr.astype(float))
        x = np.arange(n)
        xm = x.mean();
        ym = y.mean()
        denom = ((x - xm) ** 2).sum()
        if denom == 0:
            return np.nan
        return ((x - xm) * (y - ym)).sum() / denom

    @staticmethod
    def _fast_slope_for_rolling(window_arr):
        # wrapper for rolling.apply with raw=True (receives numpy array)
        return PureLeaderRadar._log_slope_array(window_arr)

    @staticmethod
    def _percentile_rank(series):
        # returns 0..1 percentile rank, preserves NaN
        return series.rank(pct=True, na_option='keep')

    @staticmethod
    def _winsorize_series(s, lower=0.01, upper=0.99):
        ql = s.quantile(lower)
        qu = s.quantile(upper)
        return s.clip(lower=ql, upper=qu)

    def process_stock(self, ticker, df):
        df = df.copy()
        df.dropna(inplace=True)
        if len(df) < 60:
            return None

        # --- Price trend (EMA + normalized slopes) ---
        df["EMA10"] = df["Close"].ewm(span=10, adjust=False).mean()
        df["EMA60"] = df["Close"].ewm(span=60, adjust=False).mean()

        # compute log-slope on EMA series (scale-invariant)
        df["ema10_slope"] = df["EMA10"].rolling(10).apply(
            PureLeaderRadar._fast_slope_for_rolling, raw=True
        )
        df["ema60_slope"] = df["EMA60"].rolling(60).apply(
            PureLeaderRadar._fast_slope_for_rolling, raw=True
        )

        # angle_strength in log-return units (daily excess log-return)
        df["angle_strength"] = df["ema10_slope"] - df["ema60_slope"]

        # shift slopes so any trading decision uses only past data (act next day)
        df["angle_strength_next"] = df["angle_strength"].shift(1)

        # --- Volatility / structure (tightness) ---
        df["range"] = (df["High"] - df["Low"]) / df["Close"]
        # raw contraction metric: smaller range relative to 20-day mean
        df["range_rel"] = df["range"] / df["range"].rolling(20).mean()
        # lower is better -> invert later when percentile-scaling
        df["range_rel"] = df["range_rel"].replace([np.inf, -np.inf], np.nan)

        # proximity to 120-day high (higher is better)
        high_120 = df["High"].rolling(120).max()
        df["dist_from_high"] = (high_120 - df["Close"]) / high_120  # 0 = at high
        df["dist_from_high"] = df["dist_from_high"].clip(lower=0)

        # --- Volume / money flow (OBV, smart money) ---
        change = df["Close"].diff()
        df["OBV"] = (np.sign(change).fillna(0) * df["Volume"]).cumsum()
        # OBV slope (log-slope on OBV can be noisy; use linear slope on OBV and zscore)
        df["obv_slope"] = df["OBV"].rolling(20).apply(
            lambda x: np.nan if np.isnan(x).any() else linregress(np.arange(len(x)), x).slope,
            raw=True
        )
        # normalize OBV slope via rolling z-score
        obv_mean = df["obv_slope"].rolling(60).mean()
        obv_std = df["obv_slope"].rolling(60).std().replace(0, np.nan)
        df["obv_z"] = (df["obv_slope"] - obv_mean) / obv_std

        # smart money ratio: avg up-volume / avg down-volume over 20 days, guard small denominators
        up_v = df["Volume"].where(change > 0).rolling(20).mean().fillna(0)
        dn_v = df["Volume"].where(change < 0).rolling(20).mean().fillna(0)
        eps = 1e-6
        df["smart_money_raw"] = (up_v + eps) / (dn_v + eps)
        # winsorize and log-transform to stabilize
        df["smart_money_w"] = np.log(self._winsorize_series(df["smart_money_raw"], 0.01, 0.99))

        # shift money-flow metrics for next-day execution
        df["obv_z_next"] = df["obv_z"].shift(1)
        df["smart_money_next"] = df["smart_money_w"].shift(1)

        # --- Convert metrics to 0..1 percentile scores (higher = better) ---
        # angle: higher positive excess slope is better
        df["angle_score"] = self._percentile_rank(df["angle_strength_next"])

        # volatility contraction: smaller range_rel is better -> invert before percentile
        df["range_rel_inv"] = 1.0 / df["range_rel"]
        df["range_rel_inv"] = df["range_rel_inv"].replace([np.inf, -np.inf], np.nan)
        df["vol_contract_score"] = self._percentile_rank(df["range_rel_inv"])

        # proximity to highs: closer (smaller dist) is better -> invert
        df["near_high_score"] = self._percentile_rank(1 - df["dist_from_high"])

        # OBV z: higher z is better
        df["obv_score"] = self._percentile_rank(df["obv_z_next"])

        # smart money: higher log ratio is better
        df["smart_money_score"] = self._percentile_rank(df["smart_money_next"])

        # --- Combine weighted scores (weights sum to 100) ---
        w_angle = 30
        w_vol = 20
        w_high = 20
        w_money = 30

        # ensure scores are 0..1 and handle NaNs by treating them as 0 (no evidence)
        score_components = (
                w_angle * df["angle_score"].fillna(0) +
                w_vol * df["vol_contract_score"].fillna(0) +
                w_high * df["near_high_score"].fillna(0) +
                w_money * df["smart_money_score"].fillna(0)
        )
        # raw score on 0..100 scale
        df["RAW_SCORE"] = score_components

        # smooth and shift so the actionable score is for next trading day
        df["SMOOTH_SCORE"] = df["RAW_SCORE"].ewm(span=SMOOTH_WINDOW, adjust=False).mean()
        df["SMOOTH_SCORE_NEXT"] = df["SMOOTH_SCORE"].shift(1)

        # persistence: require SMOOTH_SCORE_NEXT > threshold for PERSIST_DAYS (count of True)
        df["PERSIST"] = (df["SMOOTH_SCORE_NEXT"] > SCORE_THRESHOLD).rolling(PERSIST_DAYS).sum()
        df["STABLE_SCORE"] = np.where(df["PERSIST"] >= PERSIST_DAYS, df["SMOOTH_SCORE_NEXT"], 0)

        # --- Pre-signal (tightness + accumulation + base) using next-day metrics ---
        df["tightness_next"] = (df["range"] < df["range"].rolling(10).mean()).shift(1)
        df["accumulating_next"] = (df["smart_money_next"] > np.log(1.02)) & (df["obv_z_next"] > 0)
        df["in_base_next"] = ((df["Close"] < 0.98 * high_120) & (df["Close"] > 0.85 * high_120)).shift(1)
        df["PRE_SIGNAL_RAW"] = df["tightness_next"] & df["accumulating_next"] & df["in_base_next"]
        df["PRE_SIGNAL"] = df["PRE_SIGNAL_RAW"].rolling(window=5).max().fillna(0) > 0

        # metadata
        df["symbol"] = ticker

        # final: keep only rows where all required metrics are finite for clarity
        required = ["RAW_SCORE", "SMOOTH_SCORE_NEXT", "STABLE_SCORE"]
        df.loc[:, required] = df.loc[:, required].fillna(0)

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
    # tickers=["RGTX"]
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
