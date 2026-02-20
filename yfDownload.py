import yfinance  as yf

def download(ticker,period="2mo" ,interval="1d"):
    data = yf.download(ticker, period="2mo", interval="1d")

