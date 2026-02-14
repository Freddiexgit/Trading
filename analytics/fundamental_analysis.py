import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

# Configuration for display
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)


class InstitutionalAnalyzer:
    def __init__(self, tickers):
        self.tickers = tickers
        self.benchmark_symbol = 'SPY'
        self.benchmark_data = None
        self.data_source = "Yahoo Finance (via yfinance API)"
        self.today = datetime.now().strftime('%Y-%m-%d')

    def fetch_benchmark(self):
        """Fetches SPY data for Relative Strength calculations."""
        print(f"[System] Fetching Benchmark Data ({self.benchmark_symbol})...")
        try:
            spy = yf.Ticker(self.benchmark_symbol)
            # Fetch enough history for 1 Year relative strength
            hist = spy.history(period="1y")
            if hist.empty:
                raise ValueError("Empty benchmark history")
            self.benchmark_data = hist
        except Exception as e:
            print(f"[Error] Failed to fetch benchmark data: {e}")
            sys.exit(1)

    def calculate_relative_strength(self, stock_hist):
        """Calculates performance relative to SPY over different timeframes."""
        if self.benchmark_data is None or stock_hist.empty:
            return {}

        # Align dates
        df = pd.DataFrame({'Stock': stock_hist['Close'], 'Benchmark': self.benchmark_data['Close']}).dropna()

        periods = {
            '1M': 21,
            '3M': 63,
            '6M': 126,
            'YTD': None,  # Calculated via date logic below
            '1Y': 252
        }

        rs_metrics = {}
        current_price = df['Stock'].iloc[-1]
        current_bench = df['Benchmark'].iloc[-1]

        # YTD Logic
        start_year = df[df.index >= f"{datetime.now().year}-01-01"]
        if not start_year.empty:
            start_price = start_year['Stock'].iloc[0]
            start_bench = start_year['Benchmark'].iloc[0]
            stock_ret = (current_price - start_price) / start_price
            bench_ret = (current_bench - start_bench) / start_bench
            rs_metrics['YTD_Rel'] = (stock_ret - bench_ret) * 100
            rs_metrics['YTD_Abs'] = stock_ret * 100
        else:
            rs_metrics['YTD_Rel'] = np.nan

        for label, days in periods.items():
            if label == 'YTD': continue
            if len(df) > days:
                prev_price = df['Stock'].iloc[-days]
                prev_bench = df['Benchmark'].iloc[-days]

                stock_ret = (current_price - prev_price) / prev_price
                bench_ret = (current_bench - prev_bench) / prev_bench

                # Relative Strength: Stock Return minus Benchmark Return (Alpha approximation)
                rs_metrics[f'{label}_Rel'] = (stock_ret - bench_ret) * 100
                rs_metrics[f'{label}_Abs'] = stock_ret * 100
            else:
                rs_metrics[f'{label}_Rel'] = np.nan
                rs_metrics[f'{label}_Abs'] = np.nan

        return rs_metrics

    def get_financial_growth(self, ticker_obj):
        """Calculates YoY Revenue and Net Income growth from financial statements."""
        try:
            fin = ticker_obj.financials
            if fin.empty or fin.shape[1] < 2:
                return "N/A", "N/A"

            # Most recent year vs Previous year
            cols = fin.columns
            latest = fin[cols[0]]
            previous = fin[cols[1]]

            rev_growth = np.nan
            if 'Total Revenue' in fin.index:
                rev_growth = ((latest['Total Revenue'] - previous['Total Revenue']) / previous['Total Revenue']) * 100

            return rev_growth
        except Exception:
            return "N/A"

    def run_analysis(self):
        self.fetch_benchmark()

        report_separator = "=" * 80
        section_separator = "-" * 80

        for symbol in self.tickers:
            try:
                print(f"\nProcessing {symbol}...")
                ticker = yf.Ticker(symbol)

                # 1. FETCH DATA
                info = ticker.info
                hist = ticker.history(period="1y")

                if hist.empty:
                    print(f"[Warning] No price data for {symbol}. Likely delisted or invalid ticker.")
                    continue

                # 2. CALCULATIONS
                rs_data = self.calculate_relative_strength(hist)
                rev_growth_yoy = self.get_financial_growth(ticker)

                # 3. GENERATE REPORT
                print(report_separator)
                print(f"INSTITUTIONAL ANALYSIS REPORT: {symbol} ({info.get('longName', symbol)})")
                print(f"Data Source: {self.data_source} | Data Date: {self.today}")
                print(report_separator)

                # --- SECTION 1: COMPANY PROFILE ---
                print(f"1. COMPANY PROFILE")
                print(f"   Sector: {info.get('sector', 'N/A')} | Industry: {info.get('industry', 'N/A')}")
                print(f"   Business Summary: {info.get('longBusinessSummary', 'N/A')[:300]}...")
                print(f"   Moat/Peers: Competes in {info.get('industry', 'N/A')}. Check peers manually in sector.")
                print(section_separator)

                # --- SECTION 2: KEY FINANCIALS ---
                # Handle differences between Equities and ETFs
                is_etf = info.get('quoteType', '') == 'ETF'

                print(f"2. KEY FINANCIALS (Currency: {info.get('currency', 'USD')})")
                if not is_etf:
                    print(f"   Price: {info.get('currentPrice', 'N/A')}")
                    print(f"   Market Cap: {info.get('marketCap', 'N/A')}")
                    print(
                        f"   Trailing PE: {info.get('trailingPE', 'N/A')} | Forward PE: {info.get('forwardPE', 'N/A')}")
                    print(f"   PEG Ratio: {info.get('pegRatio', 'N/A')} (Valuation Metric)")
                    print(f"   Price/Sales: {info.get('priceToSalesTrailing12Months', 'N/A')}")
                    print(
                        f"   EPS (TTM): {info.get('trailingEps', 'N/A')} | EPS (Fwd): {info.get('forwardEps', 'N/A')}")
                    print(
                        f"   Total Debt: {info.get('totalDebt', 'N/A')} | Debt/Equity: {info.get('debtToEquity', 'N/A')}")
                    print(
                        f"   Revenue Growth (YoY): {rev_growth_yoy if isinstance(rev_growth_yoy, str) else f'{rev_growth_yoy:.2f}%'}")
                    print(f"   Free Cash Flow: {info.get('freeCashflow', 'N/A')}")
                else:
                    print(f"   Type: ETF | NAV: {info.get('navPrice', 'N/A')}")
                    print(
                        f"   Yield: {info.get('yield', 'N/A')} | Expense Ratio: {info.get('annualReportExpenseRatio', 'N/A')}")
                print(section_separator)

                # --- SECTION 3: PERFORMANCE & RELATIVE STRENGTH ---
                print(f"3. STOCK PERFORMANCE (vs SPY Benchmark)")
                print(f"   52-Week Range: {info.get('fiftyTwoWeekLow', 'N/A')} - {info.get('fiftyTwoWeekHigh', 'N/A')}")
                print(f"   {'Period':<10} | {'Abs Return':<12} | {'Rel Strength (vs SPY)':<20}")
                for p in ['1M', '3M', '6M', 'YTD']:
                    abs_val = rs_data.get(f'{p}_Abs')
                    rel_val = rs_data.get(f'{p}_Rel')
                    abs_str = f"{abs_val:.2f}%" if pd.notnull(abs_val) else "N/A"
                    rel_str = f"{rel_val:.2f}%" if pd.notnull(rel_val) else "N/A"
                    print(f"   {p:<10} | {abs_str:<12} | {rel_str:<20}")
                print(section_separator)

                # --- SECTION 4: WALL STREET EXPECTATIONS ---
                print(f"4. WALL STREET CONSENSUS")
                if not is_etf:
                    print(f"   Target Mean Price: {info.get('targetMeanPrice', 'N/A')}")
                    print(f"   Consensus Recommendation: {info.get('recommendationKey', 'N/A').upper()}")
                    print(f"   Number of Analyst Opinions: {info.get('numberOfAnalystOpinions', 'N/A')}")
                else:
                    print("   N/A (ETF Structure)")
                print(section_separator)

                # --- SECTION 5: CAPITAL FLOW & OWNERSHIP ---
                print(f"5. INSTITUTIONAL OWNERSHIP")
                try:
                    holders = ticker.institutional_holders
                    if holders is not None and not holders.empty:
                        # Sort by shares held if possible, or print top 5 rows
                        print(f"   Top Institutional Holders (Source: SEC 13F/Mutual Fund Filings):")
                        # Rename columns for clarity if standard yfinance output
                        if 'Holder' in holders.columns and 'Shares' in holders.columns:
                            top_holders = holders[['Holder', 'Shares', 'Date Reported', '% Out']].head(5)
                            print(top_holders.to_string(index=False))
                        else:
                            print(holders.head(5).to_string(index=False))
                    else:
                        print("   No institutional holding data available.")
                except Exception as e:
                    print(f"   Could not retrieve holder data: {e}")

                print(report_separator + "\n")

            except Exception as e:
                print(f"[ERROR] Critical failure analyzing {symbol}: {str(e)}")
                print(section_separator)


