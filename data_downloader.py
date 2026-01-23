import yfinance as yf
import pandas as pd
# Global variable
symbol_and_df = {}
symbol_and_stock = {}

def get_transaction_df(symbol, period, interval="4h"):
    """Update the shared variable safely."""
    global symbol_and_df
    df = symbol_and_df.get(symbol)
    if df is None:
        try:
            df = yf.download(symbol, period=period, interval=interval)
        except Exception as e:
            return pd.DataFrame()
        df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
        symbol_and_df[symbol] = df
    return df


def get_stock_obj(symbol):
    """Update the shared variable safely."""
    global symbol_and_stock
    stock = symbol_and_stock.get(symbol)
    if stock is None:
        stock = yf.Ticker(symbol)
        symbol_and_stock[symbol] = stock
    return stock
