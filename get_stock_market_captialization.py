import yfinance as yf
import pandas as pd


def get_stock_market_capitalization(ticker_symbol="AAPL", property_name="marketCap"):
    return  get_stock_info(ticker_symbol)
def get_stock_info(ticker_symbol ="QD"):
    # Get the stock data
    try:
        stock = yf.Ticker(ticker_symbol)
    except Exception as a :
        print(f"Error fetching data for {ticker_symbol}: {a}")
        return None
    # Get market cap
    return  stock.info
    # Print market cap in human-readable format

if __name__ == "__main__":
    stock_value_more_then_1_billion = []
    df = pd.read_csv('resource/nyse_tickers.csv')
    tickers = df['symbol'].dropna().tolist()
    for ticker in tickers:

        mrkt_val = get_stock_market_capitalization(ticker)
        if mrkt_val and mrkt_val > 10_000_000_000:
            stock_value_more_then_1_billion.append(ticker)

    df2  = pd.DataFrame(stock_value_more_then_1_billion)
    df2.to_csv('resource/nyse_tickers_value_more_then_10_billion.csv', index=False)

    # {'52WeekChange': -0.042636037,
    # 'SandP52WeekChange': 0.16821623,
    # 'address1': 'One Apple Park Way', 'ask': 209.19,
    #  'askSize': 4,
    #  'auditRisk': 7,
    #  'averageAnalystRating': '1.9 - Buy',
    #  'averageDailyVolume10Day': 46117180,
    #  'averageDailyVolume3Month': 53123538,
    #  'averageVolume': 53123538,
    #  'averageVolume10days': 46117180,
    #  'beta': 1.199,
    #  'bid': 208.79,
    #  'bidSize': 4,
    #  'boardRisk': 1,
    #  'bookValue': 4.471,
    #  'city': 'Cupertino',
    #  'companyOfficers': [
    #     {'age': 63, 'exercisedValue': 0, 'fiscalYear': 2024, 'maxAge': 1, 'name': 'Mr. Timothy D. Cook',
    #      'title': 'CEO & Director', 'totalPay': 16520856, 'unexercisedValue': 0, 'yearBorn': 1961},
    #     {'age': 52, 'exercisedValue': 0, 'fiscalYear': 2024, 'maxAge': 1, 'name': 'Mr. Kevan  Parekh',
    #      'title': 'Senior VP & CFO', 'unexercisedValue': 0, 'yearBorn': 1972},
    #     {'exercisedValue': 0, 'fiscalYear': 2024, 'maxAge': 1, 'name': 'Molly  Thompson',
    #      'title': 'Head of Documentaries for Apple TV+', 'unexercisedValue': 0},
    #     {'age': 51, 'exercisedValue': 0, 'fiscalYear': 2024, 'maxAge': 1, 'name': 'Mr. Matthew  Cherniss',
    #      'title': 'Head of Programming for Apple TV+', 'unexercisedValue': 0, 'yearBorn': 1973},
    #     {'exercisedValue': 0, 'fiscalYear': 2024, 'maxAge': 1, 'name': 'Ashish  Chowdhary',
    #      'title': 'Head of Indian Business', 'unexercisedValue': 0},
    #     {'exercisedValue': 0, 'fiscalYear': 2024, 'maxAge': 1, 'name': 'Mr. Roger  Rosner',
    #      'title': 'Vice President of Applications', 'unexercisedValue': 0},
    #     {'age': 57, 'exercisedValue': 0, 'fiscalYear': 2024, 'maxAge': 1, 'name': 'Mr. Kevin M. Lynch',
    #      'title': 'Vice President of Technology', 'unexercisedValue': 0, 'yearBorn': 1967},
    #     {'exercisedValue': 0, 'fiscalYear': 2024, 'maxAge': 1, 'name': 'Mr. Wyatt  Mitchell',
    #      'title': 'Director of App Design', 'unexercisedValue': 0},
    #     {'age': 61, 'exercisedValue': 0, 'fiscalYear': 2024, 'maxAge': 1, 'name': 'Ms. Jennifer  Bailey',
    #      'title': 'Vice President of Pay', 'unexercisedValue': 0, 'yearBorn': 1963},
    #     {'exercisedValue': 0, 'fiscalYear': 2024, 'maxAge': 1, 'name': 'Ms. Ann  Thai',
    #      'title': 'Director of Product Management for the App Store', 'unexercisedValue': 0}],
    #  'compensationAsOfEpochDate': 1735603200,
    #  'compensationRisk': 3,
    #  'corporateActions': [],
    #  'country': 'United States',
    #  'cryptoTradeable': False,
    #  'currency': 'USD',
    #  'currentPrice': 209.05,
    #  'currentRatio': 0.821,
    #  'customPriceAlertConfidence': 'HIGH',
    #  'dateShortInterest': 1752537600,
    #  'dayHigh': 212.39,
    #  'dayLow': 207.72,
    #  'debtToEquity': 146.994,
    #  'displayName': 'Apple',
    #  'dividendDate': 1747267200,
    #  'dividendRate': 1.04,
    #  'dividendYield': 0.5,
    #  'earningsCallTimestampEnd': 1753995600,
    #  'earningsCallTimestampStart': 1753995600,
    #  'earningsGrowth': 0.078,
    #  'earningsQuarterlyGrowth': 0.048, 'earningsTimestamp': 1753992000,
    #  'earningsTimestampEnd': 1753992000,
    #  'earningsTimestampStart': 1753992000, 'ebitda': 138865999872,
    #  'ebitdaMargins': 0.34685,
    #  'enterpriseToEbitda': 22.842, 'enterpriseToRevenue': 7.923,
    #  'enterpriseValue': 3172022353920,
    #  'epsCurrentYear': 7.18288, 'epsForward': 8.31, 'epsTrailingTwelveMonths': 6.42,
    #  'esgPopulated': False,
    #  'exDividendDate': 1747008000,
    #  'exchange': 'NMS',
    #  'exchangeDataDelayedBy': 0,
    #  'exchangeTimezoneName': 'America/New_York',
    #  'exchangeTimezoneShortName': 'EDT',
    #  'executiveTeam': [],
    #  'fiftyDayAverage': 205.3908,
    #  'fiftyDayAverageChange': 3.6592102,
    #  'fiftyDayAverageChangePercent': 0.017815843,
    #  'fiftyTwoWeekChangePercent': -4.2636037,
    #  'fiftyTwoWeekHigh': 260.1,
    #  'fiftyTwoWeekHighChange': -51.050003,
    #  'fiftyTwoWeekHighChangePercent': -0.19627067,
    #  'fiftyTwoWeekLow': 169.21, 'fiftyTwoWeekLowChange': 39.839996,
    #  'fiftyTwoWeekLowChangePercent': 0.23544705,
    #  'fiftyTwoWeekRange': '169.21 - 260.1',
    #  'financialCurrency': 'USD',
    #  'firstTradeDateMilliseconds': 345479400000,
    #  'fiveYearAvgDividendYield': 0.55,
    #  'floatShares': 14910285738,
    #  'forwardEps': 8.31, 'forwardPE': 25.156437, 'freeCashflow': 97251500032, 'fullExchangeName': 'NasdaqGS',
    #  'fullTimeEmployees': 164000, 'gmtOffSetMilliseconds': -14400000, 'governanceEpochDate': 1751328000,
    #  'grossMargins': 0.46632, 'grossProfits': 186699005952, 'hasPrePostMarketData': True,
    #  'heldPercentInsiders': 0.020920001, 'heldPercentInstitutions': 0.62832, 'impliedSharesOutstanding': 15024199680,
    #  'industry': 'Consumer Electronics', 'industryDisp': 'Consumer Electronics', 'industryKey': 'consumer-electronics',
    #  'irWebsite': 'http://investor.apple.com/', 'isEarningsDateEstimate': False, 'language': 'en-US',
    #  'lastDividendDate': 1747008000, 'lastDividendValue': 0.26, 'lastFiscalYearEnd': 1727481600,
    #  'lastSplitDate': 1598832000, 'lastSplitFactor': '4:1',
    #  'longBusinessSummary': 'Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discover and download applications and digital content, such as books, music, video, games, and podcasts, as well as advertising services include third-party licensing arrangements and its own advertising platforms. In addition, the company offers various subscription-based services, such as Apple Arcade, a game subscription service; Apple Fitness+, a personalized fitness service; Apple Music, which offers users a curated listening experience with on-demand radio stations; Apple News+, a subscription news and magazine service; Apple TV+, which offers exclusive original content; Apple Card, a co-branded credit card; and Apple Pay, a cashless payment service, as well as licenses its intellectual property. The company serves consumers, and small and mid-sized businesses; and the education, enterprise, and government markets. It distributes third-party applications for its products through the App Store. The company also sells its products through its retail and online stores, and direct sales force; and third-party cellular network carriers, wholesalers, retailers, and resellers. Apple Inc. was founded in 1976 and is headquartered in Cupertino, California.',
    #  'longName': 'Apple Inc.', 'market': 'us_market', 'marketCap': 3122329026560, 'marketState': 'PREPRE',
    #  'maxAge': 86400, 'messageBoardId': 'finmb_24937', 'mostRecentQuarter': 1743206400,
    #  'netIncomeToCommon': 97294000128, 'nextFiscalYearEnd': 1759017600, 'numberOfAnalystOpinions': 37, 'open': 211.895,
    #  'operatingCashflow': 109555998720, 'operatingMargins': 0.31028998, 'overallRisk': 1, 'payoutRatio': 0.1558,
    #  'phone': '(408) 996-1010', 'postMarketChange': -0.320007, 'postMarketChangePercent': -0.153077,
    #  'postMarketPrice': 208.73, 'postMarketTime': 1753919997, 'previousClose': 211.27, 'priceEpsCurrentYear': 29.103926,
    #  'priceHint': 2, 'priceToBook': 46.756878, 'priceToSalesTrailing12Months': 7.7986865, 'profitMargins': 0.24301,
    #  'quickRatio': 0.68, 'quoteSourceName': 'Nasdaq Real Time Price', 'quoteType': 'EQUITY', 'recommendationKey': 'buy',
    #  'recommendationMean': 1.93023, 'region': 'US', 'regularMarketChange': -2.22,
    #  'regularMarketChangePercent': -1.05079, 'regularMarketDayHigh': 212.39, 'regularMarketDayLow': 207.72,
    #  'regularMarketDayRange': '207.72 - 212.39', 'regularMarketOpen': 211.895, 'regularMarketPreviousClose': 211.27,
    #  'regularMarketPrice': 209.05, 'regularMarketTime': 1753905601, 'regularMarketVolume': 43533667,
    #  'returnOnAssets': 0.23809999, 'returnOnEquity': 1.38015, 'revenueGrowth': 0.051, 'revenuePerShare': 26.455,
    #  'sector': 'Technology', 'sectorDisp': 'Technology', 'sectorKey': 'technology', 'shareHolderRightsRisk': 1,
    #  'sharesOutstanding': 14935799808, 'sharesPercentSharesOut': 0.0063, 'sharesShort': 93946599,
    #  'sharesShortPreviousMonthDate': 1749772800, 'sharesShortPriorMonth': 100226522, 'shortName': 'Apple Inc.',
    #  'shortPercentOfFloat': 0.0063, 'shortRatio': 1.74, 'sourceInterval': 15, 'state': 'CA', 'symbol': 'AAPL',
    #  'targetHighPrice': 300.0, 'targetLowPrice': 173.0, 'targetMeanPrice': 230.17892, 'targetMedianPrice': 235.0,
    #  'totalCash': 48497999872, 'totalCashPerShare': 3.247, 'totalDebt': 98186002432, 'totalRevenue': 400366010368,
    #  'tradeable': False, 'trailingAnnualDividendRate': 1.0, 'trailingAnnualDividendYield': 0.00473328,
    #  'trailingEps': 6.42, 'trailingPE': 32.562305, 'trailingPegRatio': 1.9492, 'triggerable': True,
    #  'twoHundredDayAverage': 221.8129, 'twoHundredDayAverageChange': -12.762894,
    #  'twoHundredDayAverageChangePercent': -0.057539005, 'typeDisp': 'Equity', 'volume': 43533667,
    #  'website': 'https://www.apple.com', 'zip': '95014'}