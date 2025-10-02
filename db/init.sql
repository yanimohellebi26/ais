-- =========================================================
-- TABLES
-- =========================================================

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
    mmsi VARCHAR(9) NOT NULL UNIQUE,
    imo VARCHAR(7),
    vessel_name VARCHAR(50),
    call_sign VARCHAR(20),
    vessel_type_id INT REFERENCES vessel_type(id),
    cargo_type_id INT REFERENCES cargo_type(id),
    length NUMERIC(6,2),
    width NUMERIC(6,2),
    draft NUMERIC(4,2),
    transceiver_class VARCHAR(20),
    locked BOOLEAN default false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_type_id ON vessel(vessel_type_id);

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

-- =========================================================
-- TRIGGER FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION update_last_update_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_update = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =========================================================
-- TRIGGERS AUTO FOR last_update
-- =========================================================

DO $$
DECLARE
    tbl RECORD;
BEGIN
    FOR tbl IN
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'last_update' AND table_schema = 'public'
    LOOP
        -- Supprime le trigger si déjà existant
        EXECUTE format('
            DROP TRIGGER IF EXISTS trg_%I_update ON %I;
            CREATE TRIGGER trg_%I_update
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_last_update_column();
        ', tbl.table_name, tbl.table_name, tbl.table_name, tbl.table_name);
    END LOOP;
END;
$$;
