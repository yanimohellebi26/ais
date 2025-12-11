CREATE TABLE IF NOT EXISTS vessel_status
(
  id SERIAL PRIMARY KEY,
  description VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS position_vessel
(
    id             BIGSERIAL PRIMARY KEY,
    vessel_id      INTEGER   NOT NULL REFERENCES vessel(id),
    base_date_time TIMESTAMP NOT NULL,
    sog            DOUBLE PRECISION,
    cog            DOUBLE PRECISION,
    heading        SMALLINT,
    status_id      INTEGER REFERENCES vessel_status(id),
    geom           geography(Point,4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_position_vessel_geom ON position_vessel USING gist (geom);
CREATE INDEX IF NOT EXISTS idx_position_vessel_vid_time
  ON position_vessel(vessel_id, base_date_time);


INSERT INTO vessel_status (id, description) VALUES
(0, 'Under way using engine'),
(1, 'At anchor'),
(2, 'Not under command'),
(3, 'Restricted manoeuverability'),
(4, 'Constrained by her draught'),
(5, 'Moored'),
(6, 'Aground'),
(7, 'Engaged in Fishing'),
(8, 'Under way sailing'),
(9, 'Reserved for future amendment of Navigational Status for HSC'),
(10, 'Reserved for future amendment of Navigational Status for WIG'),
(11, 'Reserved for future use'),
(12, 'Reserved for future use'),
(13, 'Reserved for future use'),
(14, 'AIS-SART is active'),
(15, 'Not defined (default)');
