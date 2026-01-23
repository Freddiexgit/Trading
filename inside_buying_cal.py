import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

df = pd.read_csv("resource/inside_buying/nasdaq_insider_buying_500_2025-10-13_to_2025-10-16.csv")
df["transactionCode"] != "S"
print(df)