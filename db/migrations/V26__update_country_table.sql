ALTER TABLE country ADD COLUMN IF NOT EXISTS geom GEOMETRY(geometry, 4326);

CREATE INDEX IF NOT EXISTS idx_country_geom ON country USING GIST (geom);