import os
import glob
import re
file_pattern_base = ''
def get_csv_files(table_name) ->list[str]:
    """
    Utility function to list all CSV files in the current directory.
    This can help users identify which files are available for processing.
    """

    # glob.glob() automatically resolves the '*' wildcards
    file_pattern = f"../output/2026*/*/*/{table_name}_*.csv"
    date_csv_files = {}
    for file_path in glob.glob(file_pattern):
        print(f"Found file: {file_path}")
        date_string = re.sub(f".*{table_name}_", '', file_path)
        if "_weekend" in date_string or "_processed" in date_string:
            continue
        date_string = date_string.replace("_weekend", "")
        date_string = date_string.replace(".csv", "")
        date_csv_files[date_string] = file_path

    return date_csv_files


def rename_files(files):
    for _, file_path in files.items():
        new_file_path = file_path.replace(".csv", "_processed.csv")
        os.rename(file_path, new_file_path)
        print(f"Renamed {file_path} to {new_file_path}")
if __name__     == "__main__":
    files = get_csv_files("ema_trend")
    for date, file in files.items():
        new_file_path = file.replace("ema_trend", "ema_trend_processed")
        os.rename(file, new_file_path)
        print(f"{date}: {file}")