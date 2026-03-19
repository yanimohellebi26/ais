from etl.models.context import PipelineContext
from utils.logger import Logger

import io
from utils.db import engine


def load_pa_infos(context: PipelineContext, batch_size: int = 5_000):
    df = context.pa_infos

    if df.empty:
        Logger.warning("No pa_infos to load")
        return

    df = df.where(df.notna(), None)

    conn = engine.raw_connection()
    try:
        cur = conn.driver_connection.cursor()
        total = len(df)

        for start in range(0, total, batch_size):
            chunk = df.iloc[start:start + batch_size]

            csv_buffer = io.StringIO()
            chunk.to_csv(csv_buffer, index=False, header=False, na_rep="")
            csv_buffer.seek(0)

            sql = """
                COPY pa_infos(site_id, name, site_type, iso3, status, status_yr)
                FROM STDIN WITH (FORMAT CSV, NULL '');
            """

            with cur.copy(sql) as copy:
                copy.write(csv_buffer.getvalue())

            conn.commit()
            Logger.info(f"Inserted batch: {min(start + batch_size, total):,} / {total:,}")

        Logger.success(f"{total:,} pa_infos inserted")

    except Exception as e:
        conn.rollback()
        Logger.error(f"Error pa_infos: {e}")
        raise
    finally:
        conn.close()

    return context


def load_protected_area(context: PipelineContext, batch_size: int = 5_000):
    df = context.protected_area.copy()

    if df.empty:
        Logger.warning("No protected_area to load")
        return

    df["geom_wkt"] = df["geometry"].apply(lambda g: f"SRID=4326;{g.wkt}" if g is not None and not g.is_empty else None)

    df_final = df[[
        "site_pid", "site_id",
        "desig_eng", "desig_type", "iucn_cat",
        "realm", "no_take",
        "no_tk_area", "rep_area", "gis_area",
        "rep_m_area", "gis_m_area",
        "own_type", "geom_wkt"
    ]]

    df_final = df_final.where(df_final.notna(), None)

    conn = engine.raw_connection()
    try:
        cur = conn.driver_connection.cursor()

        total = len(df_final)

        for start in range(0, total, batch_size):
            chunk = df_final.iloc[start:start + batch_size]

            csv_buffer = io.StringIO()
            chunk.to_csv(csv_buffer, index=False, header=False, na_rep="")
            csv_buffer.seek(0)

            sql = """
                COPY protected_area(
                    site_pid, site_id,
                    desig_eng, desig_type, iucn_cat,
                    realm, no_take,
                    no_tk_area, rep_area, gis_area,
                    rep_m_area, gis_m_area,
                    own_type, geometry
                )
                FROM STDIN WITH (
                    FORMAT CSV, NULL '' 
                );
            """

            with cur.copy(sql) as copy:
                copy.write(csv_buffer.getvalue())

            conn.commit()
            Logger.info(f"Inserted batch: {min(start + batch_size, total):,} / {total:,}")
        
        Logger.success(f"{total:,} protected_area inserted")

    except Exception as e:
        conn.rollback()
        Logger.error(f"Error protected_area: {e}")
        raise
    finally:
        conn.close()

    return context