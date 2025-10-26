import requests
import os
from datetime import datetime

# -----------------------------
# Config
# -----------------------------
date_str = "20251024"  # Format: YYYYMMDD
save_folder = f"resource\sec_filings_{date_str}"
os.makedirs(save_folder, exist_ok=True)

# SEC provides daily index files in the "edgar/daily-index" path
# Example URL: https://www.sec.gov/Archives/edgar/daily-index/2025/QTR4/master.20251024.idx
# Need to determine quarter
def get_quarter(month):
    if month in [1,2,3]: return "QTR1"
    if month in [4,5,6]: return "QTR2"
    if month in [7,8,9]: return "QTR3"
    return "QTR4"

year = int(date_str[:4])
month = int(date_str[4:6])
quarter = get_quarter(month)

master_idx_url = f"https://www.sec.gov/Archives/edgar/daily-index/{year}/{quarter}/master.{date_str}.idx"
headers = {"User-Agent": "Python SEC Downloader"}
r = requests.get(master_idx_url, headers=headers)

if r.status_code != 200:
    raise Exception(f"Index file not found: {master_idx_url}")

# -----------------------------
# Parse the index file
# -----------------------------
lines = r.text.splitlines()
filings = []

# Skip header until line with 'CIK|Company Name|Form Type|Date Filed|Filename'
for i, line in enumerate(lines):
    if line.startswith("CIK|"):
        start_idx = i + 1
        break

for line in lines[start_idx:]:
    parts = line.split("|")
    if len(parts) == 5:
        cik, company, form_type, filed_date, file_path = parts
        filings.append({
            "cik": cik,
            "company": company,
            "form_type": form_type,
            "file_date": filed_date,
            "file_path": file_path
        })

print(f"Found {len(filings)} filings on {date_str}")

# -----------------------------
# Download the filings
# -----------------------------
base_url = "https://www.sec.gov/Archives/"
for i, filing in enumerate(filings[:50]):  # Limit first 50 for demo; remove [:50] to download all
    file_url = base_url + filing["file_path"]
    r = requests.get(file_url, headers=headers)
    filename = os.path.join(save_folder, f"{filing['cik']}_{filing['form_type']}_{i+1}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(r.text)
    print(f"Downloaded: {filename}")