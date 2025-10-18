import pandas as pd
from datetime import datetime
from etl.utils.logger import Logger
from etl.utils.timer import timer

@timer
def downsample_ais(context, group_cols=None, time_col="BaseDateTime"):
    """
    Downsample AIS data in a context.df DataFrame:
    - Keep only the first and last timestamp per group (default MMSI, LAT, LON)
    - Organize them in consecutive pairs
    """
    if group_cols is None:
        group_cols = ["MMSI", "LAT", "LON"]

    df = context.df
    Logger.info(f"[{datetime.now():%H:%M:%S}] Starting downsampling AIS data ...")
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
    Logger.info(f"[{datetime.now():%H:%M:%S}] Downsampling complete: "
                f"{original_len} → {reduced_len} rows ({reduction_pct:.2f}% reduction)")

    # Update context and return
    context.df = df_downsampled
    return context
