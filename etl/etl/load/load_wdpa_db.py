from utils.timer import timer
from utils.db import engine
from utils.logger import Logger

from etl.models.context import PipelineContext

import geopandas as gpd
import pandas as pd
import io

from sqlalchemy import text

PA_COLUMNS = [
    "SITE_ID", "NAME", "DESIG_ENG", "DESIG_TYPE", "IUCN_CAT",
    "REALM", "REP_M_AREA", "GIS_M_AREA", "REP_AREA", "GIS_AREA",
    "NO_TAKE", "NO_TK_AREA", "STATUS", "STATUS_YR",
    "CONS_OBJ", "ISO3", "geometry_wkb",
]

PA_PLOT_COLUMNS = ["SITE_PID", "SITE_ID"]

CREATE_TMP_WDPA = """
    CREATE TEMP TABLE IF NOT EXISTS tmp_wdpa_load (
        SITE_ID     integer,
        NAME        text,
        DESIG_ENG   text,
        DESIG_TYPE  text,
        IUCN_CAT    text,
        REALM       text,
        REP_M_AREA  double precision,
        GIS_M_AREA  double precision,
        REP_AREA    double precision,
        GIS_AREA    double precision,
        NO_TAKE     text,
        NO_TK_AREA  double precision,
        STATUS      text,
        STATUS_YR   integer,
        CONS_OBJ    text,
        ISO3        varchar(255),
        geometry_wkb text
    ) ON COMMIT DELETE ROWS;
    """

CREATE_TMP_PA_PLOT = """
    CREATE TEMP TABLE IF NOT EXISTS tmp_pa_plot_load (
        SITE_PID text,
        SITE_ID  integer
    ) ON COMMIT DELETE ROWS;
"""

UPSERT_PA_SQL = """
    INSERT INTO protected_areas (
        SITE_ID, NAME, DESIG_ENG, DESIG_TYPE, IUCN_CAT,
        REALM, REP_M_AREA, GIS_M_AREA, REP_AREA, GIS_AREA,
        NO_TAKE, NO_TK_AREA, STATUS, STATUS_YR,
        CONS_OBJ, ISO3, geometry
    )
    SELECT DISTINCT ON (SITE_ID)
        SITE_ID, NAME, DESIG_ENG,
        DESIG_TYPE::desig_type, IUCN_CAT::iucn_cat,
        REALM::realm, REP_M_AREA, GIS_M_AREA, REP_AREA, GIS_AREA,
        NO_TAKE::no_take, NO_TK_AREA, STATUS::status, STATUS_YR, CONS_OBJ::cons_obj,
        ISO3,
        ST_GeomFromWKB(decode(geometry_wkb, 'hex'), 4326)
    FROM tmp_wdpa_load
    ON CONFLICT (SITE_ID) DO UPDATE SET
        NAME       = EXCLUDED.NAME,
        DESIG_ENG  = EXCLUDED.DESIG_ENG,
        DESIG_TYPE = EXCLUDED.DESIG_TYPE,
        IUCN_CAT   = EXCLUDED.IUCN_CAT,
        REALM      = EXCLUDED.REALM,
        REP_M_AREA = EXCLUDED.REP_M_AREA,
        GIS_M_AREA = EXCLUDED.GIS_M_AREA,
        REP_AREA   = EXCLUDED.REP_AREA,
        GIS_AREA   = EXCLUDED.GIS_AREA,
        NO_TAKE    = EXCLUDED.NO_TAKE,
        NO_TK_AREA = EXCLUDED.NO_TK_AREA,
        STATUS     = EXCLUDED.STATUS,
        STATUS_YR  = EXCLUDED.STATUS_YR,
        CONS_OBJ   = EXCLUDED.CONS_OBJ,
        ISO3       = EXCLUDED.ISO3,
        geometry   = EXCLUDED.geometry;
"""

UPSERT_PA_PLOT_SQL = """
    INSERT INTO pa_plot (SITE_PID, SITE_ID)
    SELECT SITE_PID, SITE_ID FROM tmp_pa_plot_load
    ON CONFLICT (SITE_PID, SITE_ID) DO NOTHING;
"""

