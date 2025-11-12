CREATE TABLE IF NOT EXISTS mid (
    mid CHAR(3) PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    code_alpha_2 CHAR(2) NOT NULL,  -- ISO 3166 (alpha-2)
    code_alpha_3 CHAR(3) NULL  -- ISO 3166 (alpha-3)
);

ALTER TABLE vessel
    ADD COLUMN IF NOT EXISTS country VARCHAR(100) NULL;

CREATE OR REPLACE FUNCTION trg_set_country_from_mid()
RETURNS TRIGGER AS $$
DECLARE
    v_mid_code CHAR(3);
    v_country VARCHAR(100);
BEGIN
    IF NEW.mmsi IS NULL OR length(NEW.mmsi) <> 9 THEN
        NEW.country := NULL;

    ELSIF NEW.mmsi ~ '^[0-9]{9}$' THEN
        v_mid_code := SUBSTRING(NEW.mmsi FROM 1 FOR 3);

        SELECT country INTO v_country
        FROM mid
        WHERE mid = v_mid_code;

        IF FOUND THEN
            NEW.country := v_country;
        ELSE
            NEW.country := NULL;
        END IF;

    ELSE
        NEW.country := NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_country_from_mid ON vessel;

CREATE TRIGGER set_country_from_mid
BEFORE INSERT OR UPDATE OF mmsi ON vessel
FOR EACH ROW
EXECUTE FUNCTION trg_set_country_from_mid();
