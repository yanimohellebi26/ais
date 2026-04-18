CREATE TABLE IF NOT EXISTS port_routes (
    id SERIAL PRIMARY KEY,
    route_date DATE NOT NULL,
    src_port_id INTEGER NOT NULL REFERENCES port(id),
    dest_port_id INTEGER NOT NULL REFERENCES port(id),
    ship_count INTEGER DEFAULT 0,
    avg_duration_minutes DOUBLE PRECISION,
    geom geography(LINESTRING, 4326)
);

CREATE INDEX IF NOT EXISTS idx_port_routes_date ON port_routes(route_date);
CREATE INDEX IF NOT EXISTS idx_port_routes_geom ON port_routes USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_port_routes_ports ON port_routes (src_port_id, dest_port_id);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_port_routes ON port_routes(route_date, src_port_id, dest_port_id);