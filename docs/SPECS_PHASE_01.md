# Spécifications Techniques - Phase 1 : Data Quality & Preprocessing

> **Objectif** : Nettoyer, valider et préparer les données AIS pour l'analyse
> **Durée estimée** : 2-3 semaines
> **Priorité** : ⭐⭐⭐ CRITIQUE

---

## 📋 Vue d'ensemble

Cette phase constitue la fondation du projet. Elle vise à garantir la qualité des données AIS avant toute analyse ou modélisation. Les données brutes AIS contiennent souvent des erreurs, des valeurs aberrantes et des gaps temporels qui peuvent fausser les analyses.

**Prérequis** :
- Base de données PostgreSQL + PostGIS opérationnelle
- Tables principales : `vessel`, `vessel_type`, `position_vessel`, `vessel_status`
- Accès Python avec bibliothèques : pandas, numpy, psycopg2, geopandas, scikit-learn

---

## 1.1 Nettoyage des Données GPS

### 1.1.1 Détection des positions GPS aberrantes

**Objectif** : Identifier et supprimer les positions avec coordonnées invalides

**Critères de validation** :
- Latitude : -90° ≤ lat ≤ 90°
- Longitude : -180° ≤ lon ≤ 180°
- Coordonnées (0, 0) → invalide (erreur de transmission)
- Coordonnées (null, null) → invalide

**Requête SQL d'identification** :
```sql
SELECT id, vessel_id, latitude, longitude, base_date_time
FROM position_vessel
WHERE latitude NOT BETWEEN -90 AND 90
   OR longitude NOT BETWEEN -180 AND 180
   OR (latitude = 0 AND longitude = 0)
   OR latitude IS NULL
   OR longitude IS NULL;
```

**Actions** :
- Compter le nombre de positions invalides
- Calculer le pourcentage par rapport au total
- Logger les positions supprimées dans une table `data_quality_log`
- Supprimer ou marquer comme `is_valid = false`

**Livrables** :
- Script Python : `data_cleaning/clean_gps_positions.py`
- Rapport : nombre de positions supprimées, distribution par navire
- Table : `data_quality_log` (id, table_name, row_id, issue_type, detected_at)

---

### 1.1.2 Détection des outliers de vitesse (SOG)

**Objectif** : Identifier les vitesses impossibles selon le type de navire

**Vitesses maximales par type** (en nœuds) :
| Type de navire | Code | Vitesse max |
|----------------|------|-------------|
| Cargo | 70-79 | 25 |
| Tanker | 80-89 | 20 |
| Passenger | 60-69 | 35 |
| Pleasure Craft | 37 | 40 |
| Fishing | 30 | 15 |
| Tug Tow | 52 | 15 |
| Default | - | 45 |

**Méthode de détection** :
1. Joindre `position_vessel` avec `vessel` et `vessel_type`
2. Appliquer seuils par groupe
3. Détecter valeurs négatives (SOG < 0)
4. Détecter valeurs nulles suspectes (navire en mouvement mais SOG = 0)

**Requête SQL** :
```sql
SELECT pv.id, pv.vessel_id, pv.sog, vt.vessel_group, pv.base_date_time
FROM position_vessel pv
JOIN vessel v ON pv.vessel_id = v.id
JOIN vessel_type vt ON v.vessel_type_id = vt.id
WHERE pv.sog < 0
   OR (vt.vessel_group = 'Cargo' AND pv.sog > 25)
   OR (vt.vessel_group = 'Tanker' AND pv.sog > 20)
   OR (vt.vessel_group = 'Passenger' AND pv.sog > 35)
   -- ... autres types
   OR pv.sog > 45; -- max global
```

**Stratégie de traitement** :
- **Option 1** : Suppression pure (positions aberrantes)
- **Option 2** : Interpolation depuis positions adjacentes (si gap < 10 min)
- **Option 3** : Marquage `is_outlier = true` (conservation pour analyse)

**Livrables** :
- Script : `data_cleaning/detect_speed_outliers.py`
- Fonction : `validate_sog(sog, vessel_type) -> bool`
- Rapport : distribution des outliers par type de navire

---

### 1.1.3 Validation des caps (COG & Heading)

**Objectif** : Normaliser et valider les caps de navigation

**Règles de validation** :
- COG (Course Over Ground) : 0° ≤ COG ≤ 360°
- Heading (cap magnétique) : 0° ≤ heading ≤ 360°
- Heading = 511 → non disponible (valeur standard AIS)

**Normalisation** :
```python
def normalize_heading(heading):
    if heading == 511:
        return None  # Non disponible
    if heading < 0 or heading > 360:
        return None  # Invalide
    return heading

def normalize_cog(cog):
    if cog < 0 or cog > 360:
        return cog % 360  # Normalisation circulaire
    return cog
```

**Requête SQL** :
```sql
UPDATE position_vessel
SET cog = cog % 360
WHERE cog > 360 OR cog < 0;

UPDATE position_vessel
SET heading = NULL
WHERE heading = 511 OR heading > 360 OR heading < 0;
```

**Livrables** :
- Script : `data_cleaning/normalize_headings.py`
- Mise à jour en place des données
- Rapport : nombre de normalisations effectuées

---

### 1.1.4 Détection des positions terrestres

