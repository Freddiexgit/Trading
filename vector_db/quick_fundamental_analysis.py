import pandas as pd
from sentence_transformers import SentenceTransformer
import db
import  file_processor as fp
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
TABLE_NAME = "quick_fundamental_analysis"

def create_stock_summary(row):
    """
    Combines the tabular data into a semantic sentence.
    This makes the vector embeddings much more effective for search.
    """
    # Safely handle missing values by filling them with 'N/A'
    row = row.fillna("N/A")

    summary = (
        f"date: {row['date']}. "
        f"Stock {row['symbol']} in the {row['Sector']} sector. "
        f"Current Price: ${row['price']}, Analyst Score: {row['Score']}, Rating: {row['Rating']}. "
        f"Financials - PEG: {row['PEG']}, Forward P/E: {row['PE_Fwd']}, ROE: {row['ROE']}. "
        f"Market Cap: {row['Mkt_Cap_B']} Billion. "
        f"Momentum: {row['Momentum_20d']}, Bollinger Band Status: {row['bollinger_band_status']}."
    )
    return summary

def load():
    print("1. Loading CSV data...")
    db.load(fp, db, TABLE_NAME, create_stock_summary)


def query():
    print("1. Connecting to LanceDB and loading the table...")

    table = db.get_db().open_table(TABLE_NAME)


    print("2. Creating vector for our query...")
    # model = SentenceTransformer('all-MiniLM-L6-v2')
    # query_vector = model.encode("high momentum tech companies")

    print("3. Performing native hybrid search with hard SQL filters...")
    results = (
        table.search()
        # .where("symbol = 'MU'") # Hard SQL filter
        # .limit(5)                                         # Top 5 matches
        # .select() # Return only these columns
        .where("symbol = 'MU' AND cast(date as date) >= date '2026-01-01'")
        # .order_by("date")
        .to_pandas()
    )

    print("\n🔍 Search Results:")
    # 1. Cast the string 'date' column to a true datetime type
    results['date'] = pd.to_datetime(results['date'])

    # 2. Order the DataFrame by the newly casted date column
    # Ascending=True sorts from oldest to newest (chronological order)
    results = results.sort_values(by='date', ascending=True)
    print(results)
def clear_table():
    con = db.get_db()
    con.drop_table(TABLE_NAME)

if __name__ == "__main__":
    # clear_table()
    # load()
    query()