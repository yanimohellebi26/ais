CREATE TABLE IF NOT EXISTS vessel_type (
    id SERIAL PRIMARY KEY,
    description VARCHAR(100),
    vessel_group VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS cargo_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS status (
    id SERIAL PRIMARY KEY,
    code SMALLINT NOT NULL,
    description VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS vessel (
    id SERIAL PRIMARY KEY,
    mmsi CHAR(9) NOT NULL UNIQUE,
    imo CHAR(7),
    vessel_name VARCHAR(50),
    call_sign VARCHAR(20),
    vessel_type_id INT REFERENCES vessel_type(id),
    cargo_type_id INT REFERENCES cargo_type(id),
    length NUMERIC(6,2),
    width NUMERIC(6,2),
    draft NUMERIC(4,2),
    transceiver_class VARCHAR(20),
    created_at TIMESTAMP
);
-- Index for JOIN on vessel and vessel_type
CREATE INDEX idx_vessel_type_id ON vessel(vessel_type_id);

CREATE TABLE IF NOT EXISTS position_vessel (
    id BIGSERIAL PRIMARY KEY,
    vessel_id INT NOT NULL REFERENCES vessel(id),
    base_date_time TIMESTAMP,
    sog NUMERIC(5,2),
    cog NUMERIC(5,2),
    heading SMALLINT,
    status_id INT REFERENCES status(id),
    geom geography(Point, 4326),
    inserted_at TIMESTAMP
);
