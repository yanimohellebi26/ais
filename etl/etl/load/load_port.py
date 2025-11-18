import io
import pandas as pd
from etl.models.context import PipelineContext
from utils.db import engine
from utils.logger import Logger

def load_port_db(context: PipelineContext, handle_missing: str = "skip", batch_size: int = 50_000):
    df = context.df

    if df.empty:
        Logger.warning("No data to load")
        return

    with engine.connect() as conn:
        country_map = pd.read_sql("SELECT id, code_alpha_2 FROM country", conn).set_index("code_alpha_2")["id"].to_dict()

    df["country_id"] = df["country_code"].map(country_map)

    missing_countries = df.loc[df["country_id"].isna(), "country_code"].unique()
    if len(missing_countries) > 0:
        if handle_missing == "skip":
            Logger.warning(f"Ignored {len(missing_countries)} unknown country codes (mode 'skip').")
            df = df.dropna(subset=["country_id"]).copy()
        else:
            Logger.error(f"Unknown country codes detected, abort insert: {missing_countries}")
            raise Exception(f"Unknown country codes detected: {missing_countries}")

    df["country_id"] = df["country_id"].astype("int32", errors="ignore")
    df["geom_wkt"] = "POINT(" + df["longitude"].astype(str) + " " + df["latitude"].astype(str) + ")"

    df_final = df[["code", "name", "geom_wkt", "country_id"]]

    total_rows = len(df_final)
    Logger.info(f"Batch insert {batch_size:,} lines (total {total_rows:,})...")

    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        for start in range(0, total_rows, batch_size):
            end = min(start + batch_size, total_rows)
            chunk = df_final.iloc[start:end]

            csv_buffer = io.StringIO()
            chunk.to_csv(csv_buffer, index=False, header=False)
            csv_buffer.seek(0)

            copy_sql = """
                COPY port(code, name, geom, country_code)
                FROM STDIN WITH (FORMAT CSV);
            """
            if hasattr(cur, "copy_expert"):
                cur.copy_expert(copy_sql, csv_buffer)
            else:
                with cur.copy(copy_sql) as copy:
                    copy.write(csv_buffer.getvalue())

            Logger.info(f"→ Batch {start:,} to {end:,} inserted ({end}/{total_rows})")
        conn.commit()
        Logger.success(f"{total_rows:,} lines inserted.")
    except Exception as e:
        conn.rollback()
        Logger.error(f"Error while insertion: {e}")
        raise
    finally:
        conn.close()
