import yfinance as yf
import pandas as pd
# Global variable
symbol_and_df = {}
symbol_and_stock = {}

def get_transaction_df(symbol, period="10mo", interval="4h"):
    """Update the shared variable safely."""
    global symbol_and_df
    df = symbol_and_df.get(symbol)
    if df is None:
        # try:
        #     df = yf.download(symbol, period=period, interval=interval,auto_adjust=True)
        # except Exception as e:
        #     return pd.DataFrame()
        get_stock_obj(symbol,period, interval="4h")

    df =  symbol_and_df[symbol]
    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
    return df


def get_stock_obj(symbol, period="10m", interval="4h"):
    """Update the shared variable safely."""
    global symbol_and_stock ,symbol_and_df
    stock = symbol_and_stock.get(symbol)
    if stock is None:
        stock = yf.Ticker(symbol)
        symbol_and_stock[symbol] = stock
        df = stock.history(period=period, interval=interval)
        symbol_and_df[symbol] = df
    return stock
