import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 📊 Function to fetch and plot stock data
def plot_stock():
    ticker = entry.get().upper()
    if not ticker:
        messagebox.showerror("Input Error", "Please enter a stock ticker.")
        return

    try:
        data = yf.download(ticker,  period="4mo")
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA50'] = data['Close'].rolling(window=50).mean()

        # Clear previous plots
        for frame in [price_frame, volume_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

        # 📈 Tab 1: Price & Moving Averages
        fig1, ax1 = plt.subplots(figsize=(8, 4))
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
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        # print( data['MA50']),
        # print(data.index.values)
        # print(data['Volume'].values)
        # print(data['Volume'].values[0])
        ax2.bar(data.index.values, data['Volume'].values.squeeze(), color='green')
        ax2.set_title(f'{ticker} Trading Volume')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Volume')

        canvas2 = FigureCanvasTkAgg(fig2, master=volume_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch data: {e}")

# 🖼️ GUI Setup
root = tk.Tk()
root.title("Stock Analysis Dashboard")
root.geometry("900x700")

tk.Label(root, text="Enter Stock Ticker:", font=("Arial", 14)).pack(pady=10)
entry = tk.Entry(root, font=("Arial", 14), width=10)
entry.pack()

tk.Button(root, text="Plot Charts", font=("Arial", 12), command=plot_stock).pack(pady=10)

# 🗂️ Tabs
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

price_frame = tk.Frame(notebook)
volume_frame = tk.Frame(notebook)

notebook.add(price_frame, text="Price & MA")
# notebook.add(volume_frame, text="Volume")

root.mainloop()