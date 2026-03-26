CREATE TABLE IF NOT EXISTS trajectories(
    id UUID DEFAULT gen_random_uuid(),
    vessel_id INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes DOUBLE PRECISION,
    point_count INT NOT NULL,
    distance_nm DOUBLE PRECISION,
    avg_speed DOUBLE PRECISION,
    geom geometry(LINESTRING, 4326),
    PRIMARY KEY (id, start_time) 
) PARTITION BY RANGE (start_time);

CREATE INDEX IF NOT EXISTS idx_trajectories_geom ON trajectories USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_trajectories_vid_time ON trajectories (vessel_id, start_time);

SELECT partman.create_parent(
    p_parent_table := 'public.trajectories',
    p_control := 'start_time',
    p_interval := '1 month',
    p_start_partition := '2015-01-01',
    p_premake := 24
);

SELECT partman.run_maintenance('public.trajectories');