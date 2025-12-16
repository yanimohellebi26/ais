"""
Transform: AIS trajectory preprocessing for ML training.

Main functions:
- extract_trajectories: Extract trajectories by MMSI
- correct_speed: Fix aberrant speeds
- correct_position: Fix aberrant positions
- resample_trajectories: Uniform temporal resampling
- assign_dataset_splits: Assign train/val/test splits
"""

import io
import math
import argparse
import numpy as np
import pandas as pd
from typing import Optional, Tuple
from dataclasses import dataclass
from multiprocessing import Pool, cpu_count
from functools import partial

from etl.models.context import PipelineContext
from utils.db import engine
from utils.logger import Logger


@dataclass
class TrajectoryConfig:
    """Configuration for trajectory preprocessing."""
    # Physical parameters (from model_.ipynb)
    amax_knots: float = 0.15  # Max acceleration in knots/s
    amax_ms: float = 0.15 * 0.514  # Max acceleration in m/s
    max_gap_seconds: int = 600  # Max gap 10 min (new traj if dt > 600)
    min_points_per_traj: int = 24  # Minimum 24 points per trajectory
    max_duration_hours: float = 24.0  # Max trajectory duration
    min_mean_sog: float = 1.0  # Min mean SOG to keep trajectory
    resample_interval: str = "1min"  # Resample to 1 minute (as model_.ipynb)
    
    # AIS filters (from clean_ais)
    sog_min: float = 0.0  # SOG > 0
    sog_max: float = 30.0  # SOG <= 30 knots
    cog_min: float = 0.0
    cog_max: float = 360.0
    vessel_type_min: int = 20
    vessel_type_max: int = 90
    
    # Dataset splits
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    
    # Geographic zone (UTM zone 31)
    utm_zone: int = 31
    utm_hemisphere: str = "north"
    
    # Correction iterations
    correction_iterations: int = 3  # Number of correction passes
    
    # Parallel processing (optimized for 96 cores, 1TB RAM)
    n_workers: int = 64  # Use 64 workers for parallel processing


CONFIG = TrajectoryConfig()

