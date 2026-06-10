import pandas as pd
from sentence_transformers import SentenceTransformer
import db
import  file_processor as fp
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
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
        f"Quantitative signals for {row['symbol']}: The overall score is {score}. "
        f"The core model generated a {row['core_signal']} signal with a strength of {core}. "
        f"Fake breakout status is {row['fake_break_signal']}. "
        f"The early indicator is at {row['early']}, while the primary buy signal is {row['buy_signal']}. "
        f"Market accumulation is showing {row['accumulation_signal']}."
    )
    return summary

def load():
    print("1. Loading CSV data...")
    db.load(fp, db, TABLE_NAME, description_column)
    # fp.rename_files(files)

def query():
    print("1. Connecting to LanceDB and loading the table...")

    table = db.get_db().open_table(TABLE_NAME)
    import duckdb
    arrow_dataset = table.to_lance()
    sql_query = """
        select * , row_number() over (partition by symbol order by clean_date asc) as rn from (
        SELECT 
            *,
            CAST(LEFT(date, 10) AS DATE) as clean_date 
        FROM arrow_dataset 
        where symbol = 'UNH'
        ORDER BY symbol ASC, clean_date ASC
        )
    """
    ema_results = duckdb.query(sql_query).to_df()
    print(ema_results)



    print("2. Creating vector for our query...")
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
    con = db.get_db()
    con.drop_table(TABLE_NAME)

if __name__ == "__main__":
    # clear_table()
    # load()
    query()