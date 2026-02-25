CREATE INDEX IF NOT EXISTS idx_position_vessel_vid_time_desc
ON position_vessel(vessel_id, base_date_time DESC);

CREATE MATERIALIZED VIEW IF NOT EXISTS latest_positions AS
SELECT pv.*
FROM position_vessel pv
JOIN (
    SELECT id, MAX(base_date_time) AS base_date_time
    FROM position_vessel
    GROUP BY id
) AS last_pos 
ON last_pos.id = pv.id
AND last_pos.base_date_time = pv.base_date_time
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_latest_positions_id ON latest_positions (id);
CREATE INDEX IF NOT EXISTS idx_latest_positions_vid ON latest_positions (vessel_id);
CREATE INDEX IF NOT EXISTS idx_latest_positions_geom ON latest_positions USING GIST (geom);