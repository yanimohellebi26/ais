-- TABLE TRAJECTOIRES PRÉTRAITÉES
-- Contient toutes les données nécessaires pour l'entraînement
CREATE TABLE IF NOT EXISTS trajectory_processed (
    id BIGSERIAL PRIMARY KEY,
    trajectory_id INTEGER NOT NULL,              -- ID unique de la trajectoire
    mmsi VARCHAR(9) NOT NULL,                    -- Identifiant du navire
    base_date_time TIMESTAMP NOT NULL,           -- Horodatage
    lat DOUBLE PRECISION NOT NULL,               -- Latitude corrigée
    lon DOUBLE PRECISION NOT NULL,               -- Longitude corrigée
    sog DOUBLE PRECISION NOT NULL,               -- Speed Over Ground (nœuds)
    cog DOUBLE PRECISION NOT NULL,               -- Course Over Ground (degrés)
    dataset_split VARCHAR(10) DEFAULT 'train'    -- train / val / test
        CHECK (dataset_split IN ('train', 'val', 'test'))
);

-- Index essentiels pour les requêtes d'entraînement
CREATE INDEX IF NOT EXISTS idx_traj_split ON trajectory_processed(dataset_split);
CREATE INDEX IF NOT EXISTS idx_traj_id_time ON trajectory_processed(trajectory_id, base_date_time);
CREATE INDEX IF NOT EXISTS idx_traj_mmsi ON trajectory_processed(mmsi);
