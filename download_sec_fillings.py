import requests
import os

# -----------------------------
# Config
# -----------------------------
date = "2025-10-21"  # Format: YYYY-MM-DD
save_folder = f"sec_filings_{date.replace('-', '')}"
os.makedirs(save_folder, exist_ok=True)

# SEC EDGAR Full Text Search API for filings by date
# Example: https://efts.sec.gov/LATEST/search-index
search_url = "https://efts.sec.gov/LATEST/search-index"
headers = {"User-Agent": "Python SEC Downloader", "Accept": "application/json"}

query = {
    "query": {
        "query_string": {
            "query": f"filedAt:{date}"
        }
    },
    "from": 0,
    "size": 100  # number of filings per request
}

r = requests.post(search_url, headers=headers, json=query)
data = r.json()

filings = data.get("hits", {}).get("hits", [])
print(f"Found {len(filings)} filings on {date}")

# -----------------------------
# Download filings
# -----------------------------
base_url = "https://www.sec.gov/Archives/"
for i, filing in enumerate(filings):
    file_path = filing["_source"]["fileUrl"]
    full_url = base_url + file_path
    company = filing["_source"]["entityName"].replace(" ", "_")
    form_type = filing["_source"]["formType"].replace(" ", "")

    r_file = requests.get(full_url, headers=headers)
    filename = os.path.join(save_folder, f"{company}_{form_type}_{i + 1}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(r_file.text)
    print(f"Downloaded: {filename}")