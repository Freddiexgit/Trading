import pandas as pd
#
# 如何在30秒內分析一支股票（流程圖整理）：
#
# 1. 公司收入每年至少增長10%？
#    - 否：停止，收入增長緩慢。
#    - 是：下一步。
#
# 2. 市盈率是否低於25？
#    - 否：PEG比率是否低於2？
#      - 是：好，成長股。
#      - 否：估值過高。
#    - 是：下一步。
#
# 3. 公司過去五年平均淨資產收益率是否超過5%？
#    - 否：盈利能力弱。
#    - 是：下一步。
#
# 4. 速動比率是否高於1.5？
#    - 否：流動性問題。
#    - 是：下一步。
#
# 5. 現金流是否正向？
#    - 否：不適合。
#    - 是：投資！


# 1. 讀取數據
import yfinance as yf
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
# 1. 讀取只有 Ticker 的文件
try:
    df_all = pd.read_csv("../resource/my_watch_list.csv")
    tickers = df_all['symbol'].unique().tolist()  # 假設欄位叫
except:
    # 測試用：如果讀不到文件，手動輸入幾個 Ticker
    tickers = [ "ENLT"]


def get_reliable_peg(info):
    # 1. 嘗試直接獲取
    peg = info.get('pegRatio')

    # 2. 如果沒有現成的 PEG，手動計算
    if peg is None or peg == 0:
        pe = info.get('trailingPE')
        # 使用盈餘增長 (Earnings Growth) 作為分母
        growth = info.get('earningsQuarterlyGrowth')

        # 如果盈餘增長數據也沒有，退而求其次使用收入增長
        if growth is None:
            growth = info.get('revenueGrowth')

        if pe and growth and growth > 0:
            # yfinance 的 growth 通常是小數 (例如 0.25 代表 25%)
            # 計算公式需要將 0.25 轉為 25
            peg = pe / (growth * 100)
        else:
            peg = 999  # 代表數據不足，無法評估

    return peg


def get_fpe_otherwise_pe(info):
    fpe = info.get('forwardPE')
    pe = info.get('trailingPE')

    # 邏輯：如果有 FPE，優先用 FPE（代表市場對未來的預期）
    # 如果沒有 FPE (通常是分析師覆蓋不足)，則退而求其次使用真實的 PE
    current_val = fpe if fpe is not None else pe

    return current_val

def get_stock_data_and_screen(ticker_list):
    results = []
    print(f"🚀 開始分析 {len(ticker_list)} 隻股票並獲取華爾街評級...")

    for symbol in ticker_list:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info

            # --- 獲取數據 (含評分) ---
            rating = info.get('recommendationMean', 3.0)  # 預設為 3 (Hold)
            rev_growth = info.get('revenueGrowth', 0)
            pe_ratio = get_fpe_otherwise_pe(info)
            peg_ratio = get_reliable_peg(info)
            roe = info.get('returnOnEquity', 0)
            quick_ratio = info.get('quickRatio', 0)
            fcf = info.get('freeCashflow', 0)

            # --- 基礎篩選 (你的 5 個條件) ---
            if rev_growth < 0.10: continue
            if not (pe_ratio < 25 or peg_ratio < 2): continue
            if roe < 0.05: continue
            if quick_ratio < 1.5: continue
            if fcf <= 0: continue

            # --- 儲存符合條件的結果 ---
            results.append({
                'Symbol': symbol,
                'Analyst_Rating': rating,  # 數字越小越強
                'PEG_Ratio': peg_ratio,
                'ROE': roe,
                'Revenue_Growth': rev_growth,
                'Sector': info.get('sector', 'N/A'),
                'Current_Price': info.get('currentPrice', 0)
            })
            print(f"🎯 {symbol} 符合條件！評分: {rating}")

        except Exception as e:
            continue

    df = pd.DataFrame(results)

    if df.empty:
        return df

    # --- 強烈買入排序邏輯 ---
    # 權重 1: Analyst_Rating (升序: 1.0 最優)
    # 權重 2: PEG_Ratio (升序: 越小越便宜)
    # 權重 3: ROE (降序: 效率越高越好)
    final_sorted = df.sort_values(
        by=['Analyst_Rating', 'PEG_Ratio', 'ROE'],
        ascending=[True, True, False]
    )

    return final_sorted


# 執行
final_df = get_stock_data_and_screen(tickers)

# 顯示與儲存
if not final_df.empty:
    print("\n符合所有條件的股票名單：")
    print(final_df)
    final_df.to_csv("yfinance_screened_results.csv", index=False)
else:
    print("\n今日無符合條件的股票。")