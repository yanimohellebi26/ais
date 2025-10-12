import pandas as pd

def remove_rows_with_empty(df: pd.DataFrame, required: list) -> pd.DataFrame:
    df.dropna(subset=required, inplace=True)