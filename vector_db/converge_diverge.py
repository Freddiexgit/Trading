import pandas as pd
from sentence_transformers import SentenceTransformer
import db
import  file_processor as fp
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 1000)
TABLE_NAME = "ema_convergence_divergence"


def generate_converge_diverge_summary(row):
    """
    Converts a stock's convergence/divergence metrics into a semantic sentence
    optimized for VectorDB embeddings and search.
    """

    # 1. Translate Indicators into Natural Language Context
    # RSI (Relative Strength Index) Logic
    if row["RSI"] >= 70:
        rsi_text = "indicating overbought momentum"
    elif row["RSI"] <= 30:
        rsi_text = "indicating oversold momentum"
    else:
        rsi_text = "indicating neutral momentum"

    # ADX (Average Directional Index) Logic
    if row["ADX"] >= 25:
        adx_text = "a strong, active trend"
    else:
        adx_text = "a weak, trendless market"

    # Volume Ratio Logic
    vol_text = "heavy relative volume" if row["volumeRatio"] > 1.2 else "standard relative volume"

    # 2. Build the Semantic Paragraph
    summary = (
        f"date: {row['date']}. "
        f"Stock {row['symbol']} recently exhibited a pattern where its price action converged and then diverged. "
        f"During this session, it opened at ${row['open']} and closed at ${row['close']}, "
        f"earning a setup score of {row['score']}. "
        f"The divergence occurred on {vol_text} with a volume ratio of {row['volumeRatio']}. "
        f"From a momentum perspective, it has an RSI of {row['RSI']}, {rsi_text}. "
        f"Meanwhile, its ADX reading stands at {row['ADX']}, reflecting {adx_text} following the divergence."
    )

    return summary


# Example usage for a Pandas DataFrame:
# df["vector_summary"] = df.apply(generate_converge_diverge_summary, axis=1)

def load():
    print("1. Loading CSV data...")
    db.load(TABLE_NAME, generate_converge_diverge_summary)
    # fp.rename_files(files)


def clear_table():
    con = db.get_connection()
    con.drop_table(TABLE_NAME)

if __name__ == "__main__":
    # clear_table()
    load()
    # query()