if __name__ == "__main__":
    # List provided in prompt
    tickers_list = [
        "SNDK", "TQQQ", "NFLX", "ONDS", "NAK", "TSLR", "RBLU", "ACHR", "CRML", "FLNC",
        "RGTX", "AMDL", "ABAT", "GSIT", "ELBM", "BETR", "RBLX", "GFS", "UUUU", "RKLB",
        "BABA", "MP", "RDDT", "CRWV", "AMD", "LAES", "TSLA", "AEM", "SEPN", "AG",
        "LAWR", "UNH", "SNAP", "UNHG", "AAPL", "GRDN", "NVDA", "ARM", "TSMU", "JOBY",
        "BTQ", "NVDL", "CCCX", "CAN", "CLSK", "NBIS", "AMPX", "BITF", "EOSE", "IREN",
        "BURU", "TTMI", "GLW", "AEP", "TSEM", "ALAB", "NUAI", "RMBS", "QQQ", "SIDU",
        "SKYT", "POET", "DXYZ", "LITE", "STI", "QS", "DFLI", "APLS", "RTX", "VOO",
        "GLD", "UVXY", "VGT", "SQQQ", "SPMO", "TE"
    ]

    # Note: Some tickers like SNDK (SanDisk) are delisted/acquired.
    # UNHG and TSMU appear to be typos or specific foreign listings not on standard US exchanges.
    # The script handles these via try-except blocks.

    analyzer = InstitutionalAnalyzer(tickers_list)
    analyzer.run_analysis()





