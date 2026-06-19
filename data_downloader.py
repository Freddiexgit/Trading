from time import sleep

import yfinance as yf
import pandas as pd
import traceback


# Global variable
symbol_and_df = {}
symbol_and_stock = {}
global_period = None
global_interval = None
to_be_removed_tickers = []  # list to track symbols that should be removed from the cache
def get_transaction_df(symbol, period="18mo", interval="1d", is_back_test=False,start_date = None, end_date = None):
    """Update the shared variable safely."""
    if global_period and global_interval:
        period = global_period
        interval = global_interval
    df = symbol_and_df.get(symbol)
    # if df is not None :
    #     print("cache trans hit for ", symbol)
    if df is None:
        # try:
        #     df = yf.download(symbol, period=period, interval=interval,auto_adjust=False)
        # except Exception as e:
        #     return pd.DataFrame()
        get_stock_obj(symbol,period, interval,is_back_test,start_date,end_date)

    df =  symbol_and_df[symbol]
    # if len(df) < 1:
    #     try:
    #
    #         if is_back_test:
    #             df = yf.download(symbol, start=start_date, end=end_date, interval=interval, auto_adjust=False)
    #         else:
    #             df = yf.download(symbol, period=period, interval=interval, auto_adjust=False)
    #     except Exception  as e:
    #         return pd.DataFrame()
    #     symbol_and_df[symbol] = df
    if(df.empty):
        to_be_removed_tickers.append(symbol)
    df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df

    return df.copy()  # Return a copy to prevent accidental modifications to the cached DataFrame


def get_stock_obj(symbol, period="10mo", interval="1d", is_back_test=False,start_date = None, end_date = None):
    """Update the shared variable safely."""
    global symbol_and_stock ,symbol_and_df, global_period, global_interval
    if  global_period and  global_interval:
        period = global_period
        interval = global_interval
    stock = symbol_and_stock.get(symbol)
    # if stock is not None :
    #     print("cache  stock hit for ", symbol)
    if stock is None:
        stock = yf.Ticker(symbol)

        symbol_and_stock[symbol] = stock
        if is_back_test:
            df = stock.history(start=start_date, end=end_date, interval = interval, auto_adjust=True)
        else:
            df = stock.history(period=period, interval=interval, auto_adjust=True)
        symbol_and_df[symbol] = df
    return stock



