import pandas as pd
from sentence_transformers import SentenceTransformer
import db
import  file_processor as fp
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
TABLE_NAME = "uptrend"

def description_column(row):
    # 1. Fill missing values gracefully so the text reads well
    row = row.fillna("None")

    avg_vol_millions = round(float(row['avg_volume']) / 1_000_000, 1)

    return (
        f"Quantitative trading setup for {row['symbol']}: The stock is currently priced at ${row['price']:.2f} "
        f"and is triggering a {row['entry_type']} entry. The recommended entry price is ${row['recommended_entry']:.2f} "
        f"with a protective stop at ${row['recommended_stop']:.2f}, targeting sequential profit levels at "
        f"${row['target1']:.2f}, ${row['target2']:.2f}, and ${row['target3']:.2f}. "
        f"Trend metrics show extremely strong momentum with a 30-day change of {row['pct_change_30d']}%, "
        f"an annualized slope of {row['annualized_slope_pct']}%, and a highly linear R-squared fit of {row['r_squared']}. "
        f"Volatility and extension indicators note an ATR of {row['atr']:.2f}, an ADR of {row['adr_pct']}%, "
        f"and the asset is extended, sitting {row['dist_ema20_pct']}% above its 20-day EMA. "
        f"Supported by an average volume of {avg_vol_millions} million shares, the setup holds a trend quality "
        f"of {row['trend_quality']:.2f} and a final composite score of {row['composite_score']:.2f}."
    )

def load():
    print("1. Loading CSV data...")
    db.load(fp, db, TABLE_NAME, description_column)
    # fp.rename_files(files)

def query():
    print("1. Connecting to LanceDB and loading the table...")

    table = db.get_db().open_table(TABLE_NAME)


    print("2. Creating vector for our query...")
    # model = SentenceTransformer('all-MiniLM-L6-v2')
    # query_vector = model.encode("high momentum tech companies")

    print("3. Performing native hybrid search with hard SQL filters...")
    results = (
        table.search()
        .where("symbol = 'SNDK'") # Hard SQL filter
        .limit(5)                                         # Top 5 matches
        # .select() # Return only these columns
        .to_pandas()
    )

    print("\n🔍 Search Results:")
    print(results)
def clear_table():
    con = db.get_db()
    con.drop_table(TABLE_NAME)

def query_by_trend_quality():
    print("1. Connecting to LanceDB and loading the table...")
    import duckdb

    # Assuming 'df' is your DataFrame or 'arrow_dataset' from LanceDB
    table =db.get_db().open_table(TABLE_NAME)
    #
    # # 2. Convert the LanceDB table to an Arrow dataset
    arrow_dataset = table.to_lance()

    sql_query = """
    SELECT 
        *,
        CAST(LEFT(date, 10) AS DATE) as clean_date 
    FROM arrow_dataset 
    where symbol = 'MU'
    ORDER BY symbol ASC, clean_date ASC
"""

    # sql_query = """
    #     WITH RankedData AS (
    #         SELECT
    #             symbol,
    #             price as first_price,
    #             LAST_VALUE(price) OVER (
    #                 PARTITION BY symbol
    #                 ORDER BY date ASC
    #                 ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    #             ) as last_price
    #         FROM arrow_dataset
    #     )
    #     SELECT
    #         symbol,
    #         MAX(first_price) as start_price,
    #         MAX(last_price) as end_price,
    #         ROUND(((MAX(last_price) - MAX(first_price)) / MAX(first_price)) * 100, 2) AS total_trend_pct
    #     FROM RankedData
    #     GROUP BY symbol
    #     --HAVING MAX(last_price) > MAX(first_price) -- Only keep the ones going UP
    #     ORDER BY total_trend_pct DESC
    # """

    uptrend_results = duckdb.query(sql_query).to_df()
    print(uptrend_results)
if __name__ == "__main__":
    # clear_table()
    # load()
    query_by_trend_quality()