#
# “你是一名顶级投行的高级股票研究分析师，可以访问 Bloomberg、FactSet 以及 SEC 文件。每一个指标都必须标注数据来源和日期。如果数据不可获取或可能已过期，请明确说明。不要估算或编造任何数字。
#
# 请对 [股票代码 / 公司名称] 进行完整分析。
#
# 第 1 步 —— 公司概览：
# → 用通俗易懂的语言解释这家公司是做什么的
# → 业务模式，以及所有收入来源，并按总收入百分比拆分
# → 用一句话总结其核心竞争优势
#
# 第 2 步 —— 关键财务数据（每个数字都要注明来源和日期）：
# → 营收（TTM 以及最近一个季度）
# → 净利润和每股收益（EPS）
# → 市盈率（P/E）、预期市盈率（Forward P/E）、市销率（P/S）、PEG 比率
# → 资产负债率（Debt-to-Equity）和总债务
# → 自由现金流（TTM）
# → 与去年同期季度的同比对比
#
# 第 3 步 —— 股价表现：
# → 价格变动：1 个月、3 个月、6 个月、1 年、年初至今（附精确百分比变化）
# → 52 周最高价和最低价
# → 与标普 500 同期表现对比
# 第 4 步 —— 华尔街一致预期：
# → 覆盖该股票的分析师数量
# → 买入 / 持有 / 卖出评级分布
# → 平均目标价、最高目标价、最低目标价
# → 最近一次分析师上调或下调评级（注明机构名称和日期）
#
# 第 5 步 —— 机构资金动向：
# → 前 5 大机构持仓者及其上季度持仓变动情况
# → 是否有值得关注的对冲基金动向（新建仓或清仓）
# 请使用清晰的 Markdown 标题结构，在适当位置使用表格，并在每一个指标后标注来源。若数据超过 30 天，请标记提示。”


