from time import sleep

import yfinance as yf
import pandas as pd




# Global variable
symbol_and_df = {}
symbol_and_stock = {}
global_period = None
global_interval = None

def get_transaction_df(symbol, period="12mo", interval="1d"):
    """Update the shared variable safely."""
    if global_period and global_interval:
        period = global_period
        interval = global_interval
    df = symbol_and_df.get(symbol)
    if df is None:
        # try:
        #     df = yf.download(symbol, period=period, interval=interval,auto_adjust=True)
        # except Exception as e:
        #     return pd.DataFrame()
        get_stock_obj(symbol,period, interval)

    df =  symbol_and_df[symbol]
    if(len(df) < 1):
        try:
            df =  yf.download(symbol, period=period, interval=interval,auto_adjust=True)

        except Exception  as e:
            return pd.DataFrame()
        symbol_and_df[symbol] = df

    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    return df


def get_stock_obj(symbol, period="10mo", interval="1d"):
    """Update the shared variable safely."""
    global symbol_and_stock ,symbol_and_df, global_period, global_interval
    if  global_period and  global_interval:
        period = global_period
        interval = global_interval
    stock = symbol_and_stock.get(symbol)
    if stock is None:
        stock = yf.Ticker(symbol)

        symbol_and_stock[symbol] = stock
        df = stock.history(period=period, interval=interval)
        symbol_and_df[symbol] = df
    return stock



if __name__ == "__main__":
    # Example usage
    # ticker_file_name = "nzx_tickers"
    # ticker_file_name = "my_vip"
    # ticker_file_name = "my_watch_list"
    # ticker_file_name = "nyse_and_nasdaq_top_500"
    # ticker_file_name = "us_top_3000"
    # ticker_file_name = "my_owned"
    ticker_file_name = "nzx_tickers"
    ticker_file_name_full = f"{ticker_file_name}.csv"
    input_file = f"resource/{ticker_file_name_full}"
    watch_list = pd.read_csv(f"{input_file}")['symbol'].tolist()
    error_list = []
    for ticker in watch_list:
        try:
            df = get_stock_obj(ticker)
        except Exception as e:
            error_list.append(ticker)
            print(ticker)
    watch_list = list(set(watch_list) - set(error_list))
    pd.DataFrame(watch_list, columns=['symbol']).to_csv(f"resource/{ticker_file_name_full}", index=False)
    # st = get_stock_obj("AMDL")
    # print(st.get_info())
    #
    # sleep(1)
    # print(get_transaction_df("AMDL"))