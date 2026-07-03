import pandas as pd
from nltk.sem.chat80 import sql_query
from sentence_transformers import SentenceTransformer
import db
import  file_processor as fp
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
TABLE_NAME = "ema_trend"

def description_column(row):
    # 1. Fill missing values gracefully so the text reads well
    row = row.fillna("None")

    # 2. Format the sentence using the exact column names from your table
    # We round the float values slightly so the AI model reads them cleanly
    score = round(float(row['score']), 3) if row['score'] != "None" else "None"
    core = round(float(row['core']), 3) if row['core'] != "None" else "None"

    return (
        f"date: {row['date']}. "
        f"Quantitative signals for {row['symbol']}: The overall score is {score}. "
        f"The core model generated a {row['core_signal']} signal with a strength of {core}. "
        f"Fake breakout status is {row['fake_break_signal']}. "
        f"The early indicator is at {row['early']}, while the primary buy signal is {row['buy_signal']}. "
        f"Market accumulation is showing {row['accumulation_signal']}."
    )
    return summary

def load():
    print("1. Loading CSV data...")
    db.load(TABLE_NAME, description_column)
    # fp.rename_files(files)

def query():
    print("1. Connecting to LanceDB and loading the table...")

    table = db.get_connection().open_table(TABLE_NAME)
    import duckdb
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
           fake_break_signal ,

            LAG(fake_break_signal, 1) OVER (PARTITION BY symbol ORDER BY date) AS fake_break_signal_1,
            LAG(fake_break_signal, 2) OVER (PARTITION BY symbol ORDER BY date) AS fake_break_signal_2,
            LAG(fake_break_signal, 3) OVER (PARTITION BY symbol ORDER BY date) AS fake_break_signal_3,
                     buy_signal,
    LAG(buy_signal, 1) OVER (PARTITION BY symbol ORDER BY date) AS buy_signal_1,
            LAG(buy_signal, 2) OVER (PARTITION BY symbol ORDER BY date) AS buy_signal_2,
            LAG(buy_signal, 3) OVER (PARTITION BY symbol ORDER BY date) AS buy_signal_3,
                accumulation_signal,
                  LAG(accumulation_signal, 1) OVER (PARTITION BY symbol ORDER BY date) AS accumulation_signal_1,
            LAG(accumulation_signal, 2) OVER (PARTITION BY symbol ORDER BY date) AS accumulation_signal_2,
            LAG(accumulation_signal, 3) OVER (PARTITION BY symbol ORDER BY date) AS accumulation_signal_3,
            ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
        FROM arrow_dataset  where score > 0.5
         and  CAST(date AS DATE)  >= current_date - INTERVAL '5' DAY
        )
        SELECT *
        FROM ranked
        WHERE rn = 1
     --AND score > (score_1 + score_2 + score) / 3

         order by score desc

            """
    ema_results = duckdb.query(sql_query).to_df()
    print(ema_results)

    # symbol
    # score
    # sec_score
    # core
    # core_signal
    # fake_break_score
    # fake_break_signal
    # early
    # buy_signal
    # accumulation
    # accumulation_signal


    # model = SentenceTransformer('all-MiniLM-L6-v2')
    # query_vector = model.encode("high momentum tech companies")

    # print("3. Performing native hybrid search with hard SQL filters...")
    # results = (
    #     table.search()
    #     # .where("symbol = 'AAOI'") # Hard SQL filter
    #     # .select() # Return only these columns
    #     .to_pandas()
    # )
    #
    # print("\n🔍 Search Results:")
    # results['date'] = pd.to_datetime(results['date'])
    #
    # # 2. Order the DataFrame by the newly casted date column
    # # Ascending=True sorts from oldest to newest (chronological order)
    # results = results.sort_values(by='date', ascending=True)
    # print(results)
def clear_table():
    con = db.get_connection()
    con.drop_table(TABLE_NAME)

if __name__ == "__main__":
    # clear_table()
    # load()
    query()