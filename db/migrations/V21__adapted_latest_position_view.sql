CREATE INDEX IF NOT EXISTS idx_position_vessel_vid_time_desc
ON position_vessel(vessel_id, base_date_time DESC);

CREATE MATERIALIZED VIEW IF NOT EXISTS latest_positions AS
SELECT DISTINCT ON (vessel_id)
       id,
       vessel_id,
       base_date_time,
       sog,
       cog,
       heading,
       status_id,
       geom
FROM position_vessel
ORDER BY vessel_id, base_date_time DESC
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_latest_positions_vid ON latest_positions (vessel_id);
CREATE INDEX IF NOT EXISTS idx_latest_positions_geom ON latest_positions USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_latest_positions_time ON latest_positions (base_date_time DESC);