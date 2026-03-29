import os
import shutil
from etl.models.context import PipelineContext
from utils.logger import Logger

def transform_countries_raw(context: PipelineContext) -> PipelineContext:
    df = context.df

    Logger.info("Filtering countries data...")

    df = df.rename(columns={"ISO_A3_EH": "code_alpha_3"})

    context.df = df[["code_alpha_3", "geometry"]]
    
    Logger.success(f"Ready for updating {len(context.df)} geometries")
    return context

def cleanup_countries_files(context: PipelineContext) -> PipelineContext:
    path = "data/downloads/countries"

    Logger.info(f"Deleting temp folder {path} ...")

    try: 
        if os.path.exists(path):
            shutil.rmtree(path)
            Logger.success(f"Folder {path} deleted")

        else: 
            Logger.warning(f"Folder {path} not found")

    except Exception as e:
        Logger.error(f"Error cleaning : {e}")

    return context