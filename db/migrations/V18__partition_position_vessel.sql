DROP TABLE IF EXISTS position_vessel CASCADE;

CREATE TABLE position_vessel
(
    id             BIGSERIAL,
    vessel_id      INTEGER   NOT NULL REFERENCES vessel(id),
    base_date_time TIMESTAMP NOT NULL,
    sog            DOUBLE PRECISION,
    cog            DOUBLE PRECISION,
    heading        SMALLINT,
    status_id      INTEGER REFERENCES vessel_status(id),
    geom           geography(Point,4326) NOT NULL,
    PRIMARY KEY (id, base_date_time)
) PARTITION BY RANGE (base_date_time);
