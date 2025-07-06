from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
pd.set_option('display.max_columns', None)

root_folder = Path("resource/data/nzx_2025-05-27")

# # Recursively find all CSV files
csv_files = list(root_folder.rglob("*.csv"))

# # Load and concatenate all CSVs into one DataFrame
df_map = {}
for file in csv_files:
    if file.name == 'AIR.NZ.csv':
        df = pd.read_csv(file)
        df_map[file.name.replace(".csv", "")] = df

for ticker, data in df_map.items():
    data['9-day'] = data['close'].rolling(9).mean()
    data['21-day'] = data['close'].rolling(21).mean()
    data['signal'] = np.where(data['9-day'] > data['21-day'], 1, 0)
    data['signal'] = np.where(data['9-day'] < data['21-day'], -1, data['signal'])
    data['return'] = np.log(data['close']).diff()
    data['system_return'] = data['signal'] * data['return']
    data['entry'] = data.signal.diff()
    filtered = data[(data['entry'] == 2) & (data['Date'] >= '2025-05-20')]
    # if len(filtered) > 0:
    #     filtered.to_csv((f'resource/result/momentum/{ticker}.csv'), index=False)
    #     print(filtered)

    data.dropna(inplace=True)
    data = data.set_index("Date")
    plt.rcParams['figure.figsize'] = 12, 6
    plt.grid(True, alpha = .3)
    plt.plot(data.iloc[-252:]['close'], label = 'GLD')
    plt.plot(data.iloc[-252:]['9-day'], label = '9-day')
    plt.plot(data.iloc[-252:]['21-day'], label = '21-day')
    plt.plot(data[-252:].loc[data.entry == 2].index, data[-252:]['9-day'][data.entry == 2], '^',
             color = 'g', markersize = 12)
    plt.plot(data[-252:].loc[data.entry == -2].index, data[-252:]['21-day'][data.entry == -2], 'v',
             color = 'r', markersize = 12)
    plt.legend(loc=2)

    plt.show()








