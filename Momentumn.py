import pandas as pd
import numpy as np
import yfinance as yf


def calculate_indicators_and_signals(df, breakout_period=20):
    """
    计算 10 EMA、顺势突破信号，以及 52 周高点过滤
    """
    df = df.copy()

    # 1. 计算 10 EMA (作为核心止损线)
    df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
    # 使用昨天的 10 EMA 作为今天的有效盘中止损价，避免未来数据
    df['stop_level'] = df['ema_20'].shift(1)

    # 2. 计算趋势过滤 (Trend Filter)
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['is_uptrend'] = (df['close'] > df['sma_20']) & (df['sma_20'] > df['sma_50'])

    # 3. 计算动量突破 (Momentum Breakout)
    df['past_high'] = df['high'].shift(1).rolling(window=breakout_period).max()
    df['is_breakout'] = df['close'] > df['past_high']

    # 4. 一年期高点过滤 (52-Week High Filter)
    df['yearly_high'] = df['high'].rolling(window=252, min_periods=1).max()
    df['near_yearly_high'] = df['close'] >= (df['yearly_high'] * 0.97)

    # 5. 最终买入信号
    df['buy_signal'] = df['is_uptrend'] & df['is_breakout'] & (~df['near_yearly_high'])

    # 清理不再需要的中间列
    df.drop(columns=['past_high'], inplace=True)

    return df


def backtest_ema_trailing_stop(df):
    """
    支持持续加仓的回测逻辑，遇到 10 EMA 止损全抛
    """
    current_shares = 0
    total_cost = 0.0

    actions = []
    executed_stop_prices = []
    pnl_list = []
    shares_held = []

    for index, row in df.iterrows():
        current_open = row['open']
        current_low = row['low']
        current_close = row['close']

        # 今天的触发止损价 (即昨天的 10 EMA)
        current_stop = row['stop_level']

        action_today = 'WAIT'
        pnl_today = np.nan

        if pd.isna(current_stop):
            actions.append(action_today)
            executed_stop_prices.append(np.nan)
            pnl_list.append(pnl_today)
            shares_held.append(current_shares)
            continue

        # 1. 检查持仓与盘中止损
        if current_shares > 0:
            if current_low <= current_stop:
                # 盘中跌破 10 EMA，触发止损
                # 处理跳空低开：如果开盘就已经在 10 EMA 之下，按开盘价成交
                exit_price = current_open if current_open < current_stop else current_stop
                pnl_today = (exit_price * current_shares) - total_cost

                action_today = f'SELL ALL ({current_shares} shs)'

                # 清空状态
                current_shares = 0
                total_cost = 0.0
            else:
                action_today = 'HOLD'

        # 2. 检查买入信号
        if row['buy_signal']:
            current_shares += 1
            total_cost += current_close

            if current_shares == 1:
                action_today = 'BUY'
            else:
                # 趋势延续，金字塔加仓
                action_today = 'BUY (Add)'

        actions.append(action_today)
        executed_stop_prices.append(current_stop)
        pnl_list.append(pnl_today)
        shares_held.append(current_shares)

    df['action'] = actions
    df['trailing_stop_price'] = executed_stop_prices
    df['pnl'] = pnl_list
    df['shares_held'] = shares_held
    return df


# ==========================================
# 真实数据回测模块
# ==========================================
if __name__ == "__main__":
    tickers = ['AAOI', 'LITE', 'TLSA', 'ENLT']

    for ticker in tickers:
        print(f"\n{'=' * 80}")
        print(f"[{ticker}] 10 EMA 追踪止损策略回测")
        print(f"{'=' * 80}")

        try:
            stock = yf.Ticker(ticker)
            df_raw = stock.history(period="max")

            if df_raw.empty:
                print(f"未能获取到 {ticker} 的数据。")
                continue

            df_data = df_raw.reset_index()
            df_data.columns = [col.lower() for col in df_data.columns]

            # 运行指标计算和回测
            df_signals = calculate_indicators_and_signals(df_data, breakout_period=20)
            df_result = backtest_ema_trailing_stop(df_signals)

            # 提取近 3 年的交易记录进行展示
            three_years_ago = pd.Timestamp.now(tz=df_result['date'].dt.tz) - pd.DateOffset(years=3)
            df_recent = df_result[df_result['date'] >= three_years_ago]

            trades = df_recent[df_recent['action'].str.contains('BUY|SELL')].copy()

            if trades.empty:
                print(f"{ticker} 在过去 3 年中没有触发交易记录。")
            else:
                # 打印出 ema_20 和 stop_level (即昨天的 ema_20) 方便核对逻辑
                trades_to_print = trades[
                    ['date', 'close', 'ema_20', 'trailing_stop_price', 'action', 'shares_held', 'pnl']]
                trades_to_print['date'] = trades_to_print['date'].dt.strftime('%Y-%m-%d')

                trades_to_print['close'] = trades_to_print['close'].round(2)
                trades_to_print['ema_20'] = trades_to_print['ema_20'].round(2)
                trades_to_print['trailing_stop_price'] = trades_to_print['trailing_stop_price'].round(2)
                trades_to_print['pnl'] = trades_to_print['pnl'].round(2)

                trades_to_print['trailing_stop_price'] = trades_to_print['trailing_stop_price'].fillna('')
                trades_to_print['pnl'] = trades_to_print['pnl'].fillna('')

                # 重命名列名让输出更清晰
                trades_to_print = trades_to_print.rename(columns={'trailing_stop_price': 'stop_level(yest_ema)'})

                print("以下为过去 3 年的交易记录：")
                print(trades_to_print.to_string(index=False))

                # 统计总结
                sell_trades = df_recent[df_recent['pnl'].notna()]
                total_sells = len(sell_trades)
                winning_sells = len(sell_trades[sell_trades['pnl'] > 0])
                total_pnl = sell_trades['pnl'].sum()

                print("-" * 80)
                print(f"平仓次数 (近3年): {total_sells}")
                if total_sells > 0:
                    print(f"平仓胜率: {(winning_sells / total_sells) * 100:.2f}%")
                print(f"累计净盈亏 (近3年): ${total_pnl:.2f}")

        except Exception as e:
            print(f"处理 {ticker} 时发生错误: {e}")

    print("\n回测执行完毕。")