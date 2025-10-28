import pandas as pd

from etl.models.context import PipelineContext
from utils.logger import Logger

def clean_vessel_duplication(context : PipelineContext, **kwargs) -> PipelineContext:
    df = context.df
    date_col = 'base_date_time'
    id_col = 'mmsi'
    before = len(df)
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
    cleaned_count = len(df_cleaned)

    Logger.info(f"T-Dupe : {cleaned_count}/{before} ({round(cleaned_count / before * 100, 2)}%) lines selected")

    context.df = df_cleaned
    return context