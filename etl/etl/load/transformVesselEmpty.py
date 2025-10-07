import pandas as pd

def remove_missing_mmsi(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.dropna(subset=['mmsi'])
    return df_clean