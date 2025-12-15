DROP VIEW latest_positions;

CREATE MATERIALIZED VIEW latest_positions AS
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
ORDER BY vessel_id, base_date_time DESC;

CREATE UNIQUE INDEX idx_latest_positions_vessel
    ON latest_positions (vessel_id);

CREATE INDEX idx_latest_positions_geom
    ON latest_positions
        USING GIST (geom);