# 2 / 财务报表深度拆解
#
# 每个对冲基金经理都会认真读财报。现在你也可以：
#
# “你是一名顶级投行的高级股票研究分析师。请为每一个财务指标标注其精确来源（SEC 文件、财报或金融数据库）以及报告日期。不要估算任何数字。如果某项指标不可获取，请明确说明，而不是猜测。
#
# 请分析 [公司名称 / 股票代码] 最新的财务报表。
#
# 第 1 步 —— 利润表分析：
# → 最近 4 个季度的营收及精确数值与同比增长率
# → 每个季度的毛利率、营业利润率和净利率
# → 趋势方向：利润率是在扩张、稳定还是收缩？变化幅度是多少？
# → 研发支出占营收比例（如适用）
#
# 第 2 步 —— 资产负债表健康状况：
# → 总资产 vs 总负债
# → 流动比率和速动比率
# → 账上现金及短期投资
# → 总债务及债务到期结构（何时到期？）
# → 商誉占总资产比例（若超过 30%，需标记提示）
#
# 第 3 步 —— 现金流真实性检查：
# → 经营现金流（TTM）
# → 资本支出（TTM）
# → 自由现金流（TTM）及 FCF 利润率
# → 现金用途：回购、分红、并购、还债、研发
# → 与去年相比，现金流是在增长还是下降？
#
# 第 4 步 —— 风险信号（逐项明确检查）：
# → 营收增长但现金流下降？⚠️
# → 债务增长速度快于营收？⚠️
# → 应收账款增长快于营收？⚠️
# → 在营收未增长情况下库存积压？⚠️
# → 频繁一次性费用或经调整利润与 GAAP 差异显著？⚠️
# → 审计机构更换或出具保留意见？⚠️
#
# 第 5 步 —— 积极信号：
# → 利润率环比改善
# → 自由现金流增长
# → 债务下降或现金储备增加
# → GAAP 与 Non-GAAP 盈利保持一致
#
# 第 6 步 —— 竞争对比：
# → 将所有关键利润率和财务比率，与公司前三大竞争对手做成表格对比
#
# 最后用通俗易懂的语言总结：这些财务数据讲述了什么故事？这家公司是在变得更健康，还是更脆弱？请使用清晰的表格格式，并为每个数字标注来源。”


# 3 / 财报解读分析器
#
# 财报季往往一片混乱。用这个提示词，快速抓住重点：
#
# “你是一名负责 [行业] 的高级股票研究分析师。每一个数字都必须标注来源。必须清楚区分已确认的实际披露数据与前瞻性预测。不要编造任何引用或财务指标。
#
# 请分析 [公司名称 / 股票代码] 最近一次财报。
#
# 第 1 步 —— 核心数据：
# → 营收：市场预期 vs 实际结果，是超预期还是不及预期？差额是多少（美元和百分比）
# → 每股收益（EPS）：预期 vs 实际，是超预期还是不及预期？差额是多少
# → 是否存在一次性项目影响利润？调整后数据与 GAAP 数据有何差异？
#
# 第 2 步 —— 前瞻指引：
# → 管理层是上调、下调还是维持业绩指引？
# → 下一季度指引：营收区间和 EPS 区间
# → 全年指引：相比上一季度是否发生变化？
# → 管理层使用的措辞（乐观、谨慎、不确定等）
#
# 第 3 步 —— 业务板块拆解：
# → 各业务板块表现：哪些增长，哪些下滑？幅度是多少？
# → 是否强调了新的业务板块、产品线或地区市场？
# → 哪个板块对超预期或不及预期贡献最大？
#
# 第 4 步 —— 管理层评论（必须引用真实电话会议纪要）：
# → CEO 核心信息（1–2 句话）
# → CFO 对财务前景的核心表述（1–2 句话）
# → 是否提到新的战略重点、转型方向或潜在风险？
# → 语气评估：自信、谨慎、防御性还是回避问题？
#
# 第 5 步 —— 市场与分析师反应：
# → 盘后及下一交易日股价变动（精确百分比）
# → 财报后上调或下调评级的分析师（机构名称、旧评级 → 新评级、新目标价）
# → 分析师问答环节的关键主题
#
# 第 6 步 —— 最终结论：
# → 本次财报中最重要的一个数字是什么？为什么？
# → 这是一个真正强劲的季度，还是“表面好看”？解释原因
# → 根据管理层表述，下个季度最值得关注什么？
# 请使用清晰的 Markdown 标题结构并标注来源。如财报电话会议纪要尚未发布，请明确标记说明。”
#
# 4 / 行业与板块对比分析
#
# 永远不要孤立地分析一只股票。把它放到竞争格局中对比：
#
# “你是一名高级股票研究分析师，正在撰写行业竞争格局报告。每一个指标都必须标注来源和日期。仅使用最新披露的数据。不要估算或插值任何缺失数据，若无法获取请标注为 ‘N/A 未公开披露’。
#
# 请比较 [股票1] vs [股票2] vs [股票3] 在 [行业/板块] 中的表现。
#
# 第 1 步 —— 建立对比表格（每家公司包含以下列）：
# → 市值
# → TTM 营收及同比增长率
# → 毛利率、营业利润率、净利率
# → 市盈率（P/E）、预期市盈率（Forward P/E）、市销率（P/S）、EV/EBITDA、PEG 比率
# → 资产负债率（Debt-to-Equity）及净负债
# → 自由现金流及 FCF 收益率
# → 该行业关键增长指标（例如：订阅用户数、活跃用户数、预订量、销量等）
#
# 第 2 步 —— 竞争定位：
# → 每家公司的核心竞争壁垒（moat）是什么？
# → 市场份额排名（如有数据请注明来源）
# → 哪家公司正在提升市场份额？哪家正在流失份额？
#
# 第 3 步 —— 风险对比：
# → 未来 12 个月每家公司最大的单一风险是什么？
# → 哪家公司债务风险最高？
# → 哪家公司竞争风险最高？
#
# 第 4 步 —— 排名与结论：
# → 最具价值标的（在关键估值指标相对增长下最便宜）
# → 增长潜力最高（营收和盈利轨迹最强）
# → 最安全选择（资产负债表最强、业务最稳定）
# → 综合赢家及原因 —— 给出明确判断
#
# 请使用结构清晰的 Markdown 表格格式呈现所有数据，并为每个数字标注来源和日期。若任何指标数据早于最近一个季度，请特别标记。”


