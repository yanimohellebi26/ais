import pandas as pd

from etl.models.context import PipelineContext
from utils.logger import Logger

"""
def filter_marine_coastal(context: PipelineContext) -> PipelineContext:
    df = context.df
    before = len(df)

    df = df[df["REALM"].fillna("").str.contains("Marine|Coastal", case=False)]

    Logger.info(f"Filter REALM: {len(df)}/{before} kept")

    context.df = df
    return context
"""
def clean_wdpa(context: PipelineContext) -> PipelineContext:
    df = context.df

    Logger.info("Cleaning WDPA dataset")

    for col in ["NAME", "DESIG_ENG", "DESIG_TYPE", "IUCN_CAT", "OWN_TYPE"]:
        if col in df.columns:
            Logger.info(f"-> Cleaning {col} column...")
            df[col] = df[col].astype(str).str.strip()
            Logger.success(f"Cleaned {col} column")

    for col in ["REP_AREA", "GIS_AREA", "REP_M_AREA", "GIS_M_AREA", "NO_TK_AREA"]:
        if col in df.columns:
            Logger.info(f"-> Cleaning {col} column...")
            df[col] = pd.to_numeric(df[col], errors="coerce")
            Logger.success(f"Cleaned {col} column")

    if "STATUS_YR" in df.columns:
        Logger.info("-> Cleaning status_yr column...")
        df["STATUS_YR"] = pd.to_numeric(df["STATUS_YR"], errors="coerce").astype("Int64")
        Logger.success(f"Cleaned STATUS_YR column")

    if "geometry" in df.columns:
        Logger.info("-> Cleaning geometry column...")

        invalid_mask = ~df["geometry"].is_valid
        invalid_count = invalid_mask.sum()

        if invalid_count > 0:
            Logger.warning(f"Found {invalid_count} invalid geometries. Attempting to fix with buffer(0)...")
            df.loc[invalid_mask, "geometry"] = df.loc[invalid_mask, "geometry"].buffer(0)
            Logger.success(f"Fixed {invalid_count} geometries")

        Logger.success(f"Cleaned geometry column")

    Logger.success("Cleaning finished")

    context.df = df
    return context

def map_to_mcd(context: PipelineContext) -> PipelineContext:
    df = context.df
    if df.empty:
        return context

    Logger.info("Mapping WDPA -> MCD")

    df = df.rename(columns={
        "SITE_ID": "site_id",
        "SITE_PID": "site_pid",
        "NAME": "name",
        "DESIG_ENG": "desig_eng",
        "DESIG_TYPE": "desig_type",
        "IUCN_CAT": "iucn_cat",
        "ISO3": "iso3",
        "STATUS": "status",
        "STATUS_YR": "status_yr",
        "OWN_TYPE": "own_type",
        "NO_TAKE": "no_take",
        "NO_TK_AREA": "no_tk_area",
        "REP_AREA": "rep_area",
        "GIS_AREA": "gis_area",
        "REP_M_AREA": "rep_m_area",
        "GIS_M_AREA": "gis_m_area",
        "REALM": "realm"
    })

    if "desig_type" in df.columns:
        df["site_type"] = df["desig_type"].apply(
            lambda x: "OECM" if "OECM" in str(x).upper() else "PA"
        )

    context.df = df
    return context

def split_tables(context: PipelineContext):
    if context.df.empty:
        Logger.warning("Empty dataframe, no tables to split")
        context.pa_infos = pd.DataFrame()
        context.protected_area = pd.DataFrame()
        return context
    
    df = context.df

    Logger.info("Splitting tables")

    pa_infos = df[[
        "site_id", "name", "site_type", "iso3",
        "status", "status_yr"
    ]].drop_duplicates(subset=["site_id"])

    protected_area = df[[
        "site_pid", "site_id",
        "desig_eng", "desig_type", "iucn_cat",
        "realm", "no_take",
        "no_tk_area", "rep_area", "gis_area",
        "rep_m_area", "gis_m_area",
        "own_type", "geometry"
    ]]

    context.pa_infos = pa_infos
    context.protected_area = protected_area

    Logger.info(f"pa_infos: {len(pa_infos):,}")
    Logger.info(f"protected_area: {len(protected_area):,}")

    return context