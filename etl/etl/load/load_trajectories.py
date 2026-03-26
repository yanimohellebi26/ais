from sqlalchemy import text
from etl.models.context import PipelineContext
from utils.db import engine
from utils.logger import Logger

def compute_trajectories_db(context: PipelineContext, **kwargs):
    """
    compute daily trajectories and add in base.
    min 5 point
    min 1 mille nautique
    mean => 45 noeuds
    duration > 5h
    """

    query = """
        WITH daily_positions AS (
            SELECT 
                vessel_id,
                DATE(base_date_time) as trajectory_day,
                MIN(base_date_time) as start_time,
                MAX(base_date_time) as end_time,
                COUNT(geom) as point_count,
                ST_MakeLine(geom::geometry ORDER BY base_date_time) as geom 
            FROM position_vessel
            GROUP BY vessel_id, DATE(base_date_time)
            HAVING count(geom) >= 5
        )
        INSERT INTO trajectories (
            id, vessel_id, start_time, end_time, 
            duration_minutes, point_count, distance_nm, avg_speed, geom
        )
        SELECT 
            gen_random_uuid(),
            vessel_id,
            start_time,
            end_time,
            EXTRACT(EPOCH FROM (end_time - start_time)) / 60.0 AS duration_minutes,
            point_count,
            ST_Length(geom::geography) / 1852.0 AS distance_nm,
            (ST_Length(geom::geography) / 1852.0) / NULLIF(EXTRACT(EPOCH FROM (end_time - start_time)) / 3600.0, 0) AS avg_speed,
            geom
        FROM daily_positions
        WHERE 
            (ST_Length(geom::geography) / 1852.0) > 1
            AND ((ST_Length(geom::geography) / 1852.0) / NULLIF(EXTRACT(EPOCH FROM (end_time - start_time)) / 3600.0, 0)) < 45
            AND (EXTRACT(EPOCH FROM (end_time - start_time)) / 60.0) > 300;
    """

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            conn.commit() 
            Logger.info(f"Batch insert {result.rowcount} trajectories added")
            
    except Exception as e:
        Logger.error(f"Error while computing trajectories : {e}")
        raise

    return context