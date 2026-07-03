import pandas as pd
from sentence_transformers import SentenceTransformer
import db
import  file_processor as fp
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
TABLE_NAME = "find_building_up_gpt_early"
pd.set_option('display.max_rows', None)


def generate_semantic_summary(row):
    """
    Converts a stock's updated technical and industry metrics into a rich,
    semantic sentence optimized for VectorDB embeddings and search.
    """

    # 1. Translate Booleans into Natural Language
    early_trend_text = "is showing signs of an early uptrend" if row["early_trend"] else "is not in an early uptrend"
    obv_text = "exhibits rising On-Balance Volume indicating persistent institutional buying" if row[
        "obv_rising"] else "does not show rising On-Balance Volume"
    pocket_text = "recently flashed a stealthy pocket pivot buy signal" if row[
        "pocket"] else "has no recent pocket pivot activity"
    bb_squeeze_text = "is consolidating in a tight Bollinger Band squeeze indicating a potential explosive breakout" if \
    row["bb_squeeze"] else "is not in a Bollinger Band squeeze"
    fast_squeeze_text = "is triggering a short-term fast momentum squeeze" if row[
        "fast_squeeze"] else "is not in a fast squeeze"

    # 2. Build the Semantic Paragraph
    summary = (
        f"On {row['date']}, stock {row['symbol']} operating in the {row['industry']} industry closed at ${row['close']} "
        f"(open: ${row['open']}) on a volume of {row['volume']} shares. "
        f"The stock holds an accumulation score of {row['score']}, earning a rating of '{row['rating']}', "
        f"and is currently classified as being in a {row['stage']} market cycle. "
        f"Fundamentally, its industry group is performing in the {row['industry_percentile']} percentile with an industry score of {row['industry_score']}. "
        f"Technically, the stock {early_trend_text}. It has a Relative Strength (RS) rank of {row['rs_rank']} "
        f"and an RS accumulation value of {row['rs_acc']}. "
        f"Volume dynamics reveal an overall Up/Down volume ratio of {row['ud_ratio']} and a tighter 10-day U/D ratio of {row['ud10']}. "
        f"Furthermore, the stock {obv_text}, and it {pocket_text}. "
        f"Regarding volatility and setups, it {bb_squeeze_text}, and {fast_squeeze_text}."
    )

    return summary
def load():
    print("1. Loading CSV data...")
    db.load(TABLE_NAME, generate_semantic_summary)
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

def query():
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
        score,
      
        LAG(score, 1) OVER (PARTITION BY symbol ORDER BY date) AS score_1,
        LAG(score, 2) OVER (PARTITION BY symbol ORDER BY date) AS score_2,
        LAG(score, 3) OVER (PARTITION BY symbol ORDER BY date) AS score_3,
          stage,
        LAG(stage, 1) OVER (PARTITION BY symbol ORDER BY date) AS stage_1,
        LAG(stage, 2) OVER (PARTITION BY symbol ORDER BY date) AS stage_2,
        LAG(stage, 3) OVER (PARTITION BY symbol ORDER BY date) AS stage_3,
        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
    FROM arrow_dataset  where score > 20 
     and  CAST(date AS DATE)  >= current_date - INTERVAL '5' DAY
    )
    SELECT *
    FROM ranked
    WHERE rn = 1
      AND score > (score_1 + score_2 + score) / 3
       and stage not like '%Declining%'
     order by score desc

        """

    ema_results = duckdb.query(sql_query).to_df()
    print(ema_results)
if __name__ == "__main__":
    # clear_table()
    # load()
    query()