# 5 / 估值模型构建器
#
# “这只股票是高估还是低估？”——现在你可以真正回答这个问题：
#
# “你是一名高级股票研究分析师，正在构建一套估值模型。请透明展示每一个假设，并说明其来源和逻辑。不要使用凭空假设的增长率或折现率。如果必须做出假设，请明确标注为 [ASSUMPTION]，并解释为什么选择该数值及其支持来源。
#
# 请为 [公司名称 / 股票代码] 构建一份完整估值分析。
#
# 第 1 步 —— 现金流折现模型（DCF）：
# → 起始自由现金流（注明来源：最近一期 10-K 或 10-Q）
# → 第 1–5 年营收增长率假设（逐项注明来源：分析师一致预期、公司指引或历史趋势）
# → 自由现金流利润率假设（引用历史平均水平及未来变化预期）
# → 永续增长率：明确具体数值及理由（通常为 2–3%，需说明选择依据）
# → 折现率（WACC）：展示完整计算过程，包括股权成本、债务成本及资本结构（注明 Beta、无风险利率、股权风险溢价来源）
# → 计算 DCF 推导出的隐含每股价值
# → 敏感性分析表：展示 3 种不同 WACC × 3 种不同永续增长率下的估值变化
#
# 第 2 步 —— 可比公司估值法：
# → 选择 5 家最接近的可比公司（说明选择理由）
# → 对比当前 P/E、P/S 和 EV/EBITDA 倍数
# → 计算若该股票按同行平均、同行中位数、溢价/折价交易时的合理价格
# → 判断该股票当前相对于同行是溢价还是折价，并解释是否合理
#
# 第 3 步 —— 历史估值对比：
# → 当前市盈率 vs 公司自身 5 年平均市盈率
# → 是否高于或低于历史区间？
# → 过去估值高点和低点的成因是什么？
#
# 第 4 步 —— 分析师目标价：
# → 华尔街最高、最低和中位目标价（注明机构名称和日期）
# → 过去 90 天内更新目标价的分析师数量
#
# 第 5 步 —— 三种情景分析：
# → 乐观情景（Bull Case）：若增长加速，合理价值是多少？明确列出假设
# → 基准情景（Base Case）：基于一致预期的合理价值是多少？列出假设
# → 悲观情景（Bear Case）：若增长放缓或风险兑现，合理价值是多少？列出假设
# → 当前股价相对于每种情景的上涨/下跌空间（百分比）
# 最终结论：高估 / 合理估值 / 低估 —— 幅度是多少？信心等级（高/中/低）。
# 请解释一个最有可能改变该结论的关键变量。
#
# 请使用清晰的标题结构、标注清楚的表格，并为每一个假设提供来源说明。”

6 / 股息与被动收入分析器

适合希望“持有就能收钱”的投资者：