def haversine_distance(lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """
    Calculate distance in meters between two points using Haversine formula.
    Works for any coordinates worldwide.
    """
    R = 6371000  # Earth radius in meters
    
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    return R * c


def latlon_to_local_meters(lon: np.ndarray, lat: np.ndarray, lon0: float = None, lat0: float = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert lat/lon to local metric coordinates (meters).
    Uses simple equirectangular projection centered on the provided reference point.
    """
    # Reference point (center of data if not provided)
    if lat0 is None:
        lat0 = np.mean(lat)
    if lon0 is None:
        lon0 = np.mean(lon)
    
    # Convert to radians
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    lat0_rad = np.radians(lat0)
    lon0_rad = np.radians(lon0)
    
    # Earth radius in meters
    R = 6371000
    
    # Equirectangular projection
    x = R * (lon_rad - lon0_rad) * np.cos(lat0_rad)
    y = R * (lat_rad - lat0_rad)
    
    return x, y


def local_meters_to_latlon(x: np.ndarray, y: np.ndarray, lon0: float, lat0: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert local metric coordinates back to lat/lon.
    """
    R = 6371000
    lat0_rad = np.radians(lat0)
    lon0_rad = np.radians(lon0)
    
    lat_rad = y / R + lat0_rad
    lon_rad = x / (R * np.cos(lat0_rad)) + lon0_rad
    
    return np.degrees(lat_rad), np.degrees(lon_rad)


# Keep old functions for compatibility but they're not used anymore
def latlon_to_utm(lon: np.ndarray, lat: np.ndarray, zone: int = 31, northern: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """Convert lat/lon to local meters (simplified, works worldwide). DEPRECATED."""
    return latlon_to_local_meters(lon, lat)


def utm_to_latlon(x: np.ndarray, y: np.ndarray, zone: int = 31, northern: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """Not used anymore - positions are kept as lat/lon. DEPRECATED."""
    # This function should not be called in the new implementation
    raise NotImplementedError("Use local_meters_to_latlon instead")

def load_raw_data_from_db(context: PipelineContext, limit: Optional[int] = None) -> PipelineContext:
    """
    Load raw data from database.
    """
    Logger.info("Loading data from database...")
    
    limit_clause = f"LIMIT {limit}" if limit else ""
    
    query = f"""
    SELECT 
        v.mmsi,
        pv.base_date_time,
        ST_Y(pv.geom::geometry) as lat,
        ST_X(pv.geom::geometry) as lon,
        pv.sog,
        pv.cog,
        v.vessel_type_id as vessel_type
    FROM position_vessel pv
    JOIN vessel v ON pv.vessel_id = v.id
    WHERE pv.sog IS NOT NULL 
      AND pv.cog IS NOT NULL
      AND pv.geom IS NOT NULL
    ORDER BY v.mmsi, pv.base_date_time
    {limit_clause}
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    Logger.info(f"Loaded {len(df):,} points for {df['mmsi'].nunique():,} vessels")
    context.df = df
    return context

def clean_ais_data(context: PipelineContext) -> PipelineContext:
    """
    Initial AIS data cleaning.
    """
    df = context.df.copy()
    before = len(df)
    
    # Datetime conversion and sorting
    df["base_date_time"] = pd.to_datetime(df["base_date_time"])
    df = df.sort_values(["mmsi", "base_date_time"])
    
    # Numeric conversion
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df['sog'] = pd.to_numeric(df['sog'], errors='coerce')
    df['cog'] = pd.to_numeric(df['cog'], errors='coerce')
    
    # Remove duplicates (same MMSI + timestamp)
    df = df.drop_duplicates(subset=["mmsi", "base_date_time"])
    
    # SOG filters (as model_.ipynb: SOG > 0 and SOG <= 30)
    df = df[df["sog"] > CONFIG.sog_min]
    df = df[df["sog"] <= CONFIG.sog_max]
    
    # COG filter (0-360)
    df = df[df["cog"].between(CONFIG.cog_min, CONFIG.cog_max)]
    
    # VesselType filter if present (20-90 as model_.ipynb)
    if 'vessel_type' in df.columns:
        df = df[df["vessel_type"].between(CONFIG.vessel_type_min, CONFIG.vessel_type_max)]
    
    # Filter dt >= 1s between consecutive points of same vessel
    df["dt"] = df.groupby("mmsi")["base_date_time"].diff().dt.total_seconds()
    df = df[(df["dt"].isna()) | (df["dt"] >= 1)]
    df = df.drop(columns=["dt"])
    
    df = df.reset_index(drop=True)
    
    Logger.info(f"Cleaning: {len(df):,}/{before:,} points kept ({100*len(df)/before:.1f}%)")
    context.df = df
    return context

def extract_trajectories_for_vessel(vessel_data):
    """Extract trajectories for a single vessel (for parallel processing)."""
    mmsi, g = vessel_data
    
    g = g.sort_values("base_date_time").copy()
    g["dt"] = g["base_date_time"].diff().dt.total_seconds()
    
    # New trajectory if gap > 600s
    g["traj_id_local"] = (g["dt"] > CONFIG.max_gap_seconds).cumsum()
    
    trajs = []
    for _, t in g.groupby("traj_id_local"):
        # Filter: minimum 24 points
        if len(t) < CONFIG.min_points_per_traj:
            continue
        
        # Filter: max duration 24h
        duration = (t["base_date_time"].iloc[-1] - t["base_date_time"].iloc[0]).total_seconds() / 3600
        if duration > CONFIG.max_duration_hours:
            continue
        
        # Filter: mean SOG >= 1 knot
        if t["sog"].mean() < CONFIG.min_mean_sog:
            continue
        
        t = t.drop(columns=["dt", "traj_id_local"]).copy()
        trajs.append(t.reset_index(drop=True))
    
    return trajs


def extract_trajectories(context: PipelineContext, n_jobs: int = None) -> PipelineContext:
    """
    Extract individual trajectories from AIS positions with parallel processing.
    """
    df = context.df
    Logger.info(f"Extracting trajectories (max gap: {CONFIG.max_gap_seconds}s, min points: {CONFIG.min_points_per_traj})...")
    
    if n_jobs is None:
        n_jobs = 16  # Reasonable default for this workload
    
    Logger.info(f"Using {n_jobs} parallel workers for extraction...")
    
    # Prepare data for parallel processing
    vessel_data_list = [(mmsi, group) for mmsi, group in df.groupby("mmsi")]
    
    # Parallel extraction
    with Pool(processes=n_jobs) as pool:
        results = pool.map(extract_trajectories_for_vessel, vessel_data_list)
    
    # Flatten results and assign trajectory IDs
    all_trajs = []
    traj_id = 0
    for vessel_trajs in results:
        for t in vessel_trajs:
            t["trajectory_id"] = traj_id
            all_trajs.append(t)
            traj_id += 1
    
    if all_trajs:
        df_result = pd.concat(all_trajs, ignore_index=True)
    else:
        df_result = pd.DataFrame(columns=list(df.columns) + ['trajectory_id'])
    
    Logger.info(f"Extracted {traj_id:,} trajectories, {len(df_result):,} points")
    context.df = df_result
    return context


def filter_short_trajectories(context: PipelineContext, min_points: int = None) -> PipelineContext:
    """
    Filter trajectories that are too short.
    """
    if min_points is None:
        min_points = CONFIG.min_points_per_traj
    
    df = context.df
    before_traj = df['trajectory_id'].nunique()
    before_points = len(df)
    
    # Count points per trajectory
    traj_counts = df.groupby('trajectory_id').size()
    valid_trajs = traj_counts[traj_counts >= min_points].index
    
    df = df[df['trajectory_id'].isin(valid_trajs)]
    
    after_traj = df['trajectory_id'].nunique()
    Logger.info(f"Filter trajectories: {after_traj:,}/{before_traj:,} kept, {len(df):,}/{before_points:,} points")
    
    context.df = df
    return context

def correct_speed_trajectory(traj_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix aberrant speeds for a single trajectory.
    """
    traj = traj_df.copy()
    sog = traj["sog"].values.copy()
    t = traj["base_date_time"].values
    
    for i in range(1, len(traj) - 1):
        dt1 = (t[i] - t[i-1]) / np.timedelta64(1, "s")
        dt2 = (t[i+1] - t[i]) / np.timedelta64(1, "s")
        if dt1 <= 0 or dt2 <= 0:
            continue
        
        # If speed change too abrupt, interpolate
        if abs(sog[i] - sog[i-1]) > CONFIG.amax_knots * dt1:
            sog[i] = (dt1 * sog[i-1] + dt2 * sog[i+1]) / (dt1 + dt2)
    
    traj["sog"] = sog
    return traj


def correct_speed(context: PipelineContext) -> PipelineContext:
    """
    Apply speed correction to all trajectories.
    """
    df = context.df
    Logger.info(f"Speed correction (amax: {CONFIG.amax_knots} kn/s)...")
    
    corrected_trajs = []
    for traj_id in df['trajectory_id'].unique():
        traj = df[df['trajectory_id'] == traj_id].copy()
        traj = correct_speed_trajectory(traj)
        corrected_trajs.append(traj)
    
    context.df = pd.concat(corrected_trajs, ignore_index=True)
    Logger.info("Speed correction completed")
    return context

def correct_position_trajectory(traj_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix aberrant positions for a single trajectory.
    """
    traj = traj_df.copy()
    lat = traj["lat"].values.copy()
    lon = traj["lon"].values.copy()
    t = traj["base_date_time"].values
    sog = traj["sog"].values
    
    # Use trajectory centroid as reference for local coordinate conversion
    lat0 = np.mean(lat)
    lon0 = np.mean(lon)
    
    # Convert to local metric coordinates
    x, y = latlon_to_local_meters(lon, lat, lon0, lat0)
    
    amax = CONFIG.amax_ms  # Max acceleration in m/s
    
    for i in range(1, len(traj) - 1):
        dt = (t[i] - t[i-1]) / np.timedelta64(1, "s")
        if dt <= 0:
            continue
        
        # Speed in m/s and max possible distance
        v = sog[i-1] * 0.514  # knots to m/s
        dmax = v * dt + 0.5 * amax * (dt ** 2)
        d = math.hypot(x[i] - x[i-1], y[i] - y[i-1])
        
        if d > dmax:
            # Also check next segment
            dt2 = (t[i+1] - t[i]) / np.timedelta64(1, "s")
            if dt2 <= 0:
                continue
            
            v2 = sog[i] * 0.514
            dmax2 = v2 * dt2 + 0.5 * amax * (dt2 ** 2)
            d2 = math.hypot(x[i+1] - x[i], y[i+1] - y[i])
            
            if d2 > dmax2:
                # Temporal interpolation
                alpha = (t[i] - t[i-1]) / (t[i+1] - t[i-1])
                x[i] = x[i-1] + alpha * (x[i+1] - x[i-1])
                y[i] = y[i-1] + alpha * (y[i+1] - y[i-1])
    
    # Convert back to lat/lon using same reference point
    lat_c, lon_c = local_meters_to_latlon(x, y, lon0, lat0)
    traj["lat"] = lat_c
    traj["lon"] = lon_c
    
    return traj


def correct_position(context: PipelineContext) -> PipelineContext:
    """
    Apply position correction to all trajectories.
    """
    df = context.df
    Logger.info("Position correction...")
    
    corrected_trajs = []
    for traj_id in df['trajectory_id'].unique():
        traj = df[df['trajectory_id'] == traj_id].copy()
        traj = correct_position_trajectory(traj)
        corrected_trajs.append(traj)
    
    context.df = pd.concat(corrected_trajs, ignore_index=True)
    Logger.info("Position correction completed")
    return context

def process_single_trajectory_correction(traj_data):
    """Process corrections for a single trajectory (for parallel execution)."""
    traj_id, traj = traj_data
    for _ in range(CONFIG.correction_iterations):
        traj = correct_speed_trajectory(traj)
        traj = correct_position_trajectory(traj)
    return traj


def apply_corrections(context: PipelineContext, n_jobs: int = None) -> PipelineContext:
    """
    Apply speed and position corrections iteratively with parallel processing.
    """
    Logger.info(f"Applying corrections ({CONFIG.correction_iterations} iterations)...")
    
    df = context.df
    total_trajs = df['trajectory_id'].nunique()
    
    if n_jobs is None:
        n_jobs = 16  # Reasonable default for this workload
    
    Logger.info(f"Using {n_jobs} parallel workers for corrections...")
    
    # Prepare trajectory data for parallel processing
    traj_data_list = [(traj_id, df[df['trajectory_id'] == traj_id].copy()) 
                      for traj_id in df['trajectory_id'].unique()]
    
    # Parallel processing
    with Pool(processes=n_jobs) as pool:
        corrected_trajs = pool.map(process_single_trajectory_correction, traj_data_list)
    
    context.df = pd.concat(corrected_trajs, ignore_index=True)
    Logger.info(f"Corrections completed: {total_trajs} trajectories processed")
    return context

def resample_trajectory(traj_df: pd.DataFrame) -> pd.DataFrame:
    """
    Resample a trajectory to 1 minute.
    """
    traj = traj_df.copy()
    
    # Keep only numeric columns for resampling (exclude mmsi, vessel_type, trajectory_id)
    numeric_cols = ["lat", "lon", "sog", "cog"]
    
    # Numeric conversion
    for col in numeric_cols:
        traj[col] = pd.to_numeric(traj[col], errors='coerce')
    
    # Keep only required columns for resampling
    traj_numeric = traj[["base_date_time"] + numeric_cols].copy()
    
    # Resampling and interpolation (only numeric columns)
    traj_numeric = traj_numeric.set_index("base_date_time").resample(CONFIG.resample_interval).mean()
    traj_numeric = traj_numeric.interpolate(method='linear')
    
    # Recalculate SOG from positions using local coordinates
    lat = traj_numeric["lat"].values
    lon = traj_numeric["lon"].values
    
    # Use trajectory centroid as reference
    lat0 = np.mean(lat)
    lon0 = np.mean(lon)
    
    x, y = latlon_to_local_meters(lon, lat, lon0, lat0)
    dist = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
    # SOG in knots: distance(m) / 60s / 0.514 (m/s per knot)
    traj_numeric["sog"] = np.insert(dist / 60 / 0.514, 0, traj_numeric["sog"].iloc[0])
    
    # COG: unwrap to avoid 359->1 jumps
    cog = np.unwrap(np.deg2rad(traj_numeric["cog"].values))
    traj_numeric["cog"] = np.rad2deg(cog) % 360
    
    return traj_numeric.reset_index()


def process_single_trajectory_resample(traj_data):
    """Process resampling for a single trajectory (for parallel execution)."""
    traj_id, traj = traj_data
    
    if len(traj) < 2:
        return None
    
    mmsi = traj['mmsi'].iloc[0]
    
    try:
        traj_resampled = resample_trajectory(traj)
        traj_resampled = traj_resampled.dropna()
        
        # Filter out points with aberrant SOG (> sog_max from config)
        # This handles cases where interpolation creates unrealistic speeds
        traj_resampled = traj_resampled[traj_resampled['sog'] <= CONFIG.sog_max]
        
        if len(traj_resampled) < CONFIG.min_points_per_traj:
            return None
        
        traj_resampled['mmsi'] = mmsi
        traj_resampled['trajectory_id'] = traj_id
        return traj_resampled
    except Exception:
        return None  # Skip problematic trajectories


def resample_trajectories(context: PipelineContext, n_jobs: int = None) -> PipelineContext:
    """
    Resample all trajectories with parallel processing.
    """
    df = context.df
    Logger.info(f"Resampling to {CONFIG.resample_interval}...")
    
    if n_jobs is None:
        n_jobs = 16  # Reasonable default for this workload
    
    Logger.info(f"Using {n_jobs} parallel workers for resampling...")
    
    total_trajs = df['trajectory_id'].nunique()
    
    # Prepare trajectory data for parallel processing
    traj_data_list = [(traj_id, df[df['trajectory_id'] == traj_id].copy()) 
                      for traj_id in df['trajectory_id'].unique()]
    
    # Parallel processing
    with Pool(processes=n_jobs) as pool:
        resampled_list = pool.map(process_single_trajectory_resample, traj_data_list)
    
    # Filter out None results
    resampled_list = [t for t in resampled_list if t is not None]
    
    if resampled_list:
        df_resampled = pd.concat(resampled_list, ignore_index=True)
    else:
        df_resampled = pd.DataFrame(columns=['base_date_time', 'lat', 'lon', 'sog', 'cog', 'mmsi', 'trajectory_id'])
    
    Logger.info(f"Resampling completed: {len(df_resampled):,} points, {df_resampled['trajectory_id'].nunique():,} trajectories")
    context.df = df_resampled
    return context

def assign_dataset_splits(context: PipelineContext, train_ratio: float = None, 
                          val_ratio: float = None, test_ratio: float = None) -> PipelineContext:
    """
    Assign each trajectory to a split (train/val/test).
    """
    if train_ratio is None:
        train_ratio = CONFIG.train_ratio
    if val_ratio is None:
        val_ratio = CONFIG.val_ratio
    if test_ratio is None:
        test_ratio = CONFIG.test_ratio
    
    df = context.df
    Logger.info(f"Assigning splits ({train_ratio}/{val_ratio}/{test_ratio})...")
    
    # Unique trajectory list
    trajectories = df['trajectory_id'].unique()
    n_traj = len(trajectories)
    
    # Deterministic shuffle
    np.random.seed(42)
    np.random.shuffle(trajectories)
    
    # Calculate split indices
    n_train = int(n_traj * train_ratio)
    n_val = int(n_traj * val_ratio)
    
    train_trajs = set(trajectories[:n_train])
    val_trajs = set(trajectories[n_train:n_train + n_val])
    
    # Assignment function
    def assign_split(traj_id):
        if traj_id in train_trajs:
            return 'train'
        elif traj_id in val_trajs:
            return 'val'
        else:
            return 'test'
    
    df['dataset_split'] = df['trajectory_id'].apply(assign_split)
    
    # Stats
    for split in ['train', 'val', 'test']:
        n = len(df[df['dataset_split'] == split])
        n_t = df[df['dataset_split'] == split]['trajectory_id'].nunique()
        Logger.info(f"  {split}: {n:,} points, {n_t:,} trajectories")
    
    context.df = df
    return context

def save_processed_to_db(context: PipelineContext, batch_size: int = 50000, 
                         truncate_first: bool = True) -> PipelineContext:
    """
    Save preprocessed data to trajectory_processed table.
    """
    df = context.df
    Logger.info(f"Saving {len(df):,} points to trajectory_processed...")
    
    # Prepare columns
    df_save = df[['trajectory_id', 'mmsi', 'base_date_time', 'lat', 'lon', 'sog', 'cog', 'dataset_split']].copy()
    
    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        
        # Truncate if requested
        if truncate_first:
            cur.execute("TRUNCATE TABLE trajectory_processed RESTART IDENTITY")
            Logger.info("Table trajectory_processed truncated")
        
        # Batch insertion with COPY
        total_rows = len(df_save)
        for start in range(0, total_rows, batch_size):
            end = min(start + batch_size, total_rows)
            chunk = df_save.iloc[start:end]
            
            csv_buffer = io.StringIO()
            chunk.to_csv(csv_buffer, index=False, header=False)
            csv_buffer.seek(0)
            
            copy_sql = """
                COPY trajectory_processed(trajectory_id, mmsi, base_date_time, lat, lon, sog, cog, dataset_split)
                FROM STDIN WITH (FORMAT CSV)
            """
            
            if hasattr(cur, "copy_expert"):
                cur.copy_expert(copy_sql, csv_buffer)
            else:
                with cur.copy(copy_sql) as copy:
                    copy.write(csv_buffer.getvalue())
            
            progress = 100 * end / total_rows
            Logger.info(f"  Batch {start:,}-{end:,} inserted ({progress:.1f}%)")
        
        conn.commit()
        Logger.success(f"Save completed: {total_rows:,} rows inserted")
        
    except Exception as e:
        conn.rollback()
        Logger.error(f"Error during save: {e}")
        raise
    finally:
        conn.close()
    
    return context

def run_preprocessing_pipeline(context: PipelineContext, limit: Optional[int] = None) -> PipelineContext:
    """
    Execute the complete preprocessing pipeline.
    """
    Logger.info("=" * 60)
    Logger.info("STARTING PREPROCESSING PIPELINE")
    Logger.info("=" * 60)
    
    # 1. Loading
    context = load_raw_data_from_db(context, limit=limit)
    
    # 2. Cleaning (as clean_ais from model_.ipynb)
    context = clean_ais_data(context)
    
    # 3. Trajectory extraction (as extract_trajectories from model_.ipynb)
    context = extract_trajectories(context)
    
    # 4. Iterative corrections: 3 passes of correct_speed + correct_position
    context = apply_corrections(context)
    
    # 5. Resampling to 1 minute (as resample from model_.ipynb)
    context = resample_trajectories(context)
    
    # 6. Split assignment (70/15/15)
    context = assign_dataset_splits(context)
    
    # 7. Save
    context = save_processed_to_db(context)
    
    Logger.info("=" * 60)
    Logger.info("PIPELINE COMPLETED")
    Logger.info("=" * 60)
    
    return context

def main():
    """Entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="AIS trajectory preprocessing for ML"
    )
    parser.add_argument(
        '--limit', 
        type=int, 
        default=None,
        help="Limit number of points to process (for testing)"
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help="Do not save to database (dry run)"
    )
    
    args = parser.parse_args()
    
    context = PipelineContext()
    
    if args.no_save:
        # Pipeline without save
        context = load_raw_data_from_db(context, limit=args.limit)
        context = clean_ais_data(context)
        context = extract_trajectories(context)
        context = apply_corrections(context)
        context = resample_trajectories(context)
        context = assign_dataset_splits(context)
        
        Logger.info("Dry run completed - no save")
        Logger.info(f"Result: {len(context.df):,} points, {context.df['trajectory_id'].nunique():,} trajectories")
    else:
        # Full pipeline
        context = run_preprocessing_pipeline(context, limit=args.limit)
    
    return context


if __name__ == "__main__":
    main()
