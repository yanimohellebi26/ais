CREATE OR REPLACE VIEW latest_positions AS
SELECT DISTINCT ON (vessel_id) *
FROM position_vessel
ORDER BY vessel_id, base_date_time DESC;