def _geometry_to_wkb_hex(geom) -> str | None:
    """
    Convert a Shapely geometry to WKB hex.
    """
    if geom is None:
        return None
    try:
        return geom.wkb_hex
    except Exception as e:
        return None
    
def _detect_conflicts(cur, site_ids: list) -> list:
    """
    Return potential SITE_IDs already in the database (if any).
    """

    if not site_ids:
        return []
    
    cur.execute("SELECT SITE_ID FROM protected_areas WHERE SITE_ID = ANY(%s)", (site_ids,))

    return [row[0] for row in cur.fetchall()]

@timer
def load_wdpa_db(context: PipelineContext, batch_size: int = 10_000) -> PipelineContext:
    """
    Insert transformed WDPA data into the database 
    """

    gdf: gpd.GeoDataFrame = context.df

    if gdf is None or gdf.empty:
        Logger.warning("load_wdpa_db : empty or None GeoDataFrame, nothing to load.")
        return context
    
    Logger.info(f"load_wdpa_db : loading {len(gdf):,} features into database...")

    gdf = gdf.copy()
    gdf["geometry_wkb"] = gdf["geometry"].apply(_geometry_to_wkb_hex)
    n_null_geom = gdf["geometry_wkb"].isna().sum()
    if n_null_geom:
        Logger.warning(f"{n_null_geom} features have null or invalid geometry, ignored during load.")
        gdf = gdf.dropna(subset=["geometry_wkb"])

    total_rows = len(gdf)
    Logger.info(f"load_wdpa_db : {total_rows:,} features to load, batch {batch_size:,}...")

    conn = engine.raw_connection()

    try:
        cur = conn.cursor()

        cur.execute(CREATE_TMP_WDPA)
        cur.execute(CREATE_TMP_PA_PLOT)

        for start in range(0, total_rows, batch_size):
            end = min(start + batch_size, total_rows)
            chunk = gdf.iloc[start:end]

            chunk_ids = chunk["SITE_ID"].dropna().astype(int).tolist()
            conflicting = _detect_conflicts(cur, chunk_ids)

            if conflicting:
                Logger.warning(f"Batch {start:,} - {end:,} : {len(conflicting)} SITE_IDs already in base -> updated")

            pa_chunk = chunk[PA_COLUMNS].copy()
            csv_buffer = io.StringIO()
            pa_chunk.to_csv(csv_buffer, index=False, header=False, na_rep="\\N")
            csv_buffer.seek(0)

            copy_pa_sql = """
                COPY tmp_wdpa_load (
                SITE_ID, NAME, DESIG_ENG, DESIG_TYPE, IUCN_CAT,
                REALM, REP_M_AREA, GIS_M_AREA, REP_AREA, GIS_AREA,
                NO_TAKE, NO_TK_AREA, STATUS, STATUS_YR,
                CONS_OBJ, ISO3, geometry_wkb
                ) FROM STDIN WITH (FORMAT CSV, NULL '\\N')
            """

            with cur.copy(copy_pa_sql) as copy:
                copy.write(csv_buffer.getvalue())

            cur.execute(UPSERT_PA_SQL)

            pa_plot_chunk = chunk[PA_PLOT_COLUMNS].copy()
            csv_buffer_bis = io.StringIO()
            pa_plot_chunk.to_csv(csv_buffer_bis, index=False, header=False, na_rep="\\N")
            csv_buffer_bis.seek(0)

            with cur.copy("COPY tmp_pa_plot_load (SITE_PID, SITE_ID) FROM STDIN WITH (FORMAT CSV, NULL '\\N')") as copy:
                copy.write(csv_buffer_bis.getvalue())

            cur.execute(UPSERT_PA_PLOT_SQL)

            Logger.info(f"Batch {start:,} - {end:,} : loaded ({end}/{total_rows}).")

        conn.commit()
        Logger.success(f"load_wdpa_db : {total_rows:,} lines loaded in protected_areas + pa_plot.")

    except Exception as e:
        conn.rollback()
        Logger.error(f"Error during load_wdpa_db : {e}")
        raise
    finally:
        conn.close()

    return context