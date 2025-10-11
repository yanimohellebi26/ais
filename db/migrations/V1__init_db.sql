-- =========================================================
-- TABLES
-- =========================================================

CREATE TABLE IF NOT EXISTS vessel_type (
       id SERIAL PRIMARY KEY,
       description VARCHAR(100),
       vessel_group VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS vessel (
      id SERIAL PRIMARY KEY,
      mmsi VARCHAR(9) NOT NULL UNIQUE,
      imo VARCHAR(20),
      vessel_name VARCHAR(100),
      call_sign VARCHAR(20),
      vessel_type_id INT REFERENCES vessel_type(id),
      cargo_type_id INT REFERENCES vessel_type(id),
      length DOUBLE PRECISION,
      width DOUBLE PRECISION,
      draft DOUBLE PRECISION,
      transceiver_class VARCHAR(1),
      locked BOOLEAN default false,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      base_date_time TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vessel_type_id ON vessel(vessel_type_id);

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
