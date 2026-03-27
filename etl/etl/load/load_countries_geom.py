from etl.models.context import PipelineContext
from utils.logger import Logger
from utils.db import engine
from sqlalchemy import text

def update_country_geometries(context: PipelineContext) -> PipelineContext:
    df = context.df
    
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE TEMP TABLE tmp_country_geom (code VARCHAR(3), geom GEOMETRY)"))

            df.to_postgis(
                name="tmp_country_geom",
                con=conn,
                if_exists="replace",
                index=False,
                dtype={'geometry': 'Geometry'}
            )

            query = """
                UPDATE country
                SET geom = t.geometry
                FROM tmp_country_geom t
                WHERE country.code_alpha_3 = t.code_alpha_3;
            """
            result = conn.execute(text(query))
            
            Logger.success(f"Mise à jour réussie : {result.rowcount} pays ont maintenant une géométrie.")

    except Exception as e:
        Logger.error(f"Erreur lors de l'update des géométries : {e}")
        raise

    return context