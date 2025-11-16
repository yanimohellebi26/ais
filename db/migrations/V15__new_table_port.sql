CREATE TABLE IF NOT EXISTS port (
    id SERIAL PRIMARY KEY,
    code VARCHAR(5) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    geom geography(Point,4326) NOT NULL,
    country_code INTEGER NOT NULL REFERENCES country(id)
);
