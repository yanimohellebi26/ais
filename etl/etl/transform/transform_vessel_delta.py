
import pandas as pd

from sqlalchemy import text

from etl.models.context import VesselContext
from etl.utils.timer import timer
from etl.utils.db import get_session
from etl.utils.logger import Logger


def get_vessels_db(context : VesselContext ,**kwargs) -> VesselContext:
    """
    Fetch all vessels data from the database
    :return:
    """
    with get_session() as session:
        result = session.execute(text(
            """
            SELECT 
                v.id AS vessel_id,
                v.mmsi AS mmsi,
                v.imo AS imo,
                v.vessel_name as vessel_name,
                v.call_sign as call_sign,
                v.vessel_type_id as vessel_type_id,
                v.cargo_type_id as cargo_type_id,
                v.length as length,
                v.width as width,
                v.draft as draft,
                v.transceiver_class as transceiver_class,
                v.locked as locked,
                v.created_at as created_at,
                v.last_update as last_update,
                vt.id AS vessel_type_id
            FROM vessel v 
            LEFT JOIN public.vessel_type vt on v.vessel_type_id = vt.id
            """

        )).mappings().all()
        df = pd.DataFrame.from_records(result)

        context.df_db = df
        return context
def transform_vessel_delta(context : VesselContext,**kwargs) -> VesselContext:
    """
    Apply delta detection on new data, use current database vessel for comparison
    :param context: Must hold df, and db_df
    :return: new dataset clear
    """
    new_df = context.df
    db_df = context.df_db

    if len(db_df) == 0:
        Logger.info(f"T-Vessel delta : database empty all lines selected")
        return context

    #Change type for merge on key mmsi
    new_df['mmsi'] = new_df['mmsi'].astype(str)
    db_df['mmsi'] = db_df['mmsi'].astype(str)
    # Merge
    merged = pd.merge(new_df, db_df, how='left', on='mmsi', suffixes=('_new', ''))
    # Detect new from (new MMSI)
    new_boats = merged[merged["vessel_id"].isna()]

    # Columns to check for new values
    cols_to_check = [
        "vessel_name", "imo", "call_sign", "vessel_type_id",
        "cargo_type_id", "length", "width", "draft",
        "transceiver_class"
    ]

    # Construct boolean mask
    has_changes = False
    fills_missing_info = False
    for col in cols_to_check:
        # Case when value different and no-null -> check differences
        mask = (~merged[f"{col}_new"].isna()) & (merged[f"{col}_new"] != merged[col])
        has_changes |= mask

        # Case when new value, different, AND older value null -> complete an empty field
        mask_fill = (~merged[f"{col}_new"].isna()) & (merged[col].isna())
        fills_missing_info |= mask_fill

    # Update new more recent data + changed
    mask_updates = (
            (~merged["vessel_id"].isna()) &
            (merged["locked"] == False) &
            (merged["last_update_new"] >= merged["last_update"]) &
            has_changes
    )

    # Updates to fill missing value (even if older data)
    mask_fills = (
            (~merged["vessel_id"].isna()) &
            (merged["locked"] == False) &
            (~mask_updates) &  # <--- exclude the ones already in updates
            fills_missing_info
    )
    updates = merged[mask_updates]
    fills = merged[mask_fills]

    # Combine
    final = pd.concat([new_boats, updates, fills], ignore_index=True)
    final = final[[c for c in final.columns if c.endswith("_new") or c == "mmsi"]]
    final = final.rename(columns={c: c.replace("_new", "") for c in final.columns})

    Logger.info(f"T-Vessel delta : {len(final)}/{len(new_df)} ({round(len(final)/len(new_df) * 100,2)}%) lines selected")

    context.df = final
    return context



