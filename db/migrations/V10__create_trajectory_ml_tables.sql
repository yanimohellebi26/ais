-- =========================================================
-- V10: Tables pour trajectoires pré-processées ML
-- =========================================================

-- Table des segments de trajectoires nettoyés
CREATE TABLE IF NOT EXISTS trajectory_segment (
    id BIGSERIAL PRIMARY KEY,
    
    -- Identification
    vessel_id INTEGER NOT NULL REFERENCES vessel(id),
    segment_idx INTEGER NOT NULL,  -- Numéro du segment pour ce navire
    
    -- Métadonnées temporelles
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_seconds INTEGER NOT NULL,
    num_points INTEGER NOT NULL,
    
    -- Caractéristiques navire (dénormalisées)
    vessel_type_id INTEGER,
    
    -- Stats du segment (pour filtrage)
    avg_sog REAL,
    max_sog REAL,
    avg_delta_t REAL,  -- Intervalle moyen (secondes)
    max_delta_t REAL,  -- Gap max
    total_distance_m REAL,
    
    -- Bounding box
    min_lat REAL,
    max_lat REAL,
    min_lon REAL,
    max_lon REAL,
    
    -- Qualité (0-1)
    quality_score REAL DEFAULT 0,
    is_valid BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(vessel_id, segment_idx)
);

-- Table des points de trajectoire
CREATE TABLE IF NOT EXISTS trajectory_point (
    id BIGSERIAL PRIMARY KEY,
    segment_id BIGINT NOT NULL REFERENCES trajectory_segment(id) ON DELETE CASCADE,
    point_idx SMALLINT NOT NULL,  -- 0, 1, 2... ordre dans segment
    
    -- Position
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    
    -- Cinématique
    sog REAL NOT NULL,
    cog REAL NOT NULL,
    heading REAL,
    
    -- Temporel
    ts TIMESTAMP NOT NULL,
    delta_t REAL NOT NULL,  -- Secondes depuis point précédent
    
    -- Features pré-calculées
    accel REAL,      -- Changement SOG / delta_t
    turn_rate REAL,  -- Changement COG / delta_t (deg/s)
    
    UNIQUE(segment_id, point_idx)
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_seg_vessel ON trajectory_segment(vessel_id);
CREATE INDEX IF NOT EXISTS idx_seg_valid ON trajectory_segment(is_valid) WHERE is_valid = TRUE;
CREATE INDEX IF NOT EXISTS idx_seg_quality ON trajectory_segment(quality_score DESC) WHERE is_valid = TRUE;
CREATE INDEX IF NOT EXISTS idx_seg_vtype ON trajectory_segment(vessel_type_id);
CREATE INDEX IF NOT EXISTS idx_seg_numpts ON trajectory_segment(num_points) WHERE is_valid = TRUE;

CREATE INDEX IF NOT EXISTS idx_pt_segment ON trajectory_point(segment_id);
CREATE INDEX IF NOT EXISTS idx_pt_order ON trajectory_point(segment_id, point_idx);

-- Vue pour stats rapides
CREATE OR REPLACE VIEW trajectory_overview AS
SELECT 
    vessel_type_id,
    COUNT(*) as num_segments,
    SUM(num_points) as total_points,
    ROUND(AVG(num_points)::numeric, 1) as avg_points,
    ROUND(AVG(avg_sog)::numeric, 1) as avg_sog,
    ROUND(AVG(avg_delta_t)::numeric, 0) as avg_interval_s,
    ROUND(AVG(quality_score)::numeric, 2) as avg_quality
FROM trajectory_segment
WHERE is_valid = TRUE
GROUP BY vessel_type_id
ORDER BY total_points DESC;

COMMENT ON TABLE trajectory_segment IS 'Segments de trajectoires pré-processés pour ML';
COMMENT ON TABLE trajectory_point IS 'Points des segments, ordonnés temporellement';
