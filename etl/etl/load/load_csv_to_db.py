import io
import pandas as pd

from utils.db import engine
from utils.logger import Logger


def load_csv_to_db(csv_file: str, table_name: str):
    """
    Load CSV file in database using column names from the CSV directly.

    :param csv_file: path to CSV file
    :param table_name: table name in database
    """
    df = pd.read_csv(csv_file, keep_default_na=False)
    if df.empty:
        Logger.warning("No data to load")
        return

    db_cols = list(df.columns)

    total_rows = len(df)
    Logger.info(f"Inserting {total_rows:,} rows into {table_name} (columns: {', '.join(db_cols)})...")

    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, header=False)
        csv_buffer.seek(0)

        copy_sql = f"COPY {table_name}({', '.join(db_cols)}) FROM STDIN WITH (FORMAT CSV);"

        if hasattr(cur, "copy_expert"):
            # psycopg2
            cur.copy_expert(copy_sql, csv_buffer)
        else:
            # psycopg3
            with cur.copy(copy_sql) as copy:
                copy.write(csv_buffer.getvalue())

        conn.commit()
        Logger.success(f"{total_rows:,} rows inserted into {table_name}.")
    except Exception as e:
        conn.rollback()
        Logger.error(f"Error while inserting CSV into {table_name}: {e}")
        raise
    finally:
        conn.close()
