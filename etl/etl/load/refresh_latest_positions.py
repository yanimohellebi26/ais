from sqlalchemy import text
from etl.models.context import PipelineContext
from utils.db import engine
from utils.logger import Logger

def refresh_latest_positions(context: PipelineContext, view_name: str = "latest_positions", concurrently: bool = True):
    """
    Refresh a materialized view outside a transaction so CONCURRENTLY works.
    """
    sql = f"REFRESH MATERIALIZED VIEW {'CONCURRENTLY ' if concurrently else ''}{view_name};"
    try:
        engine.dispose()
        
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connexion:
            connexion.execute(text(sql))

        Logger.info(f"Refreshed materialized view {view_name} (concurrently={concurrently})")
    except Exception as e:
        Logger.error(f"Error refreshing materialized view {view_name}: {e}")
        raise

    return context