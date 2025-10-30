import pandas as pd

from etl.models.context import PipelineContext
from utils.logger import Logger

def downsample_ais(context: PipelineContext, group_cols=None, time_col="base_date_time"):
    """
    Downsample AIS data in a context.df DataFrame:
    - Keep only the first and last timestamp per group (default MMSI, LAT, LON)
    - Organize them in consecutive pairs
    """

    if group_cols is None:
        group_cols = ["mmsi", "lat", "lon"]

    df = context.df

    original_len = len(df)
    # Validate required columns
    required = group_cols + [time_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if df[required].isnull().any().any():
        raise ValueError("Critical columns contain missing values.")

    # Sort to prepare for grouping
    df = df.sort_values(by=group_cols + [time_col])

    # Get first and last rows per group
    grouped = df.groupby(group_cols, sort=False)
    first_indices = grouped[time_col].idxmin()
    last_indices = grouped[time_col].idxmax()

    # Combine and keep only unique indices
    indices = pd.unique(pd.concat([first_indices, last_indices]))
    df_downsampled = df.loc[indices].copy()

    # Sort so each group's two rows are consecutive
    df_downsampled = df_downsampled.sort_values(by=group_cols + [time_col]).reset_index(drop=True)

    reduced_len = len(df_downsampled)
    reduction_pct = 100 * (original_len - reduced_len) / original_len
    Logger.info(f" T-Downsampling {reduced_len} / {original_len} rows ({reduction_pct:.2f}% reduction)")

    # Update context and return
    context.df = df_downsampled
    return context
