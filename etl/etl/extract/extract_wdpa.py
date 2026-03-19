import geopandas as gpd
import pandas as pd
from pathlib import Path

from etl.models.context import PipelineContext
from utils.logger import Logger


def extract_and_filter_wdpa(context: PipelineContext) -> PipelineContext:
    base_path = Path("data/downloads/WDPA_DATA")
    gdfs = []
    
    total_rows_before = 0
    total_rows_after = 0

    for sub in ["0", "1", "2"]:
        folder = base_path / sub

        poly_files = list(folder.glob("*polygons*.shp"))
        point_files = list(folder.glob("*points*.shp"))

        for shp in poly_files + point_files:
            Logger.info(f"Loading {shp.name}...")
            
            gdf = gpd.read_file(shp)
            rows_before = len(gdf)
            total_rows_before += rows_before
            
            if "REALM" in gdf.columns:
                gdf = gdf[gdf["REALM"].fillna("").str.contains("Marine|Coastal", case=False)]
            else:
                Logger.warning(f"Column REALM missing in {shp.name}. File ignored.")
                gdf = gdf.iloc[0:0]
                
            rows_after = len(gdf)
            total_rows_after += rows_after
            
            Logger.info(f" -> filtered : {rows_after:,} / {rows_before:,} kept.")

            if gdf.empty:
                continue

            if gdf.crs != "EPSG:4326":
                Logger.info(f" -> convert to EPSG:4326...")
                gdf = gdf.to_crs(4326)

            gdfs.append(gdf)

    if not gdfs:
        Logger.warning("no data for marine/coastal found in the shapefiles.")
        context.df = pd.DataFrame()
        return context

    Logger.info("Concat filtered batch...")
    gdf_final = pd.concat(gdfs, ignore_index=True)

    Logger.success(f"Extraction finished. {len(gdf_final):,} kept lines, {total_rows_before:,} total.")

    context.df = gdf_final
    return context

"""
def extract_wdpa_shapefiles(context: PipelineContext) -> PipelineContext:
    base_path = Path("/data/downloads/WDPA_DATA")

    gdfs = []

    for sub in ["0", "1", "2"]:
        folder = base_path / sub

        poly_files = list(folder.glob("*polygons*.shp"))
        point_files = list(folder.glob("*points*.shp"))

        for shp in poly_files + point_files:
            Logger.info(f"Loading {shp}")
            gdf = gpd.read_file(shp)
            rows_before = len(gdf)

            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs(4326)

            gdfs.append(gdf)

    if not gdfs:
        Logger.warning("No shapefiles found")
        context.df = pd.DataFrame()
        return context

    gdf_final = pd.concat(gdfs, ignore_index=True)

    Logger.info(f"Loaded {len(gdf_final):,} rows from WDPA")

    context.df = gdf_final
    return context
    """