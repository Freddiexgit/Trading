import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

df_all = pd.read_csv("../resource/stocks_by_industry.csv")
# df_my_vip = pd.read_csv("../resource/my_vip.csv")
#
# df_filtered_by_vip = df_all[df_all['ticker'].isin(df_my_vip['symbol'])]
# df_industry_from_vip = df_all[df_all['industry'].isin(df_filtered_by_vip["industry"])]
# df_industry_from_vip = df_industry_from_vip.sort_values(by="industry").reset_index(drop=True)
# df_industry_from_vip = df_industry_from_vip[df_industry_from_vip["industry"] != "Shell Companies"]
# print(df_industry_from_vip)



for industry, group_df in df_all.groupby('industry'):
    file_name = f"{industry}.csv"
    group_df.to_csv(f"../resource/industries/{file_name}", index=False)
    print(f"Saved {file_name}")