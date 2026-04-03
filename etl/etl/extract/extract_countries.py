import os
import zipfile
import geopandas as gpd
from etl.models.context import PipelineContext
from utils.logger import Logger

def extract_countries_zip(context: PipelineContext) -> PipelineContext:
    zip_path = "data/downloads/" + context.file
    if not zip_path:
        raise ValueError("No file provided in context")
    
    extract_dir = "data/downloads/countries"
    
    Logger.info(f"Extracting {zip_path} to {extract_dir}/...")

    try:
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)
            
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        shp_file = next((f for f in os.listdir(extract_dir) if f.endswith('.shp')), None)
        
        if not shp_file:
            raise FileNotFoundError("No .shp file found.")

        shp_path = os.path.join(extract_dir, shp_file)
        Logger.info(f"Loading shapefile: {shp_path}")

        gdf = gpd.read_file(shp_path)

        context.df = gdf
        
        Logger.success(f"Extraction successful : {len(gdf)} loaded entities.")

    except Exception as e:
        Logger.error(f"Extraction error : {e}")
        raise

    return context