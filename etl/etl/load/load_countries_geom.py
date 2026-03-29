from etl.models.context import PipelineContext
from utils.logger import Logger
from utils.db import engine
from sqlalchemy import text

def update_country_geometries(context: PipelineContext) -> PipelineContext:
    df = context.df
    
    if df.empty:
        Logger.warning("No file found.")
        return context

    try:
        Logger.info("Converting geometries to WKT and filtering...")
        df_update = df.copy()
        
        df_update = df_update[df_update["code_alpha_3"] != "-99"]
        df_update['wkt_geom'] = df_update['geometry'].apply(lambda g: g.wkt)
        df_to_upload = df_update[['code_alpha_3', 'wkt_geom']]

        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS tmp_country_geom"))
            conn.execute(text("""
                CREATE TEMP TABLE tmp_country_geom (
                    code_alpha_3 VARCHAR(3), 
                    wkt_text TEXT
                )
            """))

            df_to_upload.rename(columns={'wkt_geom': 'wkt_text'}).to_sql(
                name="tmp_country_geom",
                con=conn,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000
            )

            query = """
                UPDATE country
                SET geom = ST_GeomFromText(t.wkt_text, 4326)
                FROM tmp_country_geom t
                WHERE country.code_alpha_3 = t.code_alpha_3;
            """
            result = conn.execute(text(query))
            
            Logger.success(f"Update successful : {result.rowcount} updated countries.")

    except Exception as e:
        Logger.error(f"Error loading : {e}")
        raise

    return context