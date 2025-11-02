CREATE TABLE IF NOT EXISTS user_vessel (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    vessel_id INTEGER NOT NULL REFERENCES vessel(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to ensure one OWNER by vessel --
CREATE OR REPLACE FUNCTION check_single_owner_per_vessel()
    RETURNS TRIGGER AS $$
BEGIN
    -- Check if user role is OWNER
    IF (SELECT name FROM role r JOIN users u ON u.role_id = r.id WHERE u.id = NEW.user_id) = 'OWNER' THEN
        -- Check if already an OWNER for this ship
        IF EXISTS (
            SELECT 1
            FROM user_vessel uv
                     JOIN users u2 ON uv.user_id = u2.id
                     JOIN role r2 ON u2.role_id = r2.id
            WHERE uv.vessel_id = NEW.vessel_id
              AND r2.name = 'OWNER'
        ) THEN
            RAISE EXCEPTION 'Each vessel can have only one OWNER';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_single_owner_per_vessel
    BEFORE INSERT OR UPDATE ON user_vessel
    FOR EACH ROW
EXECUTE FUNCTION check_single_owner_per_vessel();
