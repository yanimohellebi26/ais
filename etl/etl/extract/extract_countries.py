import os
import zipfile
import geopandas as gpd
from etl.models.context import PipelineContext
from utils.logger import Logger

def extract_countries_zip(context: PipelineContext) -> PipelineContext:
    zip_path = "data/downloads/countries.zip"
    extract_dir = "countries"
    
    Logger.info(f"Extracting {zip_path} to {extract_dir}/...")

    try:
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)
            
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        shp_file = next((f for f in os.listdir(extract_dir) if f.endswith('.shp')), None)
        
        if not shp_file:
            raise FileNotFoundError("Aucun fichier .shp trouvé dans le dossier dézippé.")

        shp_path = os.path.join(extract_dir, shp_file)
        Logger.info(f"Loading shapefile: {shp_path}")

        gdf = gpd.read_file(shp_path)

        context.df = gdf
        
        Logger.success(f"Extraction réussie : {len(gdf)} entités chargées.")

    except Exception as e:
        Logger.error(f"Erreur lors de l'extraction : {e}")
        raise

    return context