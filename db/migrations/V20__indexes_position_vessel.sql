CREATE INDEX IF NOT EXISTS idx_position_vessel_geom 
ON position_vessel USING gist (geom);

CREATE INDEX IF NOT EXISTS idx_position_vessel_vid_time
ON position_vessel(vessel_id, base_date_time);