“你是一名专注于收益型与股息投资的高级股票研究分析师。每一个指标都必须标注来源和日期。不要估算股息率或分红预测——仅使用已披露数据和明确说明的假设。

请从股息投资角度分析 [公司名称 / 股票代码]。

第 1 步 —— 当前股息概况：
→ 当前每股年度股息及按最新股价计算的股息率
→ 股息发放频率（季度、月度或半年）
→ 除息日及下一次派息日

第 2 步 —— 股息增长记录：
→ 股息增长率：1 年、3 年、5 年、10 年复合增长率（CAGR）
→ 连续提高股息的年数
→ 是否属于“股息贵族”（连续 25+ 年增长）或“股息之王”（连续 50+ 年增长）？
→ 过去 20 年中最大一次股息上调幅度，以及是否曾出现削减或暂停分红

第 3 步 —— 可持续性检验：
→ 派息率（基于净利润）：盈利中有多少比例用于分红？
→ 现金流派息率：自由现金流中有多少比例用于分红？
→ 派息率趋势：稳定、上升还是下降？若高于 75% 请标记风险
→ 债务/EBITDA：债务上升是否可能威胁分红？
→ 利息保障倍数：公司是否能轻松覆盖债务利息并继续分红？

第 4 步 —— 同行业对比：
→ 将股息率、增长率、派息率和自由现金流覆盖率，与同一行业前 5 大股息股进行对比（表格形式）

第 5 步 —— 收入预测（清晰展示计算过程）：
→ 若今天投资 10,000 美元并启用股息再投资（DRIP）：
→ 预计 5 年、10 年、20 年后的年度股息收入
→ 假设：使用过去 5 年平均股息增长率（注明具体数值）
→ 逐步展示计算过程

第 6 步 —— 风险评估：
→ 哪些具体情景可能导致削减股息？
→ 公司当前在派息率和债务指标上距离“危险区”有多近？
→ 管理层是否公开承诺维持或增长股息政策？

美股投资网最终结论：强收益型股票 / 中等收益型股票 / 风险较高 —— 并用 2–3 句话解释原因。请标注所有数据来源。”


7 / 风险与红旗扫描器

每只股票在出问题之前，看起来都很好。提前找到风险，而不是等风险找到你：

“你是一名顶级投行的高级风险分析师，正在进行尽职调查。你提出的每一个风险点都必须有数据、监管文件或可信报道作为证据支持。不要臆测——只有在有实际证据时才标记为风险。如果某项风险目前没有证据支持，请标注为 ‘暂无当前风险 — 持续监控’。

请对 [公司名称 / 股票代码] 进行完整风险分析。

第 1 步 —— 财务健康风险：
→ 债务增速是否快于营收增速？（展示两者增长率并注明来源）
→ 自由现金流是否在下降？（用具体数据展示趋势）
→ 利润率是否在压缩？（展示至少 4 个季度趋势）
→ 现金续航能力：按照当前现金消耗速度，公司还能维持多少个月或几年？
→ 未来 24 个月内是否有大额债务到期？

第 2 步 —— 内部人与机构动向：
→ 过去 6 个月净内部人买入或卖出情况（引用 SEC Form 4 数据）
→ 过去 12 个月是否有高管离职？（CEO、CFO 或董事会成员）
→ 上季度主要机构持仓变化（引用 13F 文件）
→ 当前做空比例（流通股中被做空的百分比）及趋势方向

第 3 步 —— 业务集中度风险：
→ 收入集中度：是否有单一产品/服务贡献超过 40% 收入？
→ 客户集中度：是否有单一客户贡献超过 10% 收入？（查阅 10-K 披露）
→ 地域集中度：收入是否高度依赖某一个国家或地区？

第 4 步 —— 竞争与行业威胁：
→ 最具威胁性的竞争对手是谁？为什么？
→ 是否存在颠覆性技术或商业模式威胁公司？
→ 所在市场是增长、停滞还是萎缩？

第 5 步 —— 监管与法律风险：
→ 是否存在正在进行的诉讼、SEC 调查或监管程序？（注明来源）
→ 是否有即将到来的监管变化可能影响业务？
→ 是否有罚款、和解或合规失败的历史？

第 6 步 —— 会计质量检验：
→ GAAP 盈利与调整后盈利差距有多大？
→ 最近是否更改会计方法或收入确认政策？
→ 审计意见：标准无保留、保留意见或持续经营风险警示？
→ 过去 3 年是否有财报重述？

