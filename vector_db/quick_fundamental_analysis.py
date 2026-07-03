import duckdb
import pandas as pd
from sentence_transformers import SentenceTransformer
import db
import  file_processor as fp
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
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
    db.load(TABLE_NAME, create_stock_summary)


def query():
    print("1. Connecting to LanceDB and loading the table...")

    table = db.get_connection().open_table(TABLE_NAME)

    arrow_dataset = table.to_lance()
    sql_query = f"""
WITH ranked AS (
    SELECT
        symbol,
        CAST(date AS DATE) AS date,
        score,
     
        LAG(score, 1) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS score_1,
        LAG(score, 2) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS score_2,
   price,
   
        LAG(price, 1) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS price_1,
        LAG(price, 2) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS price_2,
     Momentum_20d as momentum,
   

        LAG(Momentum_20d, 1) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS mom_1,
        LAG(Momentum_20d, 2) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS mom_2,
     bb_pos,
   
        LAG(bb_pos, 1) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS bb_1,
        LAG(bb_pos, 2) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS bb_2,
     peg,
    
        LAG(peg, 1) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS peg_1,
        LAG(peg, 2) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS peg_2,
    PE_Fwd as pe,
        LAG(pe, 1) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS pe_1,
        LAG(pe, 2) OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE)) AS pe_2,

        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY CAST(date AS DATE) DESC) AS rn
    FROM arrow_dataset
)
SELECT *
FROM ranked
WHERE rn = 1 and score > 5
-- AND score > score_1 AND score_1 > score_2
-- AND price > price_1 AND price_1 > price_2
-- AND momentum > mom_1 AND mom_1 > mom_2
-- AND bb_pos > bb_1 AND bb_1 > bb_2
-- AND peg < peg_1 AND peg_1 < peg_2
-- AND pe < pe_1 AND pe_1 < pe_2;
order by (score + score_1 + score_2)/3  DESC


           """
    # Score
    # Rating
    # PEG
    # PE_Fwd
    # ROE
    # OCF_to_NetIncome_Ratio_last2year
    # Debt_EBITDA
    # Mkt_Cap_B
    # Momentum_20d
    # Sector
    # bollinger_band_status
    # BB_Pos
    ema_results = duckdb.query(sql_query).to_df()
    print(ema_results)
def clear_table():
    con = db.get_db()
    con.drop_table(TABLE_NAME)

if __name__ == "__main__":
    # clear_table()
    # load()
    query()