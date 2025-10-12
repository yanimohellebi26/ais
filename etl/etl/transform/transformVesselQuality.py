import pandas as pd
import re


def remove_rows_with_empty(df: pd.DataFrame, required: list) -> pd.DataFrame:

    #Règles de nettoyage
    df.drop(index=df[~df['mmsi'].astype(str).str.fullmatch(r'\d{9}', na=False)].index, inplace=True)
    df.drop(index=df[~(df['vessel_name'].isna() | (df['vessel_name'].astype(str).str.len() <= 50))].index, inplace=True)
    df.drop(index=df[~(df['call_sign'].isna() | df['call_sign'].astype(str).str.fullmatch(r'[A-Z0-9]{4,7}', na=False))].index, inplace=True)
    df.drop(index=df[~(df['vessel_type_id'].isna() | df['vessel_type_id'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.fullmatch(r'[1-9][0-9]?'))].index, inplace=True)
    df.drop(index=df[pd.to_numeric(df['length'], errors='coerce').notna() & (pd.to_numeric(df['length'], errors='coerce').gt(500) | pd.to_numeric(df['length'], errors='coerce').le(0))].index, inplace=True)
    df.drop(index=df[pd.to_numeric(df['width'], errors='coerce').notna() &(pd.to_numeric(df['width'], errors='coerce').gt(80) | pd.to_numeric(df['width'], errors='coerce').le(0))].index, inplace=True)

    #Retirer les '.0'
    int_like = ['status', 'length', 'width', 'cargo', 'vessel_type_id']
    for col in int_like:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.replace(r'\.0$', '', regex=True)

    #pas de 'nan' ni '<NA>'
    if 'imo' in df.columns:
        df['imo'] = df['imo'].fillna('').astype(str).replace({'nan': '', '<NA>': ''}).str.strip()

    df['mmsi'] = df['mmsi'].astype(str)
    return df