第 7 步 —— 宏观敏感度：
→ 利率敏感度（该业务是否依赖低利率环境？）
→ 衰退脆弱度（历史衰退期间该股票/行业表现如何？）
→ 汇率风险（国际收入占比多少？）

总体风险评级：低 / 中 / 高 —— 并列出最关键的 3 个原因。

最终问题：如果今天不投资这只股票，最大的单一原因是什么？”

正如 Warren Buffett 的第一条投资原则：不要亏钱。



8 / ETF 与投资组合分析器

别再随便买股票了。建立一个真正有结构、有逻辑的投资组合：

“你是一名顶级财富管理公司的高级投资组合策略师。每一个数据点都必须标注来源。不要编造历史收益率或费用率。如果缺乏历史回测数据，请明确说明。

请分析以下投资组合或 ETF：
[列出持仓及大致配置比例 / 或 ETF 代码]
第 1 步 —— 资产配置拆解：
→ 行业配置：各行业占比多少？若单一行业超过 30%，标记为过度集中
→ 地理暴露：美国本土 vs 国际比例，并列出国际部分的国家级拆分
→ 市值分布：大盘股 / 中盘股 / 小盘股占比
→ 风格暴露：成长型 vs 价值型 vs 混合型

第 2 步 —— 持仓分析：
→ 全组合前 10 大持仓及权重
→ 重叠分析：若持有多个 ETF/基金，哪些股票重复出现？计算实际综合暴露比例
→ 单一个股风险：是否有单一公司占总组合超过 10%？

第 3 步 —— 风险指标：
→ 投资组合 Beta（相对于标普 500）
→ 年化历史波动率
→ 最大回撤（过去 10 年最大峰值到谷值跌幅及时间）
→ 夏普比率（风险调整后收益）
→ 持仓相关性：是否真正分散，还是高度同步波动？

第 4 步 —— 成本分析：
→ 加权平均费用率
→ 在 1 万 / 5 万 / 10 万美元规模下的年度总成本
→ 是否存在更低成本但提供类似敞口的替代品？

第 5 步 —— 收益分析：
→ 综合股息率
→ 在 1 万 / 5 万 / 10 万美元投资下的预计年度收入
→ 整体投资组合的股息增长率

第 6 步 —— 压力测试：
→ 在以下时期该组合表现如何：
→ 2008 年金融危机
→ 2020 年疫情暴跌
→ 2022 年熊市
→ 每次危机后的恢复时间

第 7 步 —— 优化建议：
→ 提出 3 个具体、可执行的优化建议（明确给出 ETF 或股票代码）
→ 每项调整说明：解决了什么问题？代价是什么？

请使用清晰的表格结构展示数据，标注所有来源，并对超过一个季度以上的数据进行标记提示。”

这正是财务顾问每年收费 3,000 美元为客户做的事情。


9 / 宏观与市场情绪扫描器

个股从来不是在真空中波动。理解大环境，才能看清趋势：

“你是一名顶级投行的高级宏观策略师，正在准备晨会简报。每一个数据点都必须标注来源和发布日期。必须区分已确认数据与市场预期/预测，不得将预测当作事实陈述。

请针对 [行业 / 股票 / 投资组合] 提供最新宏观与市场分析。

第 1 步 —— 美联储与利率：
→ 当前联邦基金利率
→ 最近一次美联储决议日期及行动内容
→ 接下来两次 FOMC 会议日期
→ CME FedWatch 工具对下次会议的概率预期（注明当前概率）
→ 利率变化将如何具体影响我的行业/股票？解释传导机制

第 2 步 —— 通胀情况：
→ 最新 CPI 数据：总体与核心（环比与同比，并注明发布日期）
→ 最新 PCE 数据（美联储偏好的指标）
→ 趋势：与过去 3 个月相比是加速、稳定还是放缓？
→ 这些通胀数据对我的行业/股票意味着什么？

第 3 步 —— 经济健康度：
→ 最新 GDP 增速（季度、年化）
→ 失业率及最新非农就业报告要点
→ 消费者信心指数（最新读数及趋势）
→ 是否有衰退信号闪现：收益率曲线、领先经济指数、制造业 PMI

第 4 步 —— 市场内部结构：
→ 标普 500、纳斯达克、道琼斯当前点位及年初至今表现
→ 市场广度：高于 200 日均线的股票比例
→ VIX（恐慌指数）当前水平及其含义
→ 看涨/看跌期权比率（Put/Call Ratio）：偏多还是偏空？
→ 当前上涨/下跌是全面性行情，还是集中于少数权重股？

