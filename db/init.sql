CREATE TABLE IF NOT EXIST user {
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role_id SMALLINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP
};

CREATE TABLE IF NOT EXIST roles {
    id SERIAL PRIMARY KEY,
    name VARCHAR(20)
}

CREATE TABLE IF NOT EXIST user_vessel {
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES user(id),
    vessel_id INT NOT NULL REFERENCES vessel(id),
    created_at TIMESTAMP
}

CREATE TABLE IF NOT EXIST vessel{
    id SERIAL PRIMARY KEY,
    mmsi CHAR(9) NOT NULL,
    imo CHAR(7),
    vessel_name VARCHAR(20),
    call_sign VARCHAR(20),
    vessel_type_id  SMALLINT REFERENCES vessel_type(id),
    cargo_type_id SMALLINT REFERENCES vessel_type(id),
    length NUMERIC(6,2),
    width NUMERIC(6.2),
    draft NUMERIC(4,2),
    --transceiver_class TRANSCEIVER_CLASS
    created_at timestamp
}

CREATE TABLE IF NOT EXIST vessel_type{
    id SMALLINT PRIMARY KEY,
    description VARCHAR(100),
    vessel_group VARCHAR(20)
}

CREATE TABLE IF NOT EXIST position_vessel{
    id BIGSERIAL PRIMARY KEY,
    vessel_id INT NOT NULL REFERENCES vessel(id),
    base_date_time TIMESTAMP,
    sog NUMERIC(5,2),
    cog NUMERIC(5,2),
    heading SMALLINT,
    status_id SMALLINT REFERENCES status(id),
    geom geography(Point, 4326),
    inserted_at TIMESTAMP
}

CREATE TABLE IF NOT EXIST satus{
    id SMALLINT PRIMARY KEY,
    code SMALLINT NOT NULL,
    description VARCHAR(100)
}
