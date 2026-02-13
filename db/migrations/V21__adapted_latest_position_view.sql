CREATE INDEX IF NOT EXISTS idx_position_vessel_vid_time_desc
ON position_vessel(vessel_id, base_date_time DESC);

CREATE OR REPLACE VIEW latest_positions AS
SELECT pv.*
FROM position_vessel pv
JOIN LATERAL (
    SELECT id
    FROM position_vessel
    WHERE vessel_id = pv.vessel_id 
    ORDER BY base_date_time DESC
    LIMIT 1
) AS last_pos ON last_pos.id = pv.id;