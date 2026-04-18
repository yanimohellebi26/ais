ALTER TABLE trajectories 
ADD COLUMN IF NOT EXISTS start_point geography(Point,4326),
ADD COLUMN IF NOT EXISTS end_point geography(Point,4326);

UPDATE trajectories
SET 
    start_point = ST_StartPoint(geom)::geography,
    end_point = ST_EndPoint(geom)::geography
WHERE start_point IS NULL;

CREATE INDEX IF NOT EXISTS idx_trajectories_start_point ON trajectories USING GIST (start_point);
CREATE INDEX IF NOT EXISTS idx_trajectories_end_point ON trajectories USING GIST (end_point);