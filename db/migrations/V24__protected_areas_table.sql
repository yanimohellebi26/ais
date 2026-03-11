CREATE TYPE "desig_type" AS ENUM (
  'National',
  'International'
);

CREATE TYPE "iucn_cat" AS ENUM (
  'Ia',
  'Ib',
  'II',
  'III',
  'IV',
  'V',
  'VI',
  'Not Applicable',
  'Not Assigned',
  'Not Reported'
);

CREATE TYPE "realm" AS ENUM (
  'Terrestrial',
  'Coastal',
  'Marine'
);

CREATE TYPE "no_take" AS ENUM (
  'All',
  'Part',
  'None',
  'Not Applicable',
  'Not Reported'
);

CREATE TYPE "status" AS ENUM (
  'Proposed',
  'Inscribed',
  'Adopted',
  'Designated',
  'Established',
  'Not Reported'
);

CREATE TYPE "own_type" AS ENUM (
  'State',
  'Communal',
  'Individual Landowners',
  'For-profit organisations',
  'Non-profit organisations',
  'Joint ownership',
  'Multiple ownership',
  'Contested',
  'Not Reported'
);

CREATE TYPE "cons_obj" AS ENUM (
  'Primary',
  'Secondary',
  'Ancillary',
  'Not Applicable',
);

CREATE TYPE "verif" AS ENUM (
  'State Verified',
  'Expert Verified',
  'Not Reported'
);

CREATE TABLE protected_areas (
  SITE_ID integer PRIMARY KEY,
  NAME text,
  DESIG_ENG text,
  DESIG_TYPE desig_type,
  IUCN_CAT iucn_cat,
  REALM realm,
  REP_M_AREA double precision,
  GIS_M_AREA double precision,
  REP_AREA double precision,
  GIS_AREA double precision,
  NO_TAKE no_take,
  NO_TK_AREA double precision,
  STATUS status,
  STATUS_YR integer,
  CONS_OBJ cons_obj,
  ISO3 varchar(3),
  geometry geometry(Geometry, 4326) NOT NULL
);

CREATE TABLE pa_plot (
  SITE_PID text,
  SITE_ID integer,
  PRIMARY KEY (SITE_PID, SITE_ID),
  FOREIGN KEY (SITE_ID)
      REFERENCES protected_areas(SITE_ID)
      DEFERRABLE INITIALLY IMMEDIATE
);

CREATE INDEX idx_protected_areas_geom ON protected_areas USING GIST (geometry);

CREATE INDEX idx_protected_areas_iso3 ON protected_areas (ISO3);
CREATE INDEX idx_protected_areas_iucn ON protected_areas (IUCN_CAT);
CREATE INDEX idx_protected_areas_status ON protected_areas (STATUS);
CREATE INDEX idx_pa_plot_site ON pa_plot (SITE_ID);

ALTER TABLE protected_areas ADD CONSTRAINT enforce_valid_geom CHECK (ST_IsValid(geometry));