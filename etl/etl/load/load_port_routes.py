from sqlalchemy import text
from etl.models.context import PipelineContext
from utils.db import engine
from utils.logger import Logger

def compute_port_routes(context: PipelineContext):
    query = """
        INSERT INTO port_routes (
            route_date,
            src_port_id,
            dest_port_id,
            ship_count,
            avg_duration_minutes,
            geom
        )
        SELECT 
            t.start_time::date AS route_date,
            p_start.id AS src_port_id,
            p_end.id AS dest_port_id,
            COUNT(DISTINCT t.vessel_id) AS ship_count,
            AVG(t.duration_minutes) AS avg_duration_minutes,
            ST_MakeLine(p_start.geom::geometry, p_end.geom::geometry)::geography AS geom
        FROM trajectories t
        JOIN port p_start ON ST_DWithin(t.start_point, p_start.geom, 2000)
        JOIN port p_end ON ST_DWithin(t.end_point, p_end.geom, 2000)
        WHERE p_start.id <> p_end.id
        GROUP BY 
            t.start_time::date, 
            p_start.id, 
            p_end.id
        ON CONFLICT (route_date, src_port_id, dest_port_id) 
        DO UPDATE SET
            ship_count = EXCLUDED.ship_count,
            avg_duration_minutes = EXCLUDED.avg_duration_minutes,
            geom = EXCLUDED.geom
    """

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            conn.commit() 
            Logger.info(f"Port routes updated: {result.rowcount} corridors added")
            
    except Exception as e:
        Logger.error(f"Error while computing port routes : {e}")
        raise

    return context