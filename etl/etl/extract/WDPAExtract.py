from pathlib import Path
import geopandas as gpd
from utils.logger import Logger
from etl.models.context import PipelineContext
from etl.transform.transform_general_wdpa import transform_wdpa
from etl.load.load_wdpa_db import load_wdpa_db

def _find_partition_dirs(base_dir: Path) -> list[Path]:
    """
    Find all the subfolders in the given base directory (0, 1, 2, etc.) and return their paths as a sorted list.
    Raise an error if no subfolder is found.
    """

    dirs = sorted(
        [folder for folder in base_dir.iterdir() if folder.is_dir() and folder.name.isdigit()],
        key=lambda folder: int(folder.name)
    )

    if not dirs:
        raise FileNotFoundError(f"No partition folders found in {base_dir}")
    
    return dirs

def _read_shp_from_partition(partition_dir: Path, shp_pattern: str) -> gpd.GeoDataFrame | None:
    """
    Read the .shp file matching the given pattern from the specified partition directory and return it as a GeoDataFrame.
    If no matching .shp file is found, return None.
    """

    matches = list(partition_dir.glob(shp_pattern))
    if not matches:
        Logger.warning(f"Partition {partition_dir.name} : no .shp file matching pattern '{shp_pattern}' found, ignored.")
        return None

    if len(matches) > 1:
        Logger.warning(f"Partition {partition_dir.name} : multiple .shp files matching pattern '{shp_pattern}' found, only the first one will be read : {matches[0].name}.")

    return gpd.read_file(matches[0])

def _process_partition(context: PipelineContext, shp_pattern: str, batch_size: int) -> PipelineContext:
    """
    Iterate over the partitions numbered from the WDPA_Data folder and do extract -> transform -> load for each of them.

    Args:
        context         : shared PipelineContext between steps
        shp_pattern     : glob pattern to focus polygons or points (ex: "*_polygons_*.shp" or "*_points_*.shp")
        batch_size      : number of features to insert in database at once during load step
    
    Returns: 
        context (cleared to None after transform)
    """

    base_dir = Path("data/downloads/WDPA_Data")
    partition_dirs = _find_partition_dirs(base_dir)

    Logger.info(f"extract_and_process_wdpa : {len(partition_dirs)} found partition(s) for '{shp_pattern}'")

    failed_partitions = []

    for partition_dir in partition_dirs:
        partition_name = partition_dir.name
        Logger.info(f"- Partition {partition_name}. -")

        try: 
            gdf = _read_shp_from_partition(partition_dir, shp_pattern)
            if gdf is None or gdf.empty:
                Logger.warning(f"Partition {partition_name} : empty or not valid file found, ignored.")
                continue

            Logger.info(f"Partition {partition_name} : {len(gdf):,} features read.")
            context.df = gdf

            context = transform_wdpa(context)

            context = load_wdpa_db(context, batch_size)

        except Exception as e:
            Logger.error(f"Partition {partition_name} : error during processing -> {e}")
            failed_partitions.append(partition_name)
            continue

        finally:
            context.df = None

    Logger.info(f"extract_and_process_wdpa completed : {len(partition_dirs) - len(failed_partitions)}/{len(partition_dirs)} partition(s) OK.")

    if failed_partitions:
        Logger.warning(f"Failed partitions : {failed_partitions}")

    return context

def load_wdpa_polygons(context: PipelineContext, batch_size: int = 10_000) -> PipelineContext:
    """
    Load WDPA polygons into database by iterating over the partitions and applying extract -> transform -> load steps.
    """

    return _process_partition(context, shp_pattern="*polygons*.shp", batch_size=batch_size)

def load_wdpa_points(context: PipelineContext, batch_size: int = 10_000) -> PipelineContext:
    """
    Load WDPA points into database by iterating over the partitions and applying extract -> transform -> load steps.
    """

    return _process_partition(context, shp_pattern="*points*.shp", batch_size=batch_size)