import pandas as pd

def remove_rows_with_empty(df: pd.DataFrame, required: list) -> pd.DataFrame:
    df_clean = df.dropna(subset=required)
    return df_clean