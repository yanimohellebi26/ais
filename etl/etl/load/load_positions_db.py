import io
import pandas as pd

from etl.models.context import PipelineContext
from utils.db import engine
from utils.logger import Logger



def load_position_db(context: PipelineContext, handle_missing: str = "skip", batch_size: int = 50_000):
    """
    @Warning temp function, will be removed in future versions
    """
    df = context.df

    if df.empty:
        Logger.warning("No data to load")
        return

    with engine.connect() as conn:
        vessel_map = pd.read_sql("SELECT id, mmsi FROM vessel", conn).set_index("mmsi")["id"].to_dict()

    df["vessel_id"] = df["mmsi"].map(vessel_map)

    # Handle unknowns MMSI
    missing_mmsi = df.loc[df["vessel_id"].isna(), "mmsi"].unique()
    if len(missing_mmsi) > 0:
        if handle_missing == "skip":
            Logger.warning(f"Ignored {len(missing_mmsi)} MMSI unknown (mode 'skip').")
            df = df.dropna(subset=["vessel_id"]).copy()
        else:
            Logger.error(f"Unknown mmsi detected, abort insert")
            raise Exception(f"Unknown mmsi detected, abort insert")


    df["vessel_id"] = df["vessel_id"].astype("int32", errors="ignore")
    df["geom_wkt"] = "POINT(" + df["lon"].astype(str) + " " + df["lat"].astype(str) + ")"

    df_final = df[[
        "vessel_id",
        "base_date_time",
        "sog",
        "cog",
        "heading",
        "status",
        "geom_wkt"
    ]]

    total_rows = len(df_final)
    Logger.info(f"Batch insert {batch_size:,} lines (total {total_rows:,})...")

    # Insert
    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        for start in range(0, total_rows, batch_size):
            end = min(start + batch_size, total_rows)
            chunk = df_final.iloc[start:end]

            csv_buffer = io.StringIO()
            chunk.to_csv(csv_buffer, index=False, header=False)
            csv_buffer.seek(0)

            if hasattr(cur, "copy_expert"):
                # psycopg2 @Deprecated will be removed
                cur.copy_expert("""
                    COPY position_vessel(vessel_id, base_date_time, sog, cog, heading, status_id, geom)
                    FROM STDIN WITH (FORMAT CSV);
                """, csv_buffer)
            else:
                # psycopg3
                copy_sql = """
                    COPY position_vessel(vessel_id, base_date_time, sog, cog, heading, status_id, geom)
                    FROM STDIN WITH (FORMAT CSV);
                """
                with cur.copy(copy_sql) as copy:
                    copy.write(csv_buffer.getvalue())

            Logger.info(f"→ Batch {start:,} to {end:,} inserted ({end}/{total_rows})")
        conn.commit()
        Logger.success(f"{total_rows:,} lines inserted.")
    except Exception as e:
        conn.rollback()
        Logger.error(f"Error while insertion : {e}")
        raise
    finally:
        conn.close()
