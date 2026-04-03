CREATE TABLE pa_infos (
    site_id        INTEGER PRIMARY KEY,
    name           VARCHAR(255),
    site_type      VARCHAR(10),
    iso3           VARCHAR(50),
    status         VARCHAR(50),
    status_yr      INTEGER
);

CREATE INDEX idx_pa_infos_iso3 ON pa_infos(iso3);
CREATE INDEX idx_pa_infos_status ON pa_infos(status);

CREATE TABLE protected_area (
    site_pid       VARCHAR(50) PRIMARY KEY,
    site_id        INTEGER NOT NULL,
    desig_eng      VARCHAR(255),
    desig_type     VARCHAR(50),
    iucn_cat       VARCHAR(50),
    realm          VARCHAR(50),
    no_take        VARCHAR(50),
    no_tk_area     DOUBLE PRECISION,
    rep_area       DOUBLE PRECISION,
    gis_area       DOUBLE PRECISION,
    rep_m_area     DOUBLE PRECISION,
    gis_m_area     DOUBLE PRECISION,
    own_type       VARCHAR(100),
    geometry       GEOMETRY(GEOMETRY, 4326) NOT NULL,

    CONSTRAINT fk_protected_area_site
        FOREIGN KEY (site_id)
        REFERENCES pa_infos(site_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_protected_area_geom ON protected_area USING GIST (geometry);
CREATE INDEX idx_protected_area_site_id ON protected_area(site_id);
CREATE INDEX idx_protected_area_realm ON protected_area(realm);
CREATE INDEX idx_protected_area_iucn_cat ON protected_area(iucn_cat);
CREATE INDEX idx_protected_area_desig_type ON protected_area(desig_type);