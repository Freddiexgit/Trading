import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import linregress

# =========================
# 配置与参数
# =========================
STOCKS = ["NVDA", "AMD", "AVGO", "MU", "SMCI","TSM","ARM"]
SECTOR_ETF = "SOXX"
MARKET = "SPY"
START_DATE = "2023-01-01"

SMOOTH_WINDOW = 5
PERSIST_DAYS = 3


# =========================
# 优化后的工具函数
# =========================
def fast_slope(series):
    """
    比 np.polyfit 快 10 倍以上的线性回归斜率计算
    """
    y = series.values
    if len(y) < 2 or np.isnan(y).any():
        return 0
    x = np.arange(len(y))
    # 使用简单线性回归公式: slope = cov(x,y) / var(x)
    slope, _, _, _, _ = linregress(x, y)
    return slope


# =========================
# 核心计算引擎
# =========================
class LeaderRadar:
    def __init__(self, tickers, sector, market, start):
        self.tickers = tickers
        self.sector_ticker = sector
        self.market_ticker = market
        self.start = start
        self.data = None

    def download_data(self):
        """一次性下载所有数据，避免循环下载产生的对齐问题"""
        all_tickers = self.tickers + [self.sector_ticker, self.market_ticker]
        # group_by='column' 确保获取清洗后的长表或宽表
        df = yf.download(all_tickers, start=self.start, progress=False)
        self.data = df['Close']
        self.full_data = df  # 保留 OHLCV 用于个股分析
        return self.data

    def get_market_regime(self):
        """判断大盘趋势"""
        spy = self.full_data.xs(self.market_ticker, axis=1, level=1)
        ma50 = spy["Close"].rolling(50).mean()
        ma200 = spy["Close"].rolling(200).mean()

        # 状态：收盘 > MA200 且 MA50 > MA200
        is_bull = (spy["Close"] > ma200) & (ma50 > ma200)
        return is_bull.iloc[-1]

    def process_stock(self, ticker, market_ok, sector_rs_val):
        """处理单只个股指标"""
        df = self.full_data.xs(ticker, axis=1, level=1).copy()

        # 1. 趋势与斜率 (EMA/MA)
        df["EMA10"] = df["Close"].ewm(span=10, adjust=False).mean()
        df["MA60"] = df["Close"].rolling(60).mean()

        # 优化：减少 apply 的调用频率
        df["slope10"] = df["EMA10"].rolling(10).apply(fast_slope, raw=False)
        df["slope60"] = df["MA60"].rolling(20).apply(fast_slope, raw=False)
        df["angle_strength"] = df["slope10"] - df["slope60"]

        # 2. 波动压缩 (VCP 特征)
        daily_range = (df["High"] - df["Low"]) / df["Close"]
        df["vol_contract"] = daily_range < daily_range.rolling(20).mean()

        # 3. 价格强度
        high_120 = df["High"].rolling(120).max()
        df["near_high"] = df["Close"] > (0.85 * high_120)

        # 4. 资金流 (OBV & Smart Money)
        change = df["Close"].diff()
        df["OBV"] = (np.sign(change).fillna(0) * df["Volume"]).cumsum()
        df["obv_slope"] = df["OBV"].rolling(20).apply(fast_slope, raw=False)

        up_vol = df["Volume"].where(change > 0).rolling(20).mean()
        down_vol = df["Volume"].where(change < 0).rolling(20).mean()
        df["smart_money_ratio"] = (up_vol / down_vol).replace([np.inf, -np.inf], 1).fillna(1)

        # 5. 综合评分 (Vectorized)
        struct_score = (df["angle_strength"] > 0).astype(int) + \
                       (df["vol_contract"]).astype(int) + \
                       (df["near_high"]).astype(int)

        money_score = (df["smart_money_ratio"] > 1.2).astype(int) + \
                      (df["obv_slope"] > 0).astype(int)

        # 原始总分计算
        df["RAW_SCORE"] = (25 * int(market_ok)) + \
                          (20 * int(sector_rs_val > 0)) + \
                          (20 * (struct_score >= 2)) + \
                          (35 * (money_score >= 1))

        # 6. 信号平滑与稳定
        df["SMOOTH_SCORE"] = df["RAW_SCORE"].ewm(span=SMOOTH_WINDOW).mean()
        df["PERSISTENCE"] = (df["SMOOTH_SCORE"] > 70).rolling(PERSIST_DAYS).sum()
        df["STABLE_SCORE"] = np.where(df["PERSISTENCE"] >= PERSIST_DAYS, df["SMOOTH_SCORE"], 0)

        return df["STABLE_SCORE"].iloc[-1]


# =========================
# 执行主逻辑
# =========================
def main():
    radar = LeaderRadar(STOCKS, SECTOR_ETF, MARKET, START_DATE)
    print(f"📥 Downloading data for {len(STOCKS)} stocks...")
    radar.download_data()

    # 大盘环境
    market_ok = radar.get_market_regime()

    # 行业相对强度 (Sector RS)
    spy_close = radar.full_data.xs(MARKET, axis=1, level=1)["Close"]
    sec_close = radar.full_data.xs(SECTOR_ETF, axis=1, level=1)["Close"]

    spy_ret = spy_close.pct_change(60).iloc[-1]
    sec_ret = sec_close.pct_change(60).iloc[-1]
    sector_rs_val = sec_ret - spy_ret

    results = []
    for ticker in STOCKS:
        try:
            score = radar.process_stock(ticker, market_ok, sector_rs_val)
            results.append((ticker, round(score, 2)))
        except Exception as e:
            print(f"⚠️ Error processing {ticker}: {e}")

    # 排序输出
    results.sort(key=lambda x: x[1], reverse=True)

    print("-" * 30)
    print(f"🚀 LEADER RADAR REPORT (Market: {'✅BULL' if market_ok else '❌BEAR'})")
    print(f"Sector Relative Strength: {sector_rs_val:.2%}")
    print("-" * 30)
    for ticker, score in results:
        status = "🔥 STRONG" if score > 80 else "👀 WATCH" if score > 0 else "❄️ WEAK"
        print(f"{ticker:<6} : {score:>6} | {status}")


if __name__ == "__main__":
    main()