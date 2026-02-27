import data_downloader

SECTOR_ETF = {
    # --- Advertising / Media / Communication Services ---
    "Advertising Agencies": "XLC",
    "Broadcasting": "XLC",
    "Internet Content & Information": "XLC",
    "Publishing": "XLC",
    "Movies&Entertainment": "XLC",
    "Radio And Television Broadcasting And Communications Equipment": "XLC",
    "Cable & Other Pay Television Services": "XLC",
    "Newspapers&Magazines": "XLC",

    # --- Aerospace / Defense ---
    "Aerospace & Defense": "ITA",
    "Aerospace": "ITA",
    "Military&Government&Technical": "ITA",
    "Ordnance And Accessories": "ITA",

    # --- Agriculture / Food ---
    "Agricultural Inputs": "MOO",
    "Agricultural Chemicals": "MOO",
    "Farm Products": "MOO",
    "Farm & Heavy Construction Machinery": "XLI",
    "Farming&Seeds&Milling": "MOO",
    "Packaged Foods": "PBJ",
    "Specialty Foods": "PBJ",
    "Food Distribution": "PBJ",
    "Meat&Poultry&Fish": "PBJ",
    "Grocery Stores": "KXI",

    # --- Airlines / Transportation ---
    "Airlines": "JETS",
    "Airports & Air Services": "JETS",
    "Air Freight&Delivery Services": "IYT",
    "Integrated Freight & Logistics": "IYT",
    "Marine Shipping": "IYT",
    "Railroads": "IYT",
    "Trucking": "IYT",
    "Trucking Freight&Courier Services": "IYT",
    "Transportation Services": "IYT",
    "Other Transportation": "IYT",

    # --- Metals / Mining / Materials ---
    "Aluminum": "XME",
    "Coking Coal": "XME",
    "Coal Mining": "XME",
    "Copper": "COPX",
    "Gold": "GDX",
    "Silver": "SIL",
    "Metal Fabrication": "XME",
    "Metal Mining": "XME",
    "Other Industrial Metals & Mining": "XME",
    "Other Precious Metals & Mining": "GDX",
    "Other Metals and Minerals": "XME",
    "Steel": "SLX",
    "Steel&Iron Ore": "SLX",
    "Lumber & Wood Production": "WOOD",
    "Paper & Paper Products": "XLB",
    "Building Materials": "XLB",
    "Packaging & Containers": "XLB",
    "Specialty Chemicals": "XLB",
    "Chemicals": "XLB",

    # --- Apparel / Retail / Consumer Discretionary ---
    "Apparel Manufacturing": "XLY",
    "Apparel Retail": "XRT",
    "Apparel": "XLY",
    "Clothing&Shoe&Accessory Stores": "XRT",
    "Department Stores": "XRT",
    "Discount Stores": "XRT",
    "Specialty Retail": "XRT",
    "Other Specialty Stores": "XRT",
    "Luxury Goods": "XLY",
    "Recreational Vehicles": "XLY",
    "Recreational Games&Products&Toys": "XLY",
    "Consumer Electronics&Appliances": "XLY",
    "Consumer Electronics&Video Chains": "XRT",
    "Internet Retail": "IBUY",
    "Restaurants": "EATZ",
    "Leisure": "PEJ",
    "Lodging": "PEJ",
    "Resorts & Casinos": "PEJ",

    # --- Autos ---
    "Auto & Truck Dealerships": "CARZ",
    "Auto Manufacturers": "CARZ",
    "Auto Parts": "CARZ",
    "Auto Parts:O.E.M.": "CARZ",
    "Automotive Aftermarket": "CARZ",
    "Motor Vehicles": "CARZ",
    "Retail-Auto Dealers and Gas Stations": "CARZ",

    # --- Banks / Financials ---
    "Banks - Diversified": "KBE",
    "Banks - Regional": "KRE",
    "Commercial Banks": "KBE",
    "Major Banks": "KBE",
    "Savings Institutions": "KRE",
    "Financial Conglomerates": "XLF",
    "Financial Data & Stock Exchanges": "KCE",
    "Capital Markets": "KCE",
    "Investment Bankers&Brokers&Service": "IAI",
    "Investment Managers": "KCE",
    "Credit Services": "XLF",
    "Mortgage Finance": "XLF",
    "Insurance - Diversified": "KIE",
    "Insurance - Life": "KIE",
    "Insurance - Property & Casualty": "KIE",
    "Insurance - Reinsurance": "KIE",
    "Insurance - Specialty": "KIE",
    "Insurance Brokers": "KIE",

    # --- Healthcare / Biotech ---
    "Biotechnology": "XBI",
    "Diagnostics & Research": "XHE",
    "Drug Manufacturers - General": "IHE",
    "Drug Manufacturers - Specialty & Generic": "IHE",
    "Health Information Services": "XHE",
    "Healthcare Plans": "XLV",
    "Medical Care Facilities": "XLV",
    "Medical Devices": "IHI",
    "Medical Distribution": "XHE",
    "Medical Instruments & Supplies": "IHI",
    "Medical&Dental Instruments": "IHI",
    "Medical Electronics": "IHI",
    "Medical Specialities": "XLV",
    "Hospital&Nursing Management": "XLV",

    # --- Technology ---
    "Communication Equipment": "IYZ",
    "Computer Hardware": "IYW",
    "Consumer Electronics": "XLY",
    "Electronic Components": "SOXX",
    "Electronic Gaming & Multimedia": "ESPO",
    "Electronics & Computer Distribution": "IYW",
    "Information Technology Services": "XLK",
    "Semiconductor Equipment & Materials": "SOXX",
    "Semiconductors": "SOXX",
    "Software - Application": "IGV",
    "Software - Infrastructure": "IGV",

    # --- Energy ---
    "Oil & Gas Drilling": "XOP",
    "Oil & Gas E&P": "XOP",
    "Oil & Gas Equipment & Services": "XES",
    "Oil & Gas Integrated": "XLE",
    "Integrated oil Companies": "XLE",
    "Oil & Gas Midstream": "AMLP",
    "Oil & Gas Refining & Marketing": "CRAK",
    "Oil Refining&Marketing": "CRAK",
    "Oilfield Services&Equipment": "XES",
    "Oil and Gas Field Machinery": "XES",
    "Thermal Coal": "XME",
    "Uranium": "URA",

    # --- Utilities ---
    "Utilities - Diversified": "XLU",
    "Utilities - Independent Power Producers": "XLU",
    "Utilities - Regulated Electric": "XLU",
    "Utilities - Regulated Gas": "XLU",
    "Utilities - Regulated Water": "FIW",
    "Utilities - Renewable": "ICLN",
    "Power Generation": "XLU",
    "Water Supply": "FIW",

    # --- Real Estate ---
    "Real Estate - Development": "XLRE",
    "Real Estate - Diversified": "XLRE",
    "Real Estate Services": "XLRE",
    "Real Estate": "XLRE",
    "REIT - Diversified": "VNQ",
    "REIT - Healthcare Facilities": "XLRE",
    "REIT - Hotel & Motel": "XLRE",
    "REIT - Industrial": "XLRE",
    "REIT - Mortgage": "REM",
    "REIT - Office": "XLRE",
    "REIT - Residential": "REZ",
    "REIT - Retail": "XLRE",
    "REIT - Specialty": "XLRE",

    # --- Industrials ---
    "Building Products & Equipment": "XLI",
    "Building Products": "XLI",
    "Business Equipment & Supplies": "XLI",
    "Construction&Ag Equipment&Trucks": "XLI",
    "Engineering & Construction": "PAVE",
    "Industrial Distribution": "XLI",
    "Industrial Machinery&Components": "XLI",
    "Industrial Specialties": "XLI",
    "Infrastructure Operations": "PAVE",
    "Misc Corporate Leasing Services": "XLI",
    "Miscellaneous manufacturing industries": "XLI",
    "Precision Instruments": "XLI",
    "Professional and commerical equipment": "XLI",
    "Professional Services": "XLI",
    "Tools & Accessories": "XLI",
    "Wholesale Distributors": "XLI",

    # --- Environmental ---
    "Pollution & Treatment Controls": "EVX",
    "Pollution Control Equipment": "EVX",
    "Environmental Services": "EVX",
    "Waste Management": "WM",

    # --- Misc / Broad ---
    "Shell Companies": "SPCX",
    "Miscellaneous": "SPY",
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
    call()
    #
    # for s, etf in SECTOR_ETF.items():
    #     data_downloader.get_stock_obj(etf)