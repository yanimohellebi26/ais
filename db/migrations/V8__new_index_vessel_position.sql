CREATE INDEX IF NOT EXISTS idx_position_vessel_mmsi_basedate_desc
    ON position_vessel(vessel_id, base_date_time DESC)
    INCLUDE (geom);