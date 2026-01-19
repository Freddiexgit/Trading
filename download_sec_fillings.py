import requests
import os
from datetime import datetime

# -----------------------------
# Config
# -----------------------------
target_date = "2025-10-23"  # YYYY-MM-DD
form_types = ["4", "13D", "13G"]
save_folder = "sec_filings_by_date"
os.makedirs(save_folder, exist_ok=True)

# -----------------------------
# Determine quarter
# -----------------------------
date_obj = datetime.strptime(target_date, "%Y-%m-%d")
year = date_obj.year
month = date_obj.month

if month in [1,2,3]:
    quarter = "QTR1"
elif month in [4,5,6]:
    quarter = "QTR2"
elif month in [7,8,9]:
    quarter = "QTR3"
else:
    quarter = "QTR4"

# -----------------------------
# Master index URL
# -----------------------------
date_str = date_obj.strftime("%Y%m%d")
master_url = f"https://www.sec.gov/Archives/edgar/daily-index/{year}/{quarter}/master.{date_str}.idx"
headers = {"User-Agent": "Python SEC Downloader"}

r = requests.get(master_url, headers=headers)
if r.status_code != 200:
    raise Exception(f"Master index not found: {master_url}")

lines = r.text.splitlines()

# -----------------------------
# Parse master index
# -----------------------------
start_idx = 0
for i, line in enumerate(lines):
    if line.startswith("CIK|"):
        start_idx = i + 1
        break

filings = []
for line in lines[start_idx:]:
    parts = line.split("|")
    if len(parts) != 5:
        continue
    cik, company, f_type, filed_date, file_path = parts
    if f_type.strip().upper() in form_types and filed_date == target_date:
        filings.append({
            "cik": cik,
            "company": company,
            "form_type": f_type.strip().upper(),
            "file_path": file_path
        })

print(f"Found {len(filings)} filings on {target_date}")

# -----------------------------
# Download filings
# -----------------------------
for i, filing in enumerate(filings):
    file_url = "https://www.sec.gov/Archives/" + filing["file_path"]
    folder_path = os.path.join(save_folder, filing["form_type"])
    os.makedirs(folder_path, exist_ok=True)

    filename = os.path.join(folder_path, f"{filing['company'].replace(' ','_')}_{filing['form_type']}_{i+1}.txt")
    try:
        r_doc = requests.get(file_url, headers=headers)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(r_doc.text)
        print(f"Downloaded: {filename}")
    except Exception as e:
        print(f"Failed to download {file_url}: {e}")
