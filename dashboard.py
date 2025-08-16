import tkinter as tk
from tkinter import ttk
import yfinance as yf
import pandas as pd
import mplfinance as mpf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def fetch_data(ticker):
    df = yf.download(ticker, start='2025-05-01', end='2025-08-01')
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    df.dropna(inplace=True)
    return df

def plot_candlestick(df, frame):
    fig = mpf.figure(style='yahoo', figsize=(10, 5))
    ax = fig.add_subplot(1,1,1)
    mpf.plot(df, type='candle', ax=ax, volume=True, mav=(5,10,20,60), show_nontrading=True)
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

def build_dashboard():
    root = tk.Tk()
    root.title("Stock Analysis Dashboard")
    root.geometry("1000x700")

    ticker_entry = tk.Entry(root, font=("Arial", 14))
    ticker_entry.pack(pady=10)

    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    candle_tab = tk.Frame(notebook)
    notebook.add(candle_tab, text="Candlestick")

    def load_data():
        ticker = ticker_entry.get().upper()
        df = fetch_data(ticker)
        for widget in candle_tab.winfo_children():
            widget.destroy()
        plot_candlestick(df, candle_tab)

    tk.Button(root, text="Load Chart", command=load_data).pack()

    root.mainloop()


if __name__ == "__main__":
    build_dashboard()