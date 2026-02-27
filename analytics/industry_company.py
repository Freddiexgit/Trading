import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

df_all = pd.read_csv("../resource/all_us_stock_info.csv")
df_my_vip = pd.read_csv("../resource/nyse_and_nasdaq_top_500.csv")
#
df_filtered_by_vip = ~df_my_vip['symbol'].isin(df_all['symbol'])
print(df_filtered_by_vip)

# df_industry_from_vip = df_all[df_all['industry'].isin(df_filtered_by_vip["industry"])]
# df_industry_from_vip = df_industry_from_vip.sort_values(by="industry").reset_index(drop=True)
# df_industry_from_vip = df_industry_from_vip[df_industry_from_vip["industry"] != "Shell Companies"]
# print(df_industry_from_vip)



# for industry, group_df in df_all.groupby('industry'):
#     file_name = f"{industry}.csv"
#     group_df.columns.values[0] = "symbol"
#     group_df["marketCap"] = group_df["marketCap"].astype("float64")
#     group_df = group_df.sort_values(by="marketCap", ascending=False)
#     group_df["marketCap_str"] = ( (group_df["marketCap"] / 1_000_000_000) .round(3) .astype(str) + "B" )
#     group_df.to_csv(f"../resource/industries/{file_name}", index=False)
#     print(f"Saved {file_name}")


