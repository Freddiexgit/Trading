import pandas as pd
from sentence_transformers import SentenceTransformer
import db
import  file_processor as fp
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_rows', 1000)
TABLE_NAME = "uptrend"

def description_column(row):
    # 1. Fill missing values gracefully so the text reads well
    row = row.fillna("None")

    avg_vol_millions = round(float(row['avg_volume']) / 1_000_000, 1)

    return (
        f"date: {row['date']}. "
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
    db.load(TABLE_NAME, description_column)
    # fp.rename_files(files)

def query():
    print("1. Connecting to LanceDB and loading the table...")

    table = db.get_connection().open_table(TABLE_NAME)


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
    table =db.get_connection().open_table(TABLE_NAME)
    #
    # # 2. Convert the LanceDB table to an Arrow dataset
    arrow_dataset = table.to_lance()


    sql_query = f"""

            WITH ranked AS (
    SELECT
        symbol,
        date,
         composite_score  score,
         annualized_slope_pct,
        trend_quality, 
        LAG(score, 1) OVER (PARTITION BY symbol ORDER BY date) AS score_1,
        LAG(score, 2) OVER (PARTITION BY symbol ORDER BY date) AS score_2,
        LAG(score, 3) OVER (PARTITION BY symbol ORDER BY date) AS score_3,
          annualized_slope_pct,
        LAG(annualized_slope_pct, 1) OVER (PARTITION BY symbol ORDER BY date) AS slope_1,
        LAG(annualized_slope_pct, 2) OVER (PARTITION BY symbol ORDER BY date) AS slope_2,
        LAG(annualized_slope_pct, 3) OVER (PARTITION BY symbol ORDER BY date) AS slope_3,
        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
    FROM arrow_dataset  where score > 300
     and  CAST(date AS DATE)  >= current_date - INTERVAL '5' DAY
    )
    SELECT *
    FROM ranked
    WHERE rn = 1
      AND score > (score_1 + score_2 + score) / 3

     order by score desc

        """

    uptrend_results = duckdb.query(sql_query).to_df()
    print(uptrend_results)
if __name__ == "__main__":
    # clear_table()
    # load()
    query_by_trend_quality()