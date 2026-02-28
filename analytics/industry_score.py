import data_downloader

SECTOR_ETF = {
    "Advertising Agencies": "OMC",
    "Aerospace & Defense": "ITA",
    "Agricultural Inputs": "MOO",
    "Airlines": "JETS",
    "Airports & Air Services": "SEA",
    "Aluminum": "IYM",
    "Apparel Manufacturing": "XRT",
    "Apparel Retail": "XRT",
    "Asset Management": "KIE",
    "Auto & Truck Dealerships": "CARZ",
    "Auto Manufacturers": "CARZ",
    "Auto Parts": "CARZ",
    "Banks - Diversified": "KBE",
    "Banks - Regional": "KRE",
    "Beverages - Brewers": "PBJ",
    "Beverages - Non-Alcoholic": "PBJ",
    "Beverages - Wineries & Distilleries": "PBJ",
    "Biotechnology": "XBI",
    "Broadcasting": "PBS",
    "Building Materials": "XLB",
    "Building Products & Equipment": "XLB",
    "Business Equipment & Supplies": "XLI",
    "Capital Markets": "KCE",
    "Chemicals": "XLB",
    "Coking Coal": "XME",
    "Communication Equipment": "XLC",
    "Computer Hardware": "IYW",
    "Confectioners": "PBJ",
    "Conglomerates": "IYJ",
    "Consulting Services": "IYG",
    "Consumer Electronics": "IYW",
    "Copper": "COPX",
    "Credit Services": "IYG",
    "Department Stores": "XRT",
    "Diagnostics & Research": "XBI",
    "Discount Stores": "XRT",
    "Drug Manufacturers - General": "IHE",
    "Drug Manufacturers - Specialty & Generic": "IHE",
    "Education & Training Services": "IYC",
    "Electrical Equipment & Parts": "XLI",
    "Electronic Components": "SOXX",
    "Electronic Gaming & Multimedia": "ESPO",
    "Electronics & Computer Distribution": "IYW",
    "Engineering & Construction": "PKB",
    "Entertainment": "PEJ",
    "Farm & Heavy Construction Machinery": "MOO",
    "Farm Products": "MOO",
    "Financial Conglomerates": "XLF",
    "Financial Data & Stock Exchanges": "KCE",
    "Food Distribution": "PBJ",
    "Footwear & Accessories": "XRT",
    "Furnishings, Fixtures & Appliances": "XHB",
    "Gambling": "BETZ",
    "Gold": "GDX",
    "Grocery Stores": "KXI",
    "Health Information Services": "XLV",
    "Healthcare Plans": "XLV",
    "Home Improvement Retail": "XHB",
    "Household & Personal Products": "XLP",
    "Industrial Distribution": "XLI",
    "Information Technology Services": "IYW",
    "Infrastructure Operations": "PAVE",
    "Insurance - Diversified": "KIE",
    "Insurance - Life": "KIE",
    "Insurance - Property & Casualty": "KIE",
    "Insurance - Reinsurance": "KIE",
    "Insurance - Specialty": "KIE",
    "Insurance Brokers": "KIE",
    "Integrated Freight & Logistics": "IYT",
    "Internet Content & Information": "FDN",
    "Internet Retail": "IBUY",
    "Leisure": "PEJ",
    "Lodging": "PEJ",
    "Lumber & Wood Production": "WOOD",
    "Luxury Goods": "LUXE",
    "Marine Shipping": "SEA",
    "Medical Devices": "IHI",
    "Medical Distribution": "IHE",
    "Medical Instruments & Supplies": "IHI",
    "Metal Fabrication": "XME",
    "Mortgage Finance": "REM",
    "Oil & Gas Drilling": "XOP",
    "Oil & Gas E&P": "XOP",
    "Oil & Gas Equipment & Services": "XES",
    "Oil & Gas Integrated": "XLE",
    "Oil & Gas Midstream": "AMLP",
    "Oil & Gas Refining & Marketing": "CRAK",
    "Other Industrial Metals & Mining": "XME",
    "Other Precious Metals & Mining": "GDXJ",
    "Packaged Foods": "PBJ",
    "Packaging & Containers": "PKG",
    "Paper & Paper Products": "WOOD",
    "Personal Services": "IYC",
    "Pharmaceutical Retailers": "IHE",
    "Pollution & Treatment Controls": "PAVE",
    "Publishing": "PBS",
    "Railroads": "IYT",
    "Real Estate - Development": "XLRE",
    "Real Estate - Diversified": "XLRE",
    "Real Estate Services": "XLRE",
    "Recreational Vehicles": "PEJ",
    "REIT - Diversified": "VNQ",
    "REIT - Healthcare Facilities": "XLRE",
    "REIT - Hotel & Motel": "PEJ",
    "REIT - Industrial": "VNQI",
    "REIT - Mortgage": "REM",
    "REIT - Office": "VNQ",
    "REIT - Residential": "REZ",
    "REIT - Retail": "RWR",
    "REIT - Specialty": "XLRE",
    "Rental & Leasing Services": "IYC",
    "Residential Construction": "XHB",
    "Resorts & Casinos": "PEJ",
    "Restaurants": "EATZ",
    "Scientific & Technical Instruments": "IYW",
    "Security & Protection Services": "XLI",
    "Semiconductor Equipment & Materials": "SOXX",
    "Semiconductors": "SOXX",
    "Shell Companies": "SPCX",
    "Silver": "SIL",
    "Software - Application": "IGV",
    "Software - Infrastructure": "IGV",
    "Solar": "TAN",
    "Specialty Business Services": "IYG",
    "Specialty Chemicals": "XLB",
    "Specialty Industrial Machinery": "XLI",
    "Specialty Retail": "XRT",
    "Staffing & Employment Services": "IYC",
    "Steel": "SLX",
    "Telecom Services": "XLC",
    "Textile Manufacturing": "XRT",
    "Thermal Coal": "XME",
    "Tobacco": "XLP",
    "Tools & Accessories": "XLI",
    "Travel Services": "AWAY",
    "Trucking": "IYT",
    "Uranium": "URA",
    "Utilities - Diversified": "XLU",
    "Utilities - Independent Power Producers": "XLU",
    "Utilities - Regulated Electric": "XLU",
    "Utilities - Regulated Gas": "XLU",
    "Utilities - Regulated Water": "FIW",
    "Utilities - Renewable": "ICLN",
    "Waste Management": "WM"
}

