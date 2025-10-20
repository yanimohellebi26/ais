import pandas as pd
import numpy as np
from etl.models.context import VesselContext
from etl.utils.db import get_session
from etl.utils.logger import Logger
from sqlalchemy import text

# function that calculates the distance between two geographical points on the Earth's surface
def haversine_km(lat1, lon1, lat2, lon2):
    # conversion to numpy array float
    lat1 = np.asarray(lat1, dtype=float)
    lon1 = np.asarray(lon1, dtype=float)
    lat2 = np.asarray(lat2, dtype=float)
    lon2 = np.asarray(lon2, dtype=float)

    # conversion to radians
    lat1_r = np.radians(lat1)
    lon1_r = np.radians(lon1)
    lat2_r = np.radians(lat2)
    lon2_r = np.radians(lon2)

    dlon = lon2_r - lon1_r
    dlat = lat2_r - lat1_r
    # Haversine formula
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371.0088
    return c * r

# function that calculates speed in km/h
def speed_kmh(distance_km: pd.Series, time_hours: pd.Series) -> pd.Series:
    with np.errstate(divide='ignore', invalid='ignore'):
        speed = distance_km / time_hours
    # replace inf with Nan
    speed = speed.replace([np.inf, -np.inf], np.nan)
    return speed

# function that detects inconsistent vessel positions
def detect_vessel_incoherent_positions(context : VesselContext ,**kwargs) -> VesselContext:
    df = context.df

    if df.empty:
        Logger.warning("No positions detected in the dataset.")
        return context

    id_col, date_col, lat_col, lon_col = "mmsi", "base_date_time", "lat", "lon"
    max_speed_kmh = 130.0

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", utc=True)
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")

    # most recent date in the df
    max_date = df[date_col].max() or pd.Timestamp.utcnow()
    # date 1 month before the most recent date
    interval_date = max_date - pd.DateOffset(months=1)

    # list of unique MMSI numbers
    mmsi_list = df[id_col].dropna().unique().tolist()
    if len(mmsi_list) == 0:
        Logger.info("No valid MMSI found in dataset.")
        return context

    # retrieval of last known positions in the DB
    sql = text("""
               SELECT DISTINCT ON (v.mmsi)
                   v.mmsi,
                   pv.base_date_time AS prev_date,
                   ST_Y(pv.geom::geometry) AS prev_lat,
                   ST_X(pv.geom::geometry) AS prev_lon
               FROM position_vessel pv
               JOIN vessel v ON pv.vessel_id = v.id    
               WHERE v.mmsi = ANY (:mmsis)
                 AND pv.base_date_time >= :interval
                 AND pv.base_date_time <= :max_date
               ORDER BY v.mmsi, pv.base_date_time DESC
               """)

    with get_session() as session:
        # the last known position for each MMSI found
        prev_positions = pd.read_sql(sql, session.bind, params={
            "mmsis": mmsi_list,
            "interval": interval_date,
            "max_date": max_date
        })

    # merge with new positions
    df = df.merge(prev_positions, on="mmsi", how="left")

    # calculation of distance, time and speed
    df["distance_km"] = haversine_km(df["prev_lat"], df["prev_lon"], df[lat_col], df[lon_col])
    df["time_hours"] = (df[date_col] - pd.to_datetime(df["prev_date"], utc=True)).dt.total_seconds() / 3600.0
    df["speed_kmh"] = speed_kmh(df["distance_km"], df["time_hours"].replace(0, np.nan))

    # detection of inconsistencies
    min_dist = 0.1
    too_fast = df["speed_kmh"] > max_speed_kmh
    invalid_time = (df["time_hours"].notna()) & (df["time_hours"] <= 0) & (df["distance_km"] > min_dist)

    df["incoherent"] = too_fast | invalid_time

    # if no previous position, then no inconsistency
    no_prev_pos = df["prev_date"].isna()
    df.loc[no_prev_pos, "incoherent"] = False

    # removal of invalid lines
    initial_len = len(df)
    df.drop(df[df["incoherent"]].index, inplace=True)
    nb_removed = initial_len - len(df)

    # removal of temporary columns
    df.drop(columns=[
        "prev_date", "prev_lat", "prev_lon",
        "distance_km", "time_hours", "speed_kmh", "incoherent",
    ], inplace=True, errors="ignore")

    # log
    Logger.info(f"T-Detection complete : Removed {nb_removed}/{initial_len} lines ({round(nb_removed / initial_len * 100, 2)}%) lines selected.")

    context.df = df
    return context