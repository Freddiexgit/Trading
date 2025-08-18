import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.gridspec as gridspec
import yfinance as yf


# === Indicator Functions ===
def compute_indicators(df):
    df = df.copy()

    # EMA
    df['EMA20'] = df['Close'].ewm(span=20).mean()

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # RSI
    delta = df['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(14).mean()
    avg_loss = pd.Series(loss).rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    return df


# === Plot Function for One Stock ===
def plot_stock_dashboard(df, ticker):
    df = compute_indicators(df)

    fig = plt.figure(figsize=(12, 10))
    fig.suptitle(f"{ticker} Dashboard", fontsize=14)

    # Grid: 4 rows total
    gs = gridspec.GridSpec(4, 1, height_ratios=[3, 1, 1, 1])

    # --- Subplot 1+2: Candlestick + Volume (shared) ---
    ax1 = plt.subplot(gs[0])  # price
    ax2 = plt.subplot(gs[1], sharex=ax1)  # volume

    mpf.plot(
        df,
        type='candle',
        ax=ax1,
        volume=ax2,
        mav=(20,),
        ylabel="Price",
        show_nontrading=False
    )

    # --- Subplot 3: MACD ---
    ax3 = plt.subplot(gs[2], sharex=ax1)
    print(df.index)
    ax3.plot(df.index, df['MACD'], label='MACD', color='blue')
    ax3.plot(df.index, df['Signal'], label='Signal', color='red')
    ax3.axhline(0, color='gray', linewidth=1)
    ax3.legend()
    ax3.set_title("MACD")

    # --- Subplot 4: RSI ---
    ax4 = plt.subplot(gs[3], sharex=ax1)
    ax4.plot(df.index, df['RSI'], label='RSI', color='purple')
    ax4.axhline(70, color='red', linestyle='--')
    ax4.axhline(30, color='green', linestyle='--')
    ax4.set_ylim([0, 100])
    ax4.set_title("RSI")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    return fig

# === Example: Multiple Stocks in One PDF ===
# Dummy TSLA
# df_tsla = {
#     "Date": ["2025-07-18", "2025-07-21", "2025-07-22", "2025-07-23", "2025-07-24"],
#     "Open": [321.66, 334.39, 329.74, 330.90, 310.00],
#     "High": [330.89, 338.00, 335.41, 336.20, 310.15],
#     "Low": [321.42, 326.88, 321.55, 328.67, 300.41],
#     "Close": [329.65, 328.49, 332.11, 332.56, 305.30],
#     "Volume": [94255000, 75768800, 77370400, 92553800, 156966000]
# }
period = "5mo"
df_tsla = yf.download("tsla", period=period)
print(df_tsla.index)
print(df_tsla.columns)
df_tsla.columns = df_tsla.columns.droplevel("Ticker")

print(df_tsla.index)
print(df_tsla.columns)
# df_tsla.columns = df_tsla.columns.droplevel(0)
print(df_tsla)

# df_tsla['Date'] = pd.to_datetime(df_tsla['Date'])
# df_tsla.set_index('Date', inplace=True)

# Dummy AAPL
# df_aapl = yf.download("aapl", period=period)
# df_aapl.columns = df_aapl.columns.droplevel("Ticker")
# df_tsla['Date'] = pd.to_datetime(df_tsla['Date'])
# df_tsla.set_index('Date', inplace=True)
# Dummy GOOG
# df_goog = yf.download("goog", period=period)
# df_goog.columns = df_goog.columns.droplevel("Ticker")
# df_tsla['Date'] = pd.to_datetime(df_tsla['Date'])
# df_tsla.set_index('Date', inplace=True)

# Save multipage PDF
with PdfPages("stocks_dashboard.pdf") as pdf:
    for ticker, df in {"TSLA": df_tsla}.items():
        fig = plot_stock_dashboard(df, ticker)
        pdf.savefig(fig)
        plt.close(fig)

print("✅ Multi-stock dashboard saved to stocks_dashboard.pdf")