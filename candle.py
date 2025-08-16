import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplfinance as mpf
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
# 📊 Function to fetch and plot stock data
def plot_stock():
    ticker = entry.get().upper()
    if not ticker:
        messagebox.showerror("Input Error", "Please enter a stock ticker.")
        return

    try:
        data = yf.download(ticker, period='1mo')
        # dates = data.index.strftime('%Y-%m-%d')
        # data.set_index(dates , inplace=True)
        print(data)
        data['MA20'] = data['Close'].rolling(window=2).mean()
        data['MA50'] = data['Close'].rolling(window=5).mean()
        data.dropna(inplace=True)

        # Clear previous plots
        for frame in [price_frame, volume_frame, candle_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

        # 📈 Tab 1: Price & Moving Averages
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(data['Close'], label='Close Price', color='blue')
        ax1.plot(data['MA20'], label='20-Day MA', color='orange')
        ax1.plot(data['MA50'], label='50-Day MA', color='green')
        ax1.set_title(f'{ticker} Price & Moving Averages')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Price (USD)')
        ax1.legend()
        ax1.grid(True)

        canvas1 = FigureCanvasTkAgg(fig1, master=price_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack()

        # 📊 Tab 2: Volume
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        ax2.bar(data.index.values, data['Volume'].values.squeeze(), color='gray')
        ax2.set_title(f'{ticker} Trading Volume')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Volume')

        canvas2 = FigureCanvasTkAgg(fig2, master=volume_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack()



        # 🕯️ Tab 3: Candlestick Chart
        data.columns = data.columns.droplevel(level="Ticker")
        print(data)
        candle_data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
        print(candle_data.dtypes)

        fig3 = mpf.figure(style='yahoo', figsize=(12, 6))
        ax3 = fig3.add_subplot(1,1,1)
        ax3.set_xticks(candle_data.index)
        mpf.plot(candle_data, type='candle', ax=ax3)
        # mpf.plot(
        #     candle_data,
        #     type='candle',
        #     volume=True,
        #     style='yahoo',  # or 'charles', 'nightclouds', etc.
        #     title='Stock Price with Volume',
        #     ylabel='Price',
        #     ylabel_lower='Volume',
        #     figsize=(12, 6)
        # )

        canvas3 = FigureCanvasTkAgg(fig3, master=candle_frame)
        canvas3.draw()
        canvas3.get_tk_widget().pack()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch data: {e}")

# 🖼️ GUI Setup
root = tk.Tk()
root.title("Stock Analysis Dashboard")
root.geometry("900x750")

tk.Label(root, text="Enter Stock Ticker:", font=("Arial", 14)).pack(pady=10)
entry = tk.Entry(root, font=("Arial", 14), width=10)
entry.pack()

tk.Button(root, text="Plot Charts", font=("Arial", 12), command=plot_stock).pack(pady=10)

# 🗂️ Tabs
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

price_frame = tk.Frame(notebook)
volume_frame = tk.Frame(notebook)
candle_frame = tk.Frame(notebook)

notebook.add(price_frame, text="Price & MA")
notebook.add(volume_frame, text="Volume")
notebook.add(candle_frame, text="Candlestick")

root.mainloop()



# data = {
#     "Open":  [100, 102, 101, 103, 102],
#     "High":  [102, 103, 103, 104, 103],
#     "Low":   [ 99, 101, 100, 102, 101],
#     "Close": [101, 102, 102, 103, 102]
# }
# df = pd.DataFrame(data, index=pd.date_range("2025-08-01", periods=5))
#
# # Plot candlestick
# mpf.plot(df, type="candle", style="charles", title="Candlestick Chart", ylabel="Price")