import traceback

import yfinance as yf
import pandas as pd
import logging
import data_downloader as dd

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ---------------- Configuration ----------------
# CONFIG = {
#     "MIN_MARKET_CAP": 5e8,  # 市值門檻
#     "MIN_VOLUME": 200_000,  # 成交量門檻
#     "MAX_DEBT_EBITDA": 3.5,  # 債務槓桿上限
#     "MIN_REV_GROWTH": 0.10,  # 營收增長下限
#     "MIN_ROE": 0.05  # ROE 下限
# }


# ---------------- Helpers ----------------
def safe_get(info: dict, key: str, default=0.0):
    val = info.get(key)
    if val is None or str(val).lower() == 'nan':
        return default
    return val


def get_reliable_peg(info: dict) -> float:
    """ 計算 PEG：優先使用現成數據，若無則手動計算 """
    peg = info.get('trailingPegRatio') or info.get('pegRatio')
    if peg and 0 < peg < 10:
        return float(peg)

    pe = info.get('forwardPE') or info.get('trailingPE')
    growth = info.get('earningsQuarterlyGrowth') or info.get('revenueGrowth')

    if pe and growth and growth > 0:
        return float(pe / (growth * 100))
    return 9.9


def compute_bollinger_bands(hist: pd.DataFrame, window: int = 20, num_std: int = 2):
    if len(hist) < window:
        return "N/A", 50.0

    sma = hist['Close'].rolling(window=window).mean()
    std = hist['Close'].rolling(window=window).std()

    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)

    current_price = hist['Close'].iloc[-1]
    last_upper = upper_band.iloc[-1]
    last_lower = lower_band.iloc[-1]

    # 計算百分比位置 (0% = 下軌, 100% = 上軌)
    bb_pos = (current_price - last_lower) / (last_upper - last_lower) * 100

    # 狀態判定
    if current_price <= last_lower:
        status = "OVERSOLD"
    elif current_price >= last_upper:
        status = "OVERBOUGHT"
    else:
        status = "NEUTRAL"

    return status, round(bb_pos, 2)

def get_fpe_otherwise_pe(info: dict):
    return info.get('forwardPE') or info.get('trailingPE') or 99.0


# ---------------- Core Logic ----------------