第 5 步 —— 板块轮动：
→ 当前资金流入最多的板块（注明最新基金流向数据来源）
→ 资金流出最多的板块
→ 机构资金最新配置方向

第 6 步 —— 地缘政治与事件日历：
→ 未来 90 天内可能影响市场的三大地缘政治风险
→ 未来 30 天关键事件：重要经济数据发布、美联储讲话、财报日期、政治事件
→ 哪个事件对我的股票/行业影响最大？

第 7 步 —— 战略结论：
→ 当前市场环境：Risk-On 还是 Risk-Off？
→ 对我的行业/股票而言，宏观环境是顺风还是逆风？
→ 现在应该防御、观望还是进攻？为什么？
→ 本月一个最关键的宏观数据点 —— 可能改变整体判断的变量

请使用清晰的分节标题呈现内容。为每一个数据点标注来源。明确标识哪些是预测，哪些是已确认数据。”

这就是每个对冲基金分析师每天早上收到的晨会简报。


10 / 完整尽职调查报告（终极母提示）

一个提示词，覆盖全部。机构级研究框架：

“你是一名顶级投行（如 Goldman Sachs、Morgan Stanley、JPMorgan Chase）的高级股票研究分析师，正在发布对 [公司名称 / 股票代码] 的首次覆盖正式报告。

规则：
→ 每一个财务指标都必须标注来源和日期
→ 仅使用最新公开披露数据（SEC 文件、财报、公司演示材料）
→ 若数据不可获取，请写明 “Not publicly available”，不得估算
→ 所有前瞻性陈述与假设必须清晰标注为 [ASSUMPTION] 并说明依据
→ 使用结构化 Markdown 标题、表格和要点列表
→ 在撰写前逐步思考每个部分逻辑

SECTION 1 —— 执行摘要
→ 三句话投资逻辑：为什么现在要关注这只股票？
→ 总体评级：Strong Buy / Buy / Hold / Sell
→ 12 个月目标价及计算方法
→ 最大投资亮点 + 最大风险

SECTION 2 —— 业务概览
→ 用通俗语言解释公司业务
→ 按业务板块、产品与地区拆分收入（附百分比）
→ 商业模式：如何赚钱？什么驱动持续收入？
→ 竞争壁垒：为何难以被复制？

SECTION 3 —— 财务深度分析
→ 关键指标表格：最近 4 个季度及 TTM 的营收、净利润、EPS、利润率、自由现金流、债务
→ 所有关键指标同比增长率
→ 资产负债表健康度：现金、债务、流动比率、资产负债率
→ 现金流质量：经营现金流与净利润比率（若显著偏离需标记）
→ 资本配置：管理层如何使用资金？回购、分红、并购、研发？

SECTION 4 —— 增长分析

→ 总可触达市场（TAM）及来源
→ 当前市场份额及趋势
→ 未来 3–5 年关键增长驱动因素
→ 管理层指引 vs 分析师一致预期：谁更乐观？
→ 增长是内生驱动还是依赖并购？

SECTION 5 —— 估值分析
→ DCF 分析（所有假设必须标注并说明来源）
→ 可比公司估值表（至少 5 家同行）
→ 5 年历史估值区间（P/E 波动区间）
→ Bull / Base / Bear 三种情景目标价及假设
→ 当前股价相对每个目标价的上涨/下跌空间

SECTION 6 —— 风险分析

→ 前 5 大实质性风险（按概率与影响排序）
→ 每个风险：触发条件、潜在影响、监测指标
→ 做空比例与内部人交易数据（注明来源）
→ 会计质量风险（如存在）

SECTION 7 —— 催化剂时间表
→ 下一次财报日期
→ 即将发布的产品、监管决定或战略事件
→ 可能影响该股票的宏观事件
→ 未来 12 个月关键催化剂时间线

SECTION 8 —— 最终结论
→ Bull 情景：目标价、必要条件及概率估计
→ Base 情景：目标价及最可能结果（概率估计）
→ Bear 情景：目标价及潜在风险（概率估计）
→ 概率加权期望值目标价计算
→ 最终评级与信心等级：High / Medium / Low
→ 30 秒电梯演讲版投资陈述

最后附上完整数据来源列表。”