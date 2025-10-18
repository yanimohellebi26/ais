import pandas as pd

from etl.models.context import VesselContext
from etl.utils.logger import Logger


def remove_rows_with_empty(context: VesselContext, required: list) -> VesselContext:
    df = context.df
    before = len(df)
    df.dropna(subset=required, inplace=True)
    Logger.info(f"T-Empty : {len(df)}/{before} ({round(len(df)/before * 100,2)}%) lines selected")
    context.df = df
    return context

def remove_rows_with_wrong_format(context: VesselContext) -> VesselContext:
    df = context.df
    before = len(df)
    #cleaning rules
    if 'mmsi' in df.columns:
        df.drop(index=df[~df['mmsi'].astype(str).str.fullmatch(r'\d{9}', na=False)].index, inplace=True)

    if 'vessel_name' in df.columns:
        df.drop(index=df[~(df['vessel_name'].isna() | (df['vessel_name'].astype(str).str.len() <= 100))].index, inplace=True)

    if 'call_sign' in df.columns:
        df.drop(index=df[~(df['call_sign'].isna() | df['call_sign'].astype(str).str.len() <= 20)].index, inplace=True)

    for col in ['vessel_type_id', 'cargo_type_id']:
        if col in df.columns:
            df.drop(index=df[~(df[col].isna() | ((df[col] >= 0) & (df[col] <= 1025)))].index, inplace=True)

    if 'length' in df.columns:
        df.drop(index=df[~(df['length'].isna() | ((df['length'] >= 0) & (df['length'] <= 370)))].index, inplace=True)

    if 'width' in df.columns:
        df.drop(index=df[~(df['width'].isna() | ((df['width'] >= 0) & (df['width'] <= 60)))].index, inplace=True)

    if 'draft' in df.columns:
        df.drop(index=df[~(df['draft'].isna() | ((df['draft'] >= 0) & (df['draft'] <= 25)))].index, inplace=True)

    if 'base_date_time' in df.columns:
        df.drop(index=df[df['base_date_time'].isna() |
                         (df['base_date_time'] > pd.Timestamp.now())].index, inplace=True)
    if 'transceiver_class' in df.columns:
        df['transceiver_class'] = df['transceiver_class'].astype(str).str.strip().str.upper()
        df.drop(index=df[~df['transceiver_class'].isin(['A', 'B'])].index, inplace=True)

    Logger.info(f"T-QC : {len(df)}/{before} ({round(len(df)/before * 100,2)}%) lines selected")

    context.df = df
    return context

def normalize_ais(context: VesselContext) -> VesselContext:
    """
    Normalize AIS data
    """
    df = context.df

    # Replace all null value by None
    df = df.astype(str).replace({"nan": None, "<NA>": None, "None": None}).replace("None", None)

    # Type int fields
    for col in ("vessel_type_id", "cargo_type_id"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Type double fields
    for col in ("length", "width", "draft"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    # Date field
    df["base_date_time"] = pd.to_datetime(df["base_date_time"], errors="coerce")

    context.df = df
    return context