CREATE TABLE IF NOT EXISTS country (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code_alpha_2 VARCHAR(2),
    code_alpha_3 VARCHAR(3)
);

CREATE TABLE IF NOT EXISTS mid (
    mid INTEGER PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES country(id)
);

ALTER TABLE vessel
    ADD COLUMN IF NOT EXISTS mid_code INTEGER;

ALTER TABLE vessel
    ADD CONSTRAINT fk_vessel_mid
        FOREIGN KEY (mid_code)
        REFERENCES mid(mid);

CREATE OR REPLACE FUNCTION trg_set_mid_code_from_mmsi()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate MMSI format (must be 9 digits)
    IF NEW.mmsi IS NULL OR NEW.mmsi !~ '^[0-9]{9}$' THEN
        NEW.mid_code := NULL;
        RETURN NEW;
    END IF;

    -- Extract MID
    NEW.mid_code := SUBSTRING(NEW.mmsi FROM 1 FOR 3)::INTEGER;

    -- Check MID exists
    IF NOT EXISTS (SELECT 1 FROM mid WHERE mid = NEW.mid_code) THEN
        NEW.mid_code := NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_country_from_mid ON vessel;
DROP TRIGGER IF EXISTS set_mid_code_from_mmsi ON vessel;

CREATE TRIGGER set_mid_code_from_mmsi
BEFORE INSERT OR UPDATE OF mmsi
ON vessel
FOR EACH ROW
EXECUTE FUNCTION trg_set_mid_code_from_mmsi();
