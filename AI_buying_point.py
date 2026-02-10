def identify_buy_signals(df):

    # --- Moving Averages ---
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()

    # --- MACD ---
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_DIF'] = exp1 - exp2
    df['MACD_DEA'] = df['MACD_DIF'].ewm(span=9, adjust=False).mean()
    df['MACD_Cross'] = (df['MACD_DIF'] > df['MACD_DEA']) & \
                       (df['MACD_DIF'].shift(1) <= df['MACD_DEA'].shift(1))

    # --- RSI (Wilder) ---
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()

    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # --- Volume Confirmation ---
    df['Vol_Strength'] = df['Volume'] > df['Volume'].rolling(20).mean()

    # --- Trend Filter ---
    df['Trend_Up'] = df['SMA50'] > df['SMA50'].shift(1)

    # --- Buy Signal Logic ---
    df['Buy_Signal'] = (
        (df['SMA20'] > df['SMA50']) &
        (df['MACD_Cross']) &
        (df['RSI'] > 50) &
        (df['Vol_Strength']) &
        (df['Trend_Up'])
    ).astype(int)

    # --- Entry Point (first bar only) ---
    df['Entry_Point'] = (df['Buy_Signal'] == 1) & (df['Buy_Signal'].shift(1) == 0)

    return df[df['Entry_Point']]