if __name__ == "__main__":
    # Example usage
    # ticker_file_name = "nzx_tickers"
    # ticker_file_name = "my_vip"
    # ticker_file_name = "my_watch_list"
    ticker_file_name = "us_top_5000"
    # ticker_file_name = "us_middle_3000"
    # ticker_file_name = "my_owned"
    # ticker_file_name = "to_be_removed_tickers"
    ticker_file_name_full = f"{ticker_file_name}.csv"
    input_file = f"resource/{ticker_file_name_full}"
    watch_list = pd.read_csv(f"{input_file}")['symbol'].tolist()
    error_list = pd.read_csv("resource/to_remove.csv")['symbol'].tolist()
    # # watch_list = ["AAOI"]
    # for ticker in watch_list:
    #     try:
    #         df = get_stock_obj(ticker,period = "2y",interval = "1wk", is_back_test=False,start_date="2025-12-01", end_date="2025-12-05")
    #         if(df is None or len(df) < 1):
    #             print(f"WARNING: DataFrame is empty for {ticker}!")
    #             error_list.append(ticker)
    #     except Exception as e:
    #         error_list.append(ticker)
    #         traceback.print_exc()
    #         print(ticker)
    # print(error_list)
    # pd.DataFrame(error_list, columns=['symbol']).to_csv(f"resource/to_remove.csv", index=False)
    watch_list = list(set(watch_list) - set(error_list))
    pd.DataFrame(watch_list, columns=['symbol']).to_csv(f"resource/{ticker_file_name_full}", index=False)
    # st = get_stock_obj("AMDL")
    # print(st.get_info())

    # sleep(1)
    # print(get_transaction_df("AMDL"))


    # Your existing code
    # stock = yf.Ticker("AAOI")
    # df = stock.history(start="2025-12-01", end="2025-12-05", interval="1d", auto_adjust=True)
    #
    # if df.empty:
    #     print(f"WARNING: DataFrame is empty for !")


    # industry_to_etf = {
    #     "Medicinal Chemicals and Botanical Products": "IHE",  # Pharmaceuticals
    #     "Accident &Health Insurance": "KIE",  # Insurance
    #     "Advertising": "XLC",  # Communication Services
    #     "Aerospace": "ITA",  # Aerospace & Defense
    #     "Agricultural Chemicals": "MOO",  # Agribusiness
    #     "Air Freight&Delivery Services": "IYT",  # Transportation
    #     "Aluminum": "XME",  # Metals & Mining
    #     "Apparel": "XLY",  # Consumer Discretionary
    #     "Auto & Home Supply Stores": "XRT",  # Retail
    #     "Auto Manufacturing": "CARZ",  # Autos
    #     "Auto Parts:O.E.M.": "CARZ",  # Autos
    #     "Automotive Aftermarket": "CARZ",  # Autos
    #     "Banks": "KBE",  # Bank
    #     "Beverages (Production&Distribution)": "PBJ",  # Food & Beverage
    #     "Biotechnology: Biological Products (No Diagnostic Substances)": "XBI",  # Biotech
    #     "Biotechnology: Commercial Physical & Biological Resarch": "XBI",  # Biotech
    #     "Biotechnology: Electromedical & Electrotherapeutic Apparatus": "IHI",  # Medical Devices
    #     "Biotechnology: In Vitro & In Vivo Diagnostic Substances": "XHE",  # Health Care Equipment & Services
    #     "Biotechnology: Laboratory Analytical Instruments": "IHI",  # Medical Devices
    #     "Biotechnology: Pharmaceutical Preparations": "IHE",  # Pharmaceuticals
    #     "Blank Checks": "SPCX",  # SPACs
    #     "Books": "XLY",  # Consumer Discretionary
    #     "Broadcasting": "XLC",  # Communication Services
    #     "Building Materials": "XLB",  # Materials
    #     "Building operators": "XLRE",  # Real Estate
    #     "Building Products": "XLI",  # Industrials
    #     "Cable & Other Pay Television Services": "XLC",  # Communication Services
    #     "Catalog&Specialty Distribution": "IBUY",  # Online Retail / E-commerce
    #     "Clothing&Shoe&Accessory Stores": "XRT",  # Retail
    #     "Coal Mining": "XME",  # Metals & Mining
    #     "Commercial Banks": "KBE",  # Bank
    #     "Computer Communications Equipment": "IYW",  # Technology Equipment
    #     "Computer Manufacturing": "IYW",  # Technology Equipment
    #     "Computer peripheral equipment": "IYW",  # Technology Equipment
    #     "Computer Software: Prepackaged Software": "IGV",  # Software
    #     "Computer Software: Programming Data Processing": "IGV",  # Software
    #     "Construction&Ag Equipment&Trucks": "XLI",  # Industrials
    #     "Consumer Electronics&Appliances": "XLY",  # Consumer Discretionary
    #     "Consumer Electronics&Video Chains": "XRT",  # Retail
    #     "Consumer Specialties": "XLY",  # Consumer Discretionary
    #     "Containers&Packaging": "XLB",  # Materials
    #     "Department&Specialty Retail Stores": "XRT",  # Retail
    #     "Diversified Commercial Services": "XLI",  # Industrials
    #     "Diversified Electronic Products": "XLK",  # Technology
    #     "Diversified Financial Services": "XLF",  # Financials
    #     "Durable Goods": "XLY",  # Consumer Discretionary
    #     "EDP Services": "XLK",  # Technology Services
    #     "Electric Utilities: Central": "XLU",  # Utilities
    #     "Electrical Products": "XLI",  # Industrials
    #     "Electronic Components": "SOXX",  # Semiconductors / Components
    #     "Electronics Distribution": "XLK",  # Technology
    #     "Engineering & Construction": "PAVE",  # Infrastructure
    #     "Environmental Services": "EVX",  # Environmental
    #     "Farming&Seeds&Milling": "MOO",  # Agribusiness
    #     "Finance&Investors Services": "KCE",  # Capital Markets
    #     "Finance Companies": "XLF",  # Financials
    #     "Finance: Consumer Services": "XLF",  # Financials
    #     "Fluid Controls": "XLI",  # Industrials
    #     "Food Chains": "PBJ",  # Food & Beverage
    #     "Food Distributors": "PBJ",  # Food & Beverage
    #     "Forest Products": "WOOD",  # Timber & Forestry
    #     "Garments and Clothing": "XLY",  # Consumer Discretionary
    #     "General Bldg Contractors - Nonresidential Bldgs": "PAVE",  # Infrastructure
    #     "Home Furnishings": "XHB",  # Homebuilders & Furnishings
    #     "Homebuilding": "ITB",  # Home Construction
    #     "Hospital&Nursing Management": "XLV",  # Healthcare Broad
    #     "Hotels&Resorts": "PEJ",  # Leisure & Entertainment
    #     "Industrial Machinery&Components": "XLI",  # Industrials
    #     "Industrial Specialties": "XLI",  # Industrials
    #     "Integrated Freight & Logistics": "IYT",  # Transportation
    #     "Integrated oil Companies": "XLE",  # Energy
    #     "Investment Bankers&Brokers&Service": "IAI",  # Broker-Dealers
    #     "Investment Managers": "KCE",  # Capital Markets
    #     "Life Insurance": "KIE",  # Insurance
    #     "Major Banks": "KBE",  # Banks
    #     "Major Chemicals": "XLB",  # Materials
    #     "Managed Health Care": "XLV",  # Healthcare Broad
    #     "Marine Transportation": "IYT",  # Transportation
    #     "Meat&Poultry&Fish": "PBJ",  # Food & Beverage
    #     "Medical&Dental Instruments": "IHI",  # Medical Devices
    #     "Medical&Nursing Services": "XLV",  # Healthcare Broad
    #     "Medical Electronics": "IHI",  # Medical Devices
    #     "Medical Specialities": "XLV",  # Healthcare Broad
    #     "Metal Fabrications": "XME",  # Metals & Mining
    #     "Metal Mining": "XME",  # Metals & Mining
    #     "Military&Government&Technical": "ITA",  # Aerospace & Defense
    #     "Mining & Quarrying of Nonmetallic Minerals (No Fuels)": "XME",  # Metals & Mining
    #     "Misc Corporate Leasing Services": "XLI",  # Industrials
    #     "Misc Health and Biotechnology Services": "XHE",  # Healthcare Services
    #     "Miscellaneous": "SPY",  # Broad Market Catch-all
    #     "Miscellaneous manufacturing industries": "XLI",  # Industrials
    #     "Motor Vehicles": "CARZ",  # Autos
    #     "Movies&Entertainment": "XLC",  # Communication Services
    #     "Multi-Sector Companies": "XLI",  # Industrials
    #     "Natural Gas Distribution": "FCG",  # Natural Gas
    #     "Newspapers&Magazines": "XLC",  # Communication Services
    #     "Office Equipment&Supplies&Services": "XLI",  # Industrials
    #     "Oil&Gas Transmission": "AMLP",  # Midstream / Pipelines
    #     "Oil & Gas Production": "XOP",  # Oil & Gas Exploration
    #     "Oil and Gas Field Machinery": "XES",  # Oil & Gas Equipment/Services
    #     "Oil Refining&Marketing": "CRAK",  # Refining
    #     "Oilfield Services&Equipment": "XES",  # Oil & Gas Equipment/Services
    #     "Ophthalmic Goods": "IHI",  # Medical Devices
    #     "Ordnance And Accessories": "ITA",  # Defense
    #     "Other Consumer Services": "XLY",  # Consumer Discretionary
    #     "Other Metals and Minerals": "XME",  # Metals & Mining
    #     "Other Pharmaceuticals": "IHE",  # Pharmaceuticals
    #     "Other Specialty Stores": "XRT",  # Retail
    #     "Other Transportation": "IYT",  # Transportation
    #     "Package Goods&Cosmetics": "XLP",  # Consumer Staples
    #     "Packaged Foods": "PBJ",  # Food & Beverage
    #     "Paints&Coatings": "XLB",  # Materials
    #     "Paper": "WOOD",  # Timber & Forestry
    #     "Pharmaceuticals and Biotechnology": "XBI",  # Biotech
    #     "Plastic Products": "XLB",  # Materials
    #     "Pollution Control Equipment": "EVX",  # Environmental
    #     "Power Generation": "XLU",  # Utilities
    #     "Precious Metals": "GDX",  # Gold/Precious Metal Miners
    #     "Precision Instruments": "XLI",  # Industrials
    #     "Professional and commerical equipment": "XLI",  # Industrials
    #     "Professional Services": "XLI",  # Industrials
    #     "Property-Casualty Insurers": "KIE",  # Insurance
    #     "Publishing": "XLC",  # Communication Services
    #     "Radio And Television Broadcasting And Communications Equipment": "XLC",  # Communication Services
    #     "Railroads": "IYT",  # Transportation
    #     "Real Estate": "XLRE",  # Real Estate
    #     "Real Estate Investment Trusts": "VNQ",  # REITs
    #     "Recreational Games&Products&Toys": "XLY",  # Consumer Discretionary
    #     "Rental&Leasing Companies": "XLI",  # Industrials
    #     "Restaurants": "EATZ",  # Restaurants
    #     "RETAIL: Building Materials": "XHB",  # Homebuilders & Supply
    #     "Retail: Computer Software & Peripheral Equipment": "XRT",  # Retail
    #     "Retail-Auto Dealers and Gas Stations": "CARZ",  # Autos
    #     "Retail-Drug Stores and Proprietary Stores": "XLP",  # Consumer Staples
    #     "Savings Institutions": "KRE",  # Regional Banks
    #     "Semiconductors": "SOXX",  # Semiconductors
    #     "Services-Misc. Amusement & Recreation": "PEJ",  # Leisure & Entertainment
    #     "Shoe Manufacturing": "XLY",  # Consumer Discretionary
    #     "Specialty Chemicals": "XLB",  # Materials
    #     "Specialty Foods": "PBJ",  # Food & Beverage
    #     "Specialty Insurers": "KIE",  # Insurance
    #     "Steel&Iron Ore": "SLX",  # Steel
    #     "Telecommunications Equipment": "IYZ",  # Telecommunications
    #     "Textiles": "XLY",  # Consumer Discretionary
    #     "Tobacco": "XLP",  # Consumer Staples
    #     "Tools&Hardware": "XLI",  # Industrials
    #     "Transportation Services": "IYT",  # Transportation
    #     "Trucking Freight&Courier Services": "IYT",  # Transportation
    #     "Trusts Except Educational Religious and Charitable": "XLF",  # Financials
    #     "Water Sewer Pipeline Comm & Power Line Construction": "PAVE",  # Infrastructure
    #     "Water Supply": "FIW",  # Water
    #     "Wholesale Distributors": "XLI"  # Industrials
    # }
    # for industry, etf in industry_to_etf.items():
    #     try:
    #         df = get_transaction_df(etf)
    #     except Exception as e:
    #         print(f"Error fetching data for {etf}: {e}")
    #         continue