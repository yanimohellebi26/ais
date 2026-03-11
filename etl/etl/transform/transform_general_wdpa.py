from utils.db import engine
from utils.logger import Logger
from utils.timer import timer

from etl.models.context import PipelineContext

import geopandas as gpd
import pandas as pd

DB_COLUMNS = {
    "SITE_ID", "NAME", "DESIG_ENG", "DESIG_TYPE", "IUCN_CAT",
    "REALM", "REP_M_AREA", "GIS_M_AREA", "REP_AREA", "GIS_AREA",
    "NO_TAKE", "NO_TK_AREA", "STATUS", "STATUS_YR",
    "CONS_OBJ", "ISO3", "geometry",
}

COLUMN_ENUM_TYPE = {
    "DESIG_TYPE": "desig_type",
    "IUCN_CAT":   "iucn_cat",
    "REALM":      "realm",
    "NO_TAKE":    "no_take",
    "STATUS":     "status",
    "CONS_OBJ":   "cons_obj",
}

def _fetch_enum_values() -> dict[str, set[str]]:
    """
    Fetch the possible values for each enum column from the database and return them as a dict.

    Returns:
        dict[db_column_name, set[enum_value]]
    """

    enum_type_names = tuple(COLUMN_ENUM_TYPE.values())
    query = f"""
        SELECT t.typname, e.enumlabel
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname IN {enum_type_names}
        ORDER BY t.typname, e.enumsortorder;
    """

    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    type_to_col = {v: k for k, v in COLUMN_ENUM_TYPE.items()}
    enum_values: dict[str, set[str]] = {}

    for type_name, label in rows:
        col = type_to_col[type_name]
        enum_values.setdefault(col, set()).add(label)

    Logger.info(f"ENUM loaded : { {k: len(v) for k, v in enum_values.items()} }")
    
    return enum_values

@timer
def transform_wdpa(context: PipelineContext) -> PipelineContext:
    """
    Transform the GeoDataFrame WDPA by applying the following steps:
    - Suppress columns not in DB_COLUMNS
    - Validate the ENUM values by dinamically fetching values from database
    - convert to EPSG:4326 if necessary
    """

    gdf: gpd.GeoDataFrame = context.df

    if gdf is None or gdf.empty:
        Logger.warning("transform_wdpa : empty GeoDataFrame, nothing to transform.")
        return context
    
    Logger.info(f"transform_wdpa : {len(gdf):,} lines to transform.")

    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        Logger.info(f"transform_wdpa : converting CRS from {gdf.crs} to EPSG:4326.")
        gdf = gdf.to_crs(epsg=4326)

    elif gdf.crs is None:
        Logger.warning("CRS undefined, we assume it's EPSG:4326.")
        gdf = gdf.set_crs(epsg=4326)

    cols_to_keep = [c for c in gdf.columns if c in DB_COLUMNS]
    cols_ignored = [c for c in gdf.columns if c not in DB_COLUMNS]
    if cols_ignored:
        Logger.warning(f"transform_wdpa : {len(cols_ignored)} columns will be ignored : {cols_ignored}")
    gdf = gdf[cols_to_keep].copy()

    enum_values = _fetch_enum_values()

    for col, valid_set in enum_values.items():
        if col not in gdf.columns:
            continue

        mask_invalid = ~gdf[col].isin(valid_set) & gdf[col].notna()
        n_invalid = mask_invalid.sum()

        if n_invalid > 0:
            Logger.warning(f"Column '{col}' : {n_invalid} invalid value(s) found -> NULL.")

        gdf.loc[mask_invalid, col] = None

    gdf["SITE_ID"]   = pd.to_numeric(gdf["SITE_ID"],    errors="coerce").astype("Int32")
    gdf["STATUS_YR"] = pd.to_numeric(gdf["STATUS_YR"],  errors="coerce").astype("Int32")

    n_null_geom = gdf["geometry"].isna().sum()
    if n_null_geom:
        Logger.warning(f"transform_wdpa : {n_null_geom} null geometry removed.")
        gdf = gdf.dropna(subset=["geometry"])

    Logger.info(f"transform_wdpa : {len(gdf):,} lines after transformation.")
    context.df = gdf
    return context