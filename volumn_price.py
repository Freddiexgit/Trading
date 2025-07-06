import pandas as pd
import os

folder = "resource/nzx_2025-06-30"
all_entries = os.listdir(folder)

for entry  in all_entries:
    df = pd.read_csv(f'{folder}/{entry}')
    df['Prev_Value'] = df['close'].shift(1)  # previous row
    df['Price_Diff'] = df['close'] - df['Prev_Value']  # difference
    df['Prev_Value_volume'] = df['volume'].shift(1)  # previous row
    df['Volume_Diff'] = df['volume'] - df['Prev_Value_volume']  # difference
    df = df.drop('Prev_Value', axis=1)
    df = df.drop('Prev_Value_volume', axis=1)
    print(df)
