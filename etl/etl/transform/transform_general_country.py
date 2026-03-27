import geopandas as gpd
from etl.models.context import PipelineContext
from utils.logger import Logger
from utils.db import engine
from sqlalchemy import text

def transform_countries_raw(context: PipelineContext) -> PipelineContext:
    df = context.df

    Logger.info("Filtering countries data...")

    df["geometry"] = df["geometry"].simplify(tolerance=0.001, preserve_topology=True).buffer(0)

    df = df.rename(columns={"ISO_A3_EH": "code_alpha_3"})

    context.df = df[["code_alpha_3", "geometry"]]
    
    Logger.success(f"Prêt pour la mise à jour de {len(context.df)} géométries")
    return context