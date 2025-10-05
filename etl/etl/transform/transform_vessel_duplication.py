import pandas as pd

from etl.utils.logger import Logger

def clean_vessel_duplication(df: pd.DataFrame, id_col: str="mmsi", date_col: str = "date") -> pd.DataFrame:
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # Sorting by descending date
    df = df.sort_values(by=date_col, ascending=False)

    # function that merges duplicates
    def merge_rows(group: pd.DataFrame) -> pd.Series:
        merged = {}
        for col in group.columns:
            non_na = group[col].dropna()
            merged[col] = non_na.iloc[0] if not non_na.empty else pd.NA
        return pd.Series(merged)

    # merging of lines with the same mmsi
    df_cleaned = df.groupby(id_col, as_index=False).apply(merge_rows)

    # logging of deleted duplicates
    initial_count = len(df)
    cleaned_count = len(df_cleaned)
    duplicates_info = initial_count - cleaned_count

    Logger.info(f"Cleaning complete. Total lines retained: {cleaned_count}. Duplicates info removed: {duplicates_info}")

    return df_cleaned