import os
import  pandas as pd
import data_downloader as dd
from collections import defaultdict
import numpy as np
industry_and_symbol = defaultdict(list)


def sector_strength(sector):

    try:
        etf = SECTOR_ETF.get(sector)
        if etf is None:
            return 0

        df_etf = dd.get_transaction_df(etf)
        df_mkt = dd.get_transaction_df("SPY")

        if df_etf is None or df_etf.empty:
            return 0

        # --- Relative strength ---
        rs = float(
            df_etf["Close"].iloc[-1] /
            df_mkt["Close"].iloc[-1]
        )

        # --- Breadth ---
        members = industry_and_symbol.get(sector, [])

        signals = []

        for t in members:
            try:
                df = dd.get_transaction_df(t)

                if df is None or len(df) < 60:
                    continue

                close = df["Close"].iloc[-1]
                ma50 = df["MA50"].iloc[-1]

                if not np.isnan(ma50):
                    signals.append(close > ma50)

            except:
                continue

        breadth = float(np.mean(signals)) if signals else 0

        # --- Final score ---
        score = 0.6 * rs + 0.4 * breadth

        return float(score)

    except Exception as e:
        print(f"Error calculating strength for {sector}: {e}")
        return 0

def call():


    # Initialize a multimap where values are lists


    base_dir = "../resource/industries/"
    for file in os.listdir(base_dir):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(base_dir, file))
            industry_and_symbol[file.replace(".csv", "")] = df["symbol"].tolist()


    sector_scores = {s: sector_strength(s) for s in industry_and_symbol.keys()}
    sorted_sectors = sorted(sector_scores.items(), key=lambda x: x[1], reverse=True)

    print("=== 行業強弱評分 ===")
    for sector, score in sorted_sectors:
        print(f"{sector}: {score:.4f}")

if __name__     == "__main__":
    # call()

    for s, etf in SECTOR_ETF.items():
        try:
            data_downloader.get_stock_obj(etf)
        except Exception as e:
            print(f"Error fetching data for {s} ({etf}): {e}")