def process_ticker(symbol: str) -> dict | None:
    """
    同步處理單個股票
    """
    try:
        logging.info(f"正在分析: {symbol}...")
        stock = dd.get_stock_obj(symbol)
        info = stock.get_info()
        if not info or 'marketCap' not in info:
            logging.warning(f"跳過 {symbol}: 無法獲取基礎數據")
            return None


        # --- 1. 硬性過濾 (Hard Filters) ---
        mkt_cap = safe_get(info, 'marketCap', 0)
        avg_vol = safe_get(info, 'averageVolume', 0)

        # if mkt_cap < CONFIG["MIN_MARKET_CAP"] or avg_vol < CONFIG["MIN_VOLUME"]:
        #     return None

        rev_growth = safe_get(info, 'revenueGrowth', 0)
        roe = safe_get(info, 'returnOnEquity', 0)
        debt = safe_get(info, 'totalDebt', 0)
        ebitda = safe_get(info, 'ebitda', 0)
        pe_ratio = get_fpe_otherwise_pe(info)
        peg_ratio = get_reliable_peg(info)
        fcf = safe_get(info, 'freeCashflow', 0)
        # ----bollinger_bands
        # hist = stock.history(period="3mo")
        hist = dd.get_transaction_df(symbol)
        bb_status, bb_pos = compute_bollinger_bands(hist)

        # 核心財務條件過濾
        # if rev_growth < CONFIG["MIN_REV_GROWTH"] or roe < CONFIG["MIN_ROE"]:
        #     return None
        #
        leverage = debt / ebitda if ebitda > 0 else 99.0
        # if leverage > CONFIG["MAX_DEBT_EBITDA"] or fcf <= 0:
        #     return None

        if pe_ratio > 45 or peg_ratio > 2.5:
            return None

        # --- 2. 計算動能 (Momentum) ---
        # 同步抓取歷史數據
        hist = dd.get_transaction_df(symbol)
        if len(hist) < 20:
            momentum = 0.0
        else:
            momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[-20]) - 1

        # --- 3. 評分系統 ---
        score = 0
        if rev_growth > 0.20:
            score += 2
        elif rev_growth > 0.10:
            score += 1

        if roe > 0.15: score += 2

        if peg_ratio < 1.0:
            score += 2
        elif peg_ratio < 1.5:
            score += 1

        if momentum > 0: score += 1

        # 門檻設定 (4分以上視為優質標的)
        if score < 3:
            return None
        # Get annual statements
        try:
            ocf = stock.cashflow.loc["Operating Cash Flow"].iloc[0]
        except Exception  as e:
            logging.debug(f"無法獲取 {symbol} 的現金流數據: {e}")
            ocf = 0.0
        try:
            net_income = stock.financials.loc["Net Income"].iloc[0]
        except Exception  as e:
            logging.debug(f"無法獲取 {symbol} 的淨利數據: {e}")
            net_income = 0.0
        if net_income is None or net_income == 0:
            ocf_net_income_ratio = 0.0
        else:
            ocf_net_income_ratio = round(ocf / net_income, 2),
        try:
            ocf2 = stock.cashflow.loc["Operating Cash Flow"].iloc[1]
        except Exception  as e:
            logging.debug(f"無法獲取 {symbol} 的前一年現金流數據: {e}")
            ocf2 = 0.0
        try:
            net_income2 = stock.financials.loc["Net Income"].iloc[1]
        except Exception  as e:
            logging.debug(f"無法獲取 {symbol} 的前一年淨利數據: {e}")
            net_income2 = 0.0
        if net_income2 is None or net_income2 == 0:
            ocf_net_income_ratio2 = 0.0
        else:
            ocf_net_income_ratio2 = round(ocf2 / net_income2, 2),

        return {
            'symbol': symbol,
            'price': hist['Close'].iloc[-1],
            'Score': score,
            'Rating': safe_get(info, 'recommendationMean', 3.0),
            'PEG': round(peg_ratio, 2),
            'PE_Fwd': round(pe_ratio, 2),
            'ROE': f"{roe:.2%}",
            "OCF_to_NetIncome_Ratio_last2year" :f"{ocf_net_income_ratio2},{ocf_net_income_ratio}",
            'Debt_EBITDA': round(leverage, 2),
            'Mkt_Cap_B': round(mkt_cap / 1e9, 2),
            'Momentum_20d': f"{momentum:.2%}",
            'Sector': info.get('sector', 'N/A'),
            'bollinger_band_status': bb_status,
            'BB_Pos': bb_pos
        }

    except Exception as e:
        logging.error(f"處理 {symbol} 時發生錯誤: {e}")
        traceback.print_exc()
        return None


def run_sequential_screening(ticker_list):
    """
    循序漸進處理清單，並加入微小延遲以防被鎖 IP
    """
    results = []
    total = len(ticker_list)

    for i, symbol in enumerate(ticker_list):
        res = process_ticker(symbol)
        if res:
            results.append(res)
            # print(f">>> [成功符合] {symbol} | 目前進度: {i + 1}/{total}")

        # 每處理完一個股票稍作休息 (可選)
        # time.sleep(0.5)

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(['Score', 'Rating', 'PEG'], ascending=[False, True, True])
    return df


# ---------------- Execution ----------------
def run_quick_fundamental_analysis(input_file=None,output_file=None):
    try:
        watch_list = pd.read_csv(f"{input_file}")['symbol'].tolist()
    except:
        watch_list = ["enlt"]

    final_df = run_sequential_screening(watch_list)

    if not final_df.empty:
        print("\n🏆 符合條件的優質標的 (按分數排序):")
        # print(final_df.to_string(index=False))
        final_df.to_csv(f"{output_file}", index=False)
    else:
        print("\n今日無標的符合篩選條件。")

if __name__ == "__main__":
    run_quick_fundamental_analysis()