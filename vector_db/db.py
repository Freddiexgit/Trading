import lancedb
import os
import file_processor as fp

# Define the path to your database
DB_URI = "./my_stock_database.lancedb"


class LanceDBConnectionManager:
    """
    A Singleton manager to ensure only one connection to the database
    is open across the entire application.
    """
    _connection = None

    @classmethod
    def get_connection(cls):
        # If a connection doesn't exist yet, create it.
        if cls._connection is None:
            # Note: lancedb.connect() automatically creates the folder if it doesn't exist!
            cls._connection = lancedb.connect(DB_URI)
            print(f"Initialized new LanceDB connection at: {DB_URI}")

        return cls._connection


# Expose a simple helper function for other modules to import
def get_connection():
    """
    Returns the active LanceDB connection.
    """
    return LanceDBConnectionManager.get_connection()
def save_to_db(table_name,df,conn)->lancedb.Table:
    if table_name in conn.table_names():
        print(f"Table '{table_name}' already exists. Appending new records...")

        # Open the existing table and append
        table = conn.open_table(table_name)
        table.add(df)

    else:
        print(f"Table '{table_name}' does not exist. Creating new table...")

        # Create the table from scratch
        table = conn.create_table(table_name, data=df)
    return table
from sentence_transformers import SentenceTransformer
import pandas as pd
def load(table_name,description_column):
    files = fp.get_csv_files(table_name)
    for date, file in files.items():
        print(f"{date}: {file}")
        df = pd.read_csv(file)

        print("2. Generating text summaries for embedding...")
        if "date" not in df.columns:
            df.insert(0, "date", date)
        # Create a new column 'text' which holds our descriptive sentences
        df['text'] = df.apply(description_column, axis=1)

        print("3. Downloading/Loading embedding model (this may take a moment the first time)...")
        # 'all-MiniLM-L6-v2' is a fast, highly capable model for general semantic search
        model = SentenceTransformer('all-MiniLM-L6-v2')

        print("4. Generating vector embeddings for all stocks...")
        # Generate embeddings and convert them to a list of lists so LanceDB can store them
        embeddings = model.encode(df['text'].tolist())
        df['vector'] = embeddings.tolist()
        table = save_to_db(table_name, df, get_connection())

        print("\n✅ Success! Database created and populated.")
        print(f"Schema: {table.schema}")
    fp.rename_files(files)
# import lancedb
# import duckdb
#
#
# # 1. Connect to LanceDB
# db = lancedb.connect("./my_stock_database.lancedb")
# table = db.open_table("quick_fundamental")
#
# # 2. Convert the LanceDB table to an Arrow dataset
# arrow_dataset = table.to_lance()
#
# # 3. Write raw, complex SQL using DuckDB
# # Note how we query 'arrow_dataset' directly in the SQL string!
# sql_query = """
#     SELECT
#         Sector,
#         COUNT(symbol) as total_stocks,
#         ROUND(AVG(price), 2) as avg_price,
#         MAX(Score) as highest_analyst_score
#     FROM arrow_dataset
#     WHERE price > 10.0
#     GROUP BY Sector
#     ORDER BY total_stocks DESC
# """
#
# # 4. Execute and get a Pandas DataFrame back
# analytics_df = duckdb.query(sql_query).to_df()
# print(analytics_df)

# # Create the vector for our query
# model = SentenceTransformer('all-MiniLM-L6-v2')
# query_vector = model.encode("high momentum tech companies")
#
# # Native Hybrid Query
# results = (
#     table.search(query_vector)
#     .where("Sector = 'Technology' AND price < 150.0") # Hard SQL filter
#     .limit(5)                                         # Top 5 matches
#     .select(["symbol", "price", "text", "_distance"]) # Return only these columns
#     .to_pandas()
# )
#
# print(results)
# Removes the stock with the exact symbol 'GPUS'
# table.delete("symbol = 'GPUS'")
#
# # --- Example 2: Delete multiple records based on conditions ---
# # Removes any stock with an analyst score under 4
# table.delete("Score < 4")
#
# # --- Example 3: Delete using multiple conditions ---
# # Removes stocks in the Technology sector that are priced under $10
# table.delete("Sector = 'Technology' AND price < 10.0")
#
# table.update(
#     where="symbol = 'NVDA'",
#     values={"price": 250.00, "Score": 8}
# )