**Objectif** : Identifier les navires sur terre (erreurs GPS ou ports mal définis)

**Méthode** :
1. Utiliser données géographiques (Natural Earth Data)
2. Requête spatiale PostGIS : `ST_Intersects` avec polygones terrestres
3. Exclure zones portuaires connues (buffer de 500m autour des ports)

**Requête PostGIS** :
```sql
SELECT pv.id, pv.vessel_id, pv.geom, pv.base_date_time
FROM position_vessel pv
WHERE ST_Intersects(
    pv.geom,
    (SELECT ST_Union(geom) FROM land_polygons)
)
AND NOT ST_DWithin(
    pv.geom::geography,
    (SELECT ST_Union(geom)::geography FROM ports),
    500  -- 500 mètres
);
```

**Prérequis** :
- Télécharger shapefile des terres : [Natural Earth](https://www.naturalearthdata.com/)
- Créer table `land_polygons` dans PostGIS
- Créer table `ports` avec positions des ports majeurs

**Livrables** :
- Script : `data_cleaning/detect_land_positions.py`
- Script : `data_import/import_land_polygons.sh`
- Table : `land_polygons` (geom GEOMETRY)
- Rapport : positions terrestres par navire

---

## 1.2 Gestion des Gaps Temporels

### 1.2.1 Identification des gaps AIS

**Objectif** : Détecter les périodes sans signal AIS par navire

**Définition d'un gap** :
- **Gap mineur** : 10 min < Δt < 1h
- **Gap modéré** : 1h < Δt < 4h
- **Gap majeur** : 4h < Δt < 24h
- **Gap critique** : Δt > 24h (désactivation probable de l'AIS)

**Requête SQL avec Window Functions** :
```sql
WITH position_with_lag AS (
    SELECT
        vessel_id,
        base_date_time,
        LAG(base_date_time) OVER (
            PARTITION BY vessel_id 
            ORDER BY base_date_time
        ) AS prev_time,
        latitude,
        longitude
    FROM position_vessel
    ORDER BY vessel_id, base_date_time
),
gaps AS (
    SELECT
        vessel_id,
        prev_time AS gap_start,
        base_date_time AS gap_end,
        EXTRACT(EPOCH FROM (base_date_time - prev_time)) / 3600 AS gap_hours
    FROM position_with_lag
    WHERE prev_time IS NOT NULL
      AND EXTRACT(EPOCH FROM (base_date_time - prev_time)) > 600  -- > 10 min
)
SELECT
    vessel_id,
    COUNT(*) AS gap_count,
    AVG(gap_hours) AS avg_gap_hours,
    MAX(gap_hours) AS max_gap_hours,
    SUM(gap_hours) AS total_gap_hours
FROM gaps
GROUP BY vessel_id
ORDER BY total_gap_hours DESC;
```

**Livrables** :
- Script : `data_analysis/detect_ais_gaps.py`
- Table : `ais_gaps` (vessel_id, gap_start, gap_end, gap_duration_seconds, gap_category)
- Vue matérialisée : `vessel_gap_statistics`
- Rapport : top 100 navires avec le plus de gaps

---

### 1.2.2 Statistiques des gaps

**Métriques à calculer** :

1. **Par navire** :
   - Nombre total de gaps
   - Durée totale en gap (heures)
   - Durée moyenne des gaps
   - Pourcentage du temps total en gap
   - Gap maximum observé

2. **Par type de navire** :
   - Distribution des gaps par vessel_group
   - Comparaison Cargo vs Fishing vs Passenger

3. **Temporelles** :
   - Gaps par heure de la journée (nuit vs jour)
   - Gaps par jour de la semaine
   - Gaps par mois (saisonnalité)

**Implémentation Python** :
```python
import pandas as pd
import psycopg2

def calculate_gap_statistics(conn):
    query = """
    SELECT 
        v.id AS vessel_id,
        v.mmsi,
        vt.vessel_group,
        COUNT(g.id) AS gap_count,
        AVG(g.gap_duration_seconds) / 3600 AS avg_gap_hours,
        MAX(g.gap_duration_seconds) / 3600 AS max_gap_hours,
        SUM(g.gap_duration_seconds) / 3600 AS total_gap_hours
    FROM vessel v
    LEFT JOIN ais_gaps g ON v.id = g.vessel_id
    LEFT JOIN vessel_type vt ON v.vessel_type_id = vt.id
    GROUP BY v.id, v.mmsi, vt.vessel_group
    """
    df = pd.read_sql(query, conn)
    return df

# Analyse par type
def gap_analysis_by_type(df):
    stats = df.groupby('vessel_group').agg({
        'gap_count': ['mean', 'median', 'max'],
        'avg_gap_hours': ['mean', 'median'],
        'total_gap_hours': 'sum'
    })
    return stats
```

**Livrables** :
- Script : `data_analysis/gap_statistics.py`
- Notebook Jupyter : `notebooks/gap_analysis.ipynb`
- Graphiques : histogrammes de distribution, boxplots par type
- CSV : `reports/gap_statistics_by_vessel.csv`

---

### 1.2.3 Détection de désactivations suspectes

**Objectif** : Identifier les navires qui désactivent intentionnellement leur AIS

**Critères suspects** :
1. Gap > 24h en pleine mer (loin des ports > 50 nm)
2. Réapparition à une position très éloignée (> 500 nm)
3. Pattern répétitif (> 3 gaps majeurs par mois)
4. Gap dans zone de pêche réglementée
5. Gap suivi d'un changement de cap radical (> 90°)

**Requête SQL avancée** :
```sql
WITH gaps_with_context AS (
    SELECT
        g.vessel_id,
        g.gap_start,
        g.gap_end,
        g.gap_duration_seconds / 3600 AS gap_hours,
        p1.latitude AS start_lat,
        p1.longitude AS start_lon,
        p2.latitude AS end_lat,
        p2.longitude AS end_lon,
        -- Distance parcourue pendant le gap (en nm)
        ST_Distance(p1.geom::geography, p2.geom::geography) / 1852 AS distance_nm,
        -- Distance au port le plus proche au début du gap
        (SELECT MIN(ST_Distance(p1.geom::geography, ports.geom::geography)) / 1852
         FROM ports) AS dist_to_port_nm
    FROM ais_gaps g
    JOIN position_vessel p1 ON g.vessel_id = p1.vessel_id AND g.gap_start = p1.base_date_time
    JOIN position_vessel p2 ON g.vessel_id = p2.vessel_id AND g.gap_end = p2.base_date_time
)
SELECT
    vessel_id,
    gap_start,
    gap_end,
    gap_hours,
    distance_nm,
    dist_to_port_nm,
    CASE
        WHEN gap_hours > 24 AND dist_to_port_nm > 50 THEN 'SUSPICIOUS_OFFSHORE'
        WHEN distance_nm > 500 THEN 'SUSPICIOUS_TELEPORT'
        WHEN gap_hours > 48 THEN 'SUSPICIOUS_LONG_DARK'
        ELSE 'NORMAL'
    END AS suspicion_level
FROM gaps_with_context
WHERE gap_hours > 4
ORDER BY gap_hours DESC;
```

**Scoring de suspicion** :
```python
def calculate_suspicion_score(gap_hours, distance_nm, dist_to_port_nm, gap_count_monthly):
    score = 0
    
    if gap_hours > 24 and dist_to_port_nm > 50:
        score += 40
    
    if distance_nm > 500:
        score += 30
    
    if gap_count_monthly > 3:
        score += 20
    
    if gap_hours > 48:
        score += 10
    
    return min(score, 100)  # Max 100
```

**Livrables** :
- Script : `detection/detect_suspicious_gaps.py`
- Table : `suspicious_gaps` (gap_id, vessel_id, suspicion_score, suspicion_reasons)
- Dashboard : alertes temps réel des gaps suspects
- Rapport mensuel : navires avec comportement suspect

---

### 1.2.4 Interpolation des gaps mineurs

**Objectif** : Combler les petits gaps (< 1h) par interpolation linéaire

**Méthode d'interpolation** :

1. **Interpolation spatiale** (lat/lon) :
```python
def interpolate_position(t, t1, t2, lat1, lon1, lat2, lon2):
    """
    Interpolation linéaire temporelle
    t : timestamp à interpoler
    t1, t2 : timestamps connus
    lat1, lon1 : position au temps t1
    lat2, lon2 : position au temps t2
    """
    alpha = (t - t1) / (t2 - t1)
    lat = lat1 + alpha * (lat2 - lat1)
    lon = lon1 + alpha * (lon2 - lon1)
    return lat, lon
```

2. **Interpolation de la vitesse (SOG)** :
```python
def interpolate_sog(t, t1, t2, sog1, sog2):
    alpha = (t - t1) / (t2 - t1)
    sog = sog1 + alpha * (sog2 - sog1)
    return sog
```

3. **Interpolation du cap (COG)** :
```python
def interpolate_cog_circular(t, t1, t2, cog1, cog2):
    """
    Interpolation circulaire pour angles
    Gère le passage 0°/360°
    """
    alpha = (t - t1) / (t2 - t1)
    
    # Différence angulaire minimale
    diff = (cog2 - cog1 + 180) % 360 - 180
    
    cog = (cog1 + alpha * diff) % 360
    return cog
```

**Stratégie d'interpolation** :
- Appliquer uniquement si gap < 60 minutes
- Générer positions à intervalle régulier (5 ou 10 minutes)
- Marquer positions interpolées : `is_interpolated = true`
- Ne pas interpoler si vitesse moyenne > vitesse max du type de navire

**Requête de génération** :
```sql
-- Créer série temporelle pour interpolation
WITH gaps_to_fill AS (
    SELECT
        vessel_id,
        gap_start,
        gap_end,
        EXTRACT(EPOCH FROM (gap_end - gap_start)) / 60 AS gap_minutes
    FROM ais_gaps
    WHERE gap_duration_seconds BETWEEN 600 AND 3600  -- 10 min à 1h
),
time_series AS (
    SELECT
        g.vessel_id,
        g.gap_start + (interval '5 minutes' * s.i) AS timestamp
    FROM gaps_to_fill g
    CROSS JOIN generate_series(1, (gap_minutes / 5)::int - 1) AS s(i)
)
-- Insérer positions interpolées
INSERT INTO position_vessel (
    vessel_id, base_date_time, latitude, longitude, sog, cog,
    is_interpolated, geom
)
SELECT
    ts.vessel_id,
    ts.timestamp,
    -- Interpolation lat/lon (requiert fonction PL/pgSQL)
    interpolate_lat(...),
    interpolate_lon(...),
    interpolate_sog(...),
    interpolate_cog(...),
    true,  -- is_interpolated
    ST_SetSRID(ST_MakePoint(interpolate_lon(...), interpolate_lat(...)), 4326)
FROM time_series ts;
```

**Livrables** :
- Script : `data_processing/interpolate_gaps.py`
- Fonctions PL/pgSQL : `interpolate_position()`, `interpolate_sog()`, `interpolate_cog()`
- Colonne : `position_vessel.is_interpolated BOOLEAN`
- Rapport : nombre de positions interpolées par navire

---

## 1.3 Feature Engineering de Base

### 1.3.1 Calcul des deltas temporels

**Objectif** : Calculer le temps écoulé entre chaque position successive

**Implémentation SQL** :
```sql
ALTER TABLE position_vessel ADD COLUMN delta_time_seconds INTEGER;

UPDATE position_vessel pv
SET delta_time_seconds = EXTRACT(EPOCH FROM (
    pv.base_date_time - LAG(pv.base_date_time) OVER (
        PARTITION BY vessel_id 
        ORDER BY base_date_time
    )
));
```

**Implémentation Python (plus efficace pour grands volumes)** :
```python
import pandas as pd
from sqlalchemy import create_engine

def calculate_delta_time():
    engine = create_engine('postgresql://user:pass@localhost/ais_db')
    
    # Charger par batch pour éviter surcharge mémoire
    chunk_size = 100000
    
    for vessel_id in get_all_vessel_ids():
        query = f"""
        SELECT id, vessel_id, base_date_time
        FROM position_vessel
        WHERE vessel_id = {vessel_id}
        ORDER BY base_date_time
        """
        df = pd.read_sql(query, engine)
        
        # Calcul delta
        df['delta_time_seconds'] = df['base_date_time'].diff().dt.total_seconds()
        
        # Mise à jour DB
        for idx, row in df.iterrows():
            if pd.notna(row['delta_time_seconds']):
                update_query = f"""
                UPDATE position_vessel
                SET delta_time_seconds = {row['delta_time_seconds']}
                WHERE id = {row['id']}
                """
                engine.execute(update_query)
```

**Livrables** :
- Script : `feature_engineering/calculate_delta_time.py`
- Colonne : `position_vessel.delta_time_seconds INTEGER`
- Index : `CREATE INDEX idx_delta_time ON position_vessel(delta_time_seconds)`

---

### 1.3.2 Calcul de la distance parcourue (Haversine)

**Objectif** : Calculer la distance géodésique entre positions successives

**Formule de Haversine** :
```python
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en kilomètres entre deux points GPS
    """
    R = 6371  # Rayon de la Terre en km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance_km = R * c
    return distance_km

def km_to_nautical_miles(km):
    return km * 0.539957
```

**Méthode PostGIS (plus efficace)** :
```sql
ALTER TABLE position_vessel ADD COLUMN distance_nm REAL;

UPDATE position_vessel pv
SET distance_nm = ST_Distance(
    pv.geom::geography,
    LAG(pv.geom::geography) OVER (
        PARTITION BY vessel_id 
        ORDER BY base_date_time
    )
) / 1852.0;  -- Conversion mètres vers nautical miles
```

**Optimisation par batch** :
```python
def calculate_distances_batch(vessel_ids, batch_size=1000):
    for vessel_id in vessel_ids:
        query = f"""
        WITH positions_with_lag AS (
            SELECT
                id,
                vessel_id,
                geom,
                LAG(geom) OVER (ORDER BY base_date_time) AS prev_geom
            FROM position_vessel
            WHERE vessel_id = {vessel_id}
        )
        UPDATE position_vessel pv
        SET distance_nm = ST_Distance(
            pwl.geom::geography,
            pwl.prev_geom::geography
        ) / 1852.0
        FROM positions_with_lag pwl
        WHERE pv.id = pwl.id
          AND pwl.prev_geom IS NOT NULL
        """
        execute_query(query)
```

**Livrables** :
- Script : `feature_engineering/calculate_distances.py`
- Colonne : `position_vessel.distance_nm REAL`
- Validation : comparer distance calculée vs distance SOG * delta_time

---

### 1.3.3 Calcul de la vitesse dérivée

**Objectif** : Calculer vitesse réelle depuis distance et temps (pour validation SOG)

**Formule** :
```
speed_derived (knots) = distance_nm / (delta_time_seconds / 3600)
```

**Implémentation SQL** :
```sql
ALTER TABLE position_vessel ADD COLUMN speed_derived_knots REAL;

UPDATE position_vessel
SET speed_derived_knots = CASE
    WHEN delta_time_seconds > 0 THEN
        distance_nm / (delta_time_seconds / 3600.0)
    ELSE NULL
END;
```

**Analyse de cohérence SOG vs Speed Derived** :
```sql
SELECT
    vessel_id,
    AVG(ABS(sog - speed_derived_knots)) AS avg_speed_diff,
    STDDEV(sog - speed_derived_knots) AS std_speed_diff,
    COUNT(*) AS position_count
FROM position_vessel
WHERE sog IS NOT NULL
  AND speed_derived_knots IS NOT NULL
  AND delta_time_seconds BETWEEN 60 AND 600  -- Entre 1 et 10 min
GROUP BY vessel_id
HAVING AVG(ABS(sog - speed_derived_knots)) > 2  -- Différence > 2 nœuds
ORDER BY avg_speed_diff DESC;
```

**Détection d'incohérences** :
- Si `|SOG - speed_derived| > 5 nœuds` → probable erreur de SOG
- Si différence systématique → problème de capteur AIS du navire

**Livrables** :
- Script : `feature_engineering/calculate_derived_speed.py`
- Colonne : `position_vessel.speed_derived_knots REAL`
- Rapport : navires avec incohérence SOG vs vitesse dérivée

---

### 1.3.4 Calcul de l'accélération

**Objectif** : Détecter accélérations/décélérations brusques

**Formule** :
```
acceleration (knots/hour) = (SOG₂ - SOG₁) / (Δt / 3600)
```

**Implémentation SQL** :
```sql
ALTER TABLE position_vessel ADD COLUMN acceleration_knots_per_hour REAL;

UPDATE position_vessel pv
SET acceleration_knots_per_hour = CASE
    WHEN delta_time_seconds > 0 THEN
        (pv.sog - LAG(pv.sog) OVER (
            PARTITION BY vessel_id 
            ORDER BY base_date_time
        )) / (delta_time_seconds / 3600.0)
    ELSE NULL
END;
```

**Détection d'événements** :
```sql
-- Accélérations brutales (> 10 nœuds/h)
SELECT vessel_id, base_date_time, sog, acceleration_knots_per_hour
FROM position_vessel
WHERE acceleration_knots_per_hour > 10
ORDER BY acceleration_knots_per_hour DESC;

-- Décélérations d'urgence (< -15 nœuds/h)
SELECT vessel_id, base_date_time, sog, acceleration_knots_per_hour
FROM position_vessel
WHERE acceleration_knots_per_hour < -15
ORDER BY acceleration_knots_per_hour ASC;
```

**Interprétation** :
- Accélération positive forte : départ du port, urgence
- Décélération forte : arrivée port, urgence, évitement collision

**Livrables** :
- Script : `feature_engineering/calculate_acceleration.py`
- Colonne : `position_vessel.acceleration_knots_per_hour REAL`
- Alertes : événements d'accélération anormale

---

### 1.3.5 Calcul du changement de cap (delta COG)

**Objectif** : Détecter virages et manœuvres

**Implémentation (gestion angle circulaire)** :
```python
def delta_cog_circular(cog1, cog2):
    """
    Calcule différence angulaire minimale
    Gère passage 0°/360°
    """
    diff = (cog2 - cog1 + 180) % 360 - 180
    return diff

# Exemple :
# COG₁ = 350°, COG₂ = 10°
# → delta_cog = 20° (et non 340°)
```

**Implémentation SQL** :
```sql
ALTER TABLE position_vessel ADD COLUMN delta_cog_degrees REAL;

CREATE OR REPLACE FUNCTION delta_angle_circular(angle1 REAL, angle2 REAL)
RETURNS REAL AS $$
BEGIN
    RETURN MOD((angle2 - angle1 + 180), 360) - 180;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

UPDATE position_vessel pv
SET delta_cog_degrees = delta_angle_circular(
    LAG(pv.cog) OVER (PARTITION BY vessel_id ORDER BY base_date_time),
    pv.cog
);
```

**Détection de virages** :
```sql
-- Virages serrés (> 45°)
SELECT vessel_id, base_date_time, cog, delta_cog_degrees
FROM position_vessel
WHERE ABS(delta_cog_degrees) > 45
ORDER BY ABS(delta_cog_degrees) DESC;

-- Manœuvres complexes (zigzag)
WITH consecutive_turns AS (
    SELECT
        vessel_id,
        base_date_time,
        delta_cog_degrees,
        LAG(delta_cog_degrees) OVER (
            PARTITION BY vessel_id 
            ORDER BY base_date_time
        ) AS prev_delta_cog
    FROM position_vessel
)
SELECT *
FROM consecutive_turns
WHERE ABS(delta_cog_degrees) > 30
  AND ABS(prev_delta_cog) > 30
  AND SIGN(delta_cog_degrees) != SIGN(prev_delta_cog);  -- Changement de sens
```

**Livrables** :
- Script : `feature_engineering/calculate_delta_cog.py`
- Fonction SQL : `delta_angle_circular()`
- Colonne : `position_vessel.delta_cog_degrees REAL`

---

### 1.3.6 Temps total en mer par navire

**Objectif** : Calculer la durée totale d'activité de chaque navire

**Méthode** :
```sql
CREATE MATERIALIZED VIEW vessel_activity_summary AS
SELECT
    vessel_id,
    MIN(base_date_time) AS first_seen,
    MAX(base_date_time) AS last_seen,
    EXTRACT(EPOCH FROM (MAX(base_date_time) - MIN(base_date_time))) / 3600 AS total_hours,
    COUNT(*) AS position_count,
    COUNT(*) FILTER (WHERE sog > 1) AS moving_count,
    SUM(distance_nm) AS total_distance_nm,
    AVG(sog) AS avg_sog
FROM position_vessel
GROUP BY vessel_id;

CREATE INDEX idx_vessel_activity ON vessel_activity_summary(vessel_id);
```

**Calcul temps effectif en mouvement** :
```sql
SELECT
    vessel_id,
    SUM(delta_time_seconds) FILTER (WHERE sog > 1) / 3600.0 AS hours_in_motion,
    SUM(delta_time_seconds) FILTER (WHERE sog <= 1) / 3600.0 AS hours_stationary,
    SUM(delta_time_seconds) / 3600.0 AS total_hours
FROM position_vessel
GROUP BY vessel_id;
```

**Livrables** :
- Vue : `vessel_activity_summary`
- Rapport CSV : temps en mer par navire et par type
- Graphique : distribution temps en mer par type de navire

---

### 1.3.7 Flag "navire en mouvement"

**Objectif** : Créer un indicateur binaire d'activité

**Critères** :
- `is_moving = true` si :
  - SOG > 1 nœud (seuil standard maritime)
  - OU distance_nm > 0.1 (position a changé significativement)
  - OU vessel_status IN (0, 7, 8) (underway)

**Implémentation** :
```sql
ALTER TABLE position_vessel ADD COLUMN is_moving BOOLEAN;

UPDATE position_vessel
SET is_moving = CASE
    WHEN sog > 1 THEN true
    WHEN distance_nm > 0.1 THEN true
    WHEN vessel_status_id IN (
        SELECT id FROM vessel_status WHERE code IN (0, 7, 8)
    ) THEN true
    ELSE false
END;

CREATE INDEX idx_is_moving ON position_vessel(is_moving);
```

**Applications** :
- Filtrer positions pour analyse de trajectoires (uniquement moving)
- Identifier périodes de mouillage
- Calculer ratio temps_en_mouvement / temps_total

**Livrables** :
- Script : `feature_engineering/flag_moving_vessels.py`
- Colonne : `position_vessel.is_moving BOOLEAN`
- Index pour performance des requêtes

---

## 1.4 Validation et Indexation

### 1.4.1 Vérification de l'intégrité référentielle

**Objectif** : S'assurer que toutes les clés étrangères sont valides

**Checks à effectuer** :
```sql
-- 1. Positions orphelines (vessel inexistant)
SELECT COUNT(*)
FROM position_vessel pv
LEFT JOIN vessel v ON pv.vessel_id = v.id
WHERE v.id IS NULL;

-- 2. Navires avec type invalide
SELECT COUNT(*)
FROM vessel v
LEFT JOIN vessel_type vt ON v.vessel_type_id = vt.id
WHERE vt.id IS NULL;

-- 3. Positions avec statut invalide
SELECT COUNT(*)
FROM position_vessel pv
WHERE pv.vessel_status_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM vessel_status vs WHERE vs.id = pv.vessel_status_id
  );

-- 4. user_vessel avec vessel inexistant
SELECT COUNT(*)
FROM user_vessel uv
LEFT JOIN vessel v ON uv.vessel_id = v.id
WHERE v.id IS NULL;
```

**Actions correctives** :
- Supprimer positions orphelines
- Attribuer type "Unknown" (99) aux navires sans type
- Mettre statut NULL si invalide
- Logger anomalies dans `data_quality_log`

**Livrables** :
- Script : `validation/check_referential_integrity.py`
- Rapport : anomalies d'intégrité détectées et corrigées

---

### 1.4.2 Optimisation des index PostGIS

**Objectif** : Accélérer les requêtes spatiales

**Index spatiaux GIST** :
```sql
-- Index principal sur la géométrie
CREATE INDEX IF NOT EXISTS idx_position_vessel_geom
ON position_vessel USING GIST (geom);

-- Index spatial avec filtre temporel (couverture partielle)
CREATE INDEX IF NOT EXISTS idx_position_vessel_geom_recent
ON position_vessel USING GIST (geom)
WHERE base_date_time > NOW() - INTERVAL '30 days';

-- Cluster la table pour localité spatiale
CLUSTER position_vessel USING idx_position_vessel_geom;
ANALYZE position_vessel;
```

**Vérification performance** :
```sql
EXPLAIN ANALYZE
SELECT COUNT(*)
FROM position_vessel
WHERE ST_DWithin(
    geom::geography,
    ST_SetSRID(ST_MakePoint(-122.4, 37.8), 4326)::geography,
    10000  -- 10 km
);
```

**Livrables** :
- Script : `database/optimize_spatial_indexes.sql`
- Rapport : temps d'exécution avant/après indexation

---

### 1.4.3 Index composite pour requêtes temporelles

**Objectif** : Optimiser requêtes par navire et période

**Index B-tree composites** :
```sql
-- Index principal : vessel + temps
CREATE INDEX IF NOT EXISTS idx_vessel_time
ON position_vessel (vessel_id, base_date_time DESC);

-- Index pour trajectoires
CREATE INDEX IF NOT EXISTS idx_vessel_time_moving
ON position_vessel (vessel_id, base_date_time)
WHERE is_moving = true;

-- Index pour analyse temporelle globale
CREATE INDEX IF NOT EXISTS idx_time_vessel
ON position_vessel (base_date_time, vessel_id);

-- Index partiel pour données récentes
CREATE INDEX IF NOT EXISTS idx_recent_positions
ON position_vessel (base_date_time DESC)
WHERE base_date_time > NOW() - INTERVAL '7 days';
```

**Test de performance** :
```sql
-- Requête de trajectoire typique
EXPLAIN ANALYZE
SELECT base_date_time, latitude, longitude, sog, cog
FROM position_vessel
WHERE vessel_id = 123456
  AND base_date_time BETWEEN '2024-01-01' AND '2024-01-31'
ORDER BY base_date_time;
```

**Livrables** :
- Script : `database/create_composite_indexes.sql`
- Documentation : guide d'utilisation des index

---

### 1.4.4 Index sur types de navires

**Objectif** : Accélérer filtres par catégorie

**Index** :
```sql
-- Sur la table vessel
CREATE INDEX IF NOT EXISTS idx_vessel_type
ON vessel (vessel_type_id);

-- Index composite vessel_type + dimensions
CREATE INDEX IF NOT EXISTS idx_vessel_type_dims
ON vessel (vessel_type_id, length, width);

-- Sur la table vessel_type
CREATE INDEX IF NOT EXISTS idx_vessel_type_group
ON vessel_type (vessel_group);

CREATE INDEX IF NOT EXISTS idx_vessel_type_code
ON vessel_type (type_code);
```

**Livrables** :
- Script : `database/create_vessel_type_indexes.sql`

---

### 1.4.5 Validation de la cohérence temporelle

**Objectif** : Garantir que les timestamps sont ordonnés correctement

**Checks** :
```sql
-- 1. Détecter timestamps futurs
SELECT vessel_id, base_date_time
FROM position_vessel
WHERE base_date_time > NOW()
ORDER BY base_date_time DESC;

-- 2. Détecter désordre temporel par navire
WITH ordered_positions AS (
    SELECT
        vessel_id,
        base_date_time,
        LAG(base_date_time) OVER (
            PARTITION BY vessel_id 
            ORDER BY base_date_time
        ) AS prev_time
    FROM position_vessel
)
SELECT vessel_id, COUNT(*) AS disorder_count
FROM ordered_positions
WHERE prev_time IS NOT NULL
  AND base_date_time < prev_time
GROUP BY vessel_id
HAVING COUNT(*) > 0;

-- 3. Détecter timestamps dupliqués
SELECT vessel_id, base_date_time, COUNT(*) AS duplicate_count
FROM position_vessel
GROUP BY vessel_id, base_date_time
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
```

**Corrections** :
```sql
-- Supprimer timestamps futurs
DELETE FROM position_vessel
WHERE base_date_time > NOW();

-- Supprimer doublons (garder le plus récent inserted)
DELETE FROM position_vessel a
USING position_vessel b
WHERE a.id < b.id
  AND a.vessel_id = b.vessel_id
  AND a.base_date_time = b.base_date_time;
```

**Contrainte d'intégrité** :
```sql
-- Ajouter contrainte unicité
ALTER TABLE position_vessel
ADD CONSTRAINT unique_vessel_time
UNIQUE (vessel_id, base_date_time);
```

**Livrables** :
- Script : `validation/check_temporal_consistency.py`
- Contraintes SQL appliquées
- Rapport : incohérences détectées et corrigées

---

## 📊 Livrables de la Phase 1

### Scripts Python
```
data_processing/
├── clean_gps_positions.py
├── detect_speed_outliers.py
├── normalize_headings.py
├── detect_land_positions.py
├── detect_ais_gaps.py
├── gap_statistics.py
├── interpolate_gaps.py
├── calculate_delta_time.py
├── calculate_distances.py
├── calculate_derived_speed.py
├── calculate_acceleration.py
├── calculate_delta_cog.py
├── flag_moving_vessels.py
└── run_all_preprocessing.py  # Script orchestrateur
```

### Scripts SQL
```
database/
├── migrations/
│   ├── V10__add_quality_columns.sql
│   ├── V11__create_indexes.sql
│   └── V12__create_views.sql
├── functions/
│   ├── interpolate_position.sql
│   ├── delta_angle_circular.sql
│   └── haversine_distance.sql
└── validation/
    ├── check_referential_integrity.sql
    └── check_temporal_consistency.sql
```

### Nouvelles Colonnes
```sql
ALTER TABLE position_vessel
ADD COLUMN delta_time_seconds INTEGER,
ADD COLUMN distance_nm REAL,
ADD COLUMN speed_derived_knots REAL,
ADD COLUMN acceleration_knots_per_hour REAL,
ADD COLUMN delta_cog_degrees REAL,
ADD COLUMN is_moving BOOLEAN,
ADD COLUMN is_interpolated BOOLEAN DEFAULT false,
ADD COLUMN is_outlier BOOLEAN DEFAULT false,
ADD COLUMN is_valid BOOLEAN DEFAULT true;
```

### Nouvelles Tables
```sql
-- Logs de qualité
CREATE TABLE data_quality_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    row_id INTEGER,
    issue_type VARCHAR(50),
    issue_description TEXT,
    detected_at TIMESTAMP DEFAULT NOW()
);

-- Gaps AIS
CREATE TABLE ais_gaps (
    id SERIAL PRIMARY KEY,
    vessel_id INTEGER REFERENCES vessel(id),
    gap_start TIMESTAMP,
    gap_end TIMESTAMP,
    gap_duration_seconds INTEGER,
    gap_category VARCHAR(20),  -- 'minor', 'moderate', 'major', 'critical'
    is_suspicious BOOLEAN DEFAULT false,
    suspicion_score INTEGER
);

-- Polygones terrestres
CREATE TABLE land_polygons (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    geom GEOMETRY(MULTIPOLYGON, 4326)
);

-- Ports
CREATE TABLE ports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    country VARCHAR(100),
    geom GEOMETRY(POINT, 4326),
    buffer_radius_m INTEGER DEFAULT 500
);
```

### Vues Matérialisées
```sql
-- Statistiques par navire
CREATE MATERIALIZED VIEW vessel_activity_summary AS
SELECT
    v.id AS vessel_id,
    v.mmsi,
    vt.vessel_group,
    MIN(pv.base_date_time) AS first_seen,
    MAX(pv.base_date_time) AS last_seen,
    COUNT(*) AS position_count,
    COUNT(*) FILTER (WHERE pv.is_moving) AS moving_count,
    SUM(pv.distance_nm) AS total_distance_nm,
    AVG(pv.sog) AS avg_sog,
    MAX(pv.sog) AS max_sog
FROM vessel v
JOIN vessel_type vt ON v.vessel_type_id = vt.id
LEFT JOIN position_vessel pv ON v.id = pv.vessel_id
GROUP BY v.id, v.mmsi, vt.vessel_group;

-- Statistiques de gaps
CREATE MATERIALIZED VIEW vessel_gap_statistics AS
SELECT
    vessel_id,
    COUNT(*) AS gap_count,
    AVG(gap_duration_seconds) / 3600 AS avg_gap_hours,
    MAX(gap_duration_seconds) / 3600 AS max_gap_hours,
    SUM(gap_duration_seconds) / 3600 AS total_gap_hours
FROM ais_gaps
GROUP BY vessel_id;
```

### Rapports
```
reports/
├── phase1_summary.md
├── data_quality_report.pdf
├── gap_analysis.html
├── outliers_by_vessel.csv
├── interpolated_positions_log.csv
└── performance_before_after.xlsx
```

### Notebooks Jupyter
```
notebooks/
├── phase1_exploratory_analysis.ipynb
├── gap_analysis_visualization.ipynb
├── speed_outliers_investigation.ipynb
└── data_quality_dashboard.ipynb
```

---

## ✅ Critères de Validation

**Phase 1 considérée terminée si** :

1. ✅ **Taux de positions valides > 95%**
   - Positions GPS valides
   - Vitesses cohérentes
   - Caps normalisés

2. ✅ **Gaps identifiés et traités**
   - 100% des gaps détectés
   - Gaps < 1h interpolés
   - Gaps suspects flaggés

3. ✅ **Features de base calculées**
   - delta_time, distance, vitesse dérivée
   - Accélération, delta COG
   - Flag is_moving

4. ✅ **Base de données optimisée**
   - Index créés et testés
   - Contraintes d'intégrité en place
   - Requêtes < 1s pour trajectoire standard

5. ✅ **Documentation complète**
   - Scripts documentés
   - Rapports de qualité générés
   - Notebooks exécutables

---

## 🔄 Pipeline d'Exécution

**Script orchestrateur** :
```python
# run_all_preprocessing.py

def run_phase1_preprocessing():
    steps = [
        ("1.1.1", clean_gps_positions),
        ("1.1.2", detect_speed_outliers),
        ("1.1.3", normalize_headings),
        ("1.1.4", detect_land_positions),
        ("1.2.1", detect_ais_gaps),
        ("1.2.2", calculate_gap_statistics),
        ("1.2.3", detect_suspicious_gaps),
        ("1.2.4", interpolate_minor_gaps),
        ("1.3.1", calculate_delta_time),
        ("1.3.2", calculate_distances),
        ("1.3.3", calculate_derived_speed),
        ("1.3.4", calculate_acceleration),
        ("1.3.5", calculate_delta_cog),
        ("1.3.6", calculate_time_at_sea),
        ("1.3.7", flag_moving_vessels),
        ("1.4.1", check_referential_integrity),
        ("1.4.2", optimize_spatial_indexes),
        ("1.4.3", create_composite_indexes),
        ("1.4.4", create_vessel_type_indexes),
        ("1.4.5", validate_temporal_consistency)
    ]
    
    for step_id, func in steps:
        print(f"Running step {step_id}: {func.__name__}")
        try:
            func()
            log_success(step_id)
        except Exception as e:
            log_error(step_id, str(e))
            raise
    
    print("Phase 1 completed successfully!")
    generate_summary_report()

if __name__ == "__main__":
    run_phase1_preprocessing()
```

---

## 📚 Ressources et Dépendances

**Bibliothèques Python** :
```
pandas>=2.0.0
numpy>=1.24.0
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
geopandas>=0.13.0
shapely>=2.0.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0
jupyter>=1.0.0
```

**Extensions PostgreSQL** :
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS btree_gist;
```

**Données externes** :
- Natural Earth Land Polygons : https://www.naturalearthdata.com/downloads/10m-physical-vectors/
- Liste des ports mondiaux : https://msi.nga.mil/Publications/WPI

---

**Fin de SPECS_PHASE_01.md**

---

> **Note** : Ce fichier est complet. Voulez-vous que je continue avec **SPECS_PHASE_02.md** (Analyse Spatiale) ?
