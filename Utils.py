def combine_files():
    import pandas as pd
    import glob
    import os

    # Folder containing CSV files
    input_folder = "resource/vip/"

    # Output file
    output_file = "resource/vip_industries.csv"

    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_folder, "*.csv"))

    if not csv_files:
        print("No CSV files found.")
        exit()

    # Read and combine
    df_list = []

    for file in csv_files:
        print(f"Reading: {file}")
        df = pd.read_csv(file)
        df_list.append(df)

    combined_df = pd.concat(df_list, ignore_index=True)

    # Save
    combined_df.to_csv(output_file, index=False)

    print(f"\nCombined {len(csv_files)} files")
    print(f"Total rows: {len(combined_df)}")
    print(f"Saved to: {output_file}")


if __name__ =="__main__":
    combine_files()