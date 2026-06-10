def rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))



import pandas as pd

def merge_csv_symbols(file_a_path, file_b_path):
    # 1. Read both CSV files
    df_a = pd.read_csv(file_a_path)
    df_b = pd.read_csv(file_b_path)

    # 2. Combine the dataframes
    # This appends the symbols from file B to file A
    combined_df = pd.concat([df_a, df_b])

    # 3. Remove duplicates
    # This keeps only the first occurrence of each symbol
    unique_df = combined_df.drop_duplicates(subset=['symbol'])

    # 4. Write the results back to file A
    unique_df.to_csv(file_a_path, index=False)
    print(f"Successfully merged symbols into {file_a_path}. Total unique symbols: {len(unique_df)}")

# Usage:
merge_csv_symbols('us_top_5000.csv', 'us_vip_industries.csv')