# Spécifications Techniques - Phase 2 : Analyse Spatiale

> **Objectif** : Analyser la distribution géographique du trafic maritime et identifier les zones clés
> **Durée estimée** : 2-3 semaines
> **Priorité** : ⭐⭐⭐ HAUTE

---

## 📋 Vue d'ensemble

Cette phase exploite les capacités spatiales de PostGIS pour analyser la distribution géographique des navires, identifier les zones de forte activité, calculer la proximité aux ports et extraire les trajectoires maritimes.

**Prérequis** :
- Phase 1 complétée (données nettoyées)
- PostGIS activé et index spatiaux créés
- Python avec geopandas, shapely, folium, scikit-learn
- Données géographiques : côtes, ports, zones maritimes

---

## 2.1 Zones Géographiques

### 2.1.1 Identification du bounding box global

**Objectif** : Déterminer l'étendue géographique complète des données AIS

**Requête PostGIS** :
```sql
-- Bounding box global
SELECT
    ST_XMin(ST_Extent(geom)) AS min_lon,
    ST_YMin(ST_Extent(geom)) AS min_lat,
    ST_XMax(ST_Extent(geom)) AS max_lon,
    ST_YMax(ST_Extent(geom)) AS max_lat,
    ST_Extent(geom) AS bbox
FROM position_vessel
WHERE is_valid = true;

-- Résultat exemple :
-- min_lon: -125.5, min_lat: 32.5, max_lon: -117.0, max_lat: 48.8
```

**Créer géométrie du bounding box** :
```sql
CREATE TABLE spatial_extent AS
SELECT
    ST_MakeEnvelope(
        ST_XMin(extent),
        ST_YMin(extent),
        ST_XMax(extent),
        ST_YMax(extent),
        4326
    ) AS geom,
    ST_Area(ST_MakeEnvelope(
        ST_XMin(extent),
        ST_YMin(extent),
        ST_XMax(extent),
        ST_YMax(extent),
        4326
    )::geography) / 1000000 AS area_km2
FROM (
    SELECT ST_Extent(geom) AS extent
    FROM position_vessel
) AS subquery;
```

**Visualisation Python** :
```python
import geopandas as gpd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

def plot_spatial_extent():
    engine = create_engine('postgresql://user:pass@localhost/ais_db')
    
    # Charger bounding box
    bbox = gpd.read_postgis(
        "SELECT geom FROM spatial_extent",
        engine,
        geom_col='geom'
    )
    
    # Charger échantillon de positions
    positions = gpd.read_postgis(
        """
        SELECT geom 
        FROM position_vessel 
        WHERE random() < 0.01  -- 1% échantillon
        LIMIT 10000
        """,
        engine,
        geom_col='geom'
    )
    
    fig, ax = plt.subplots(figsize=(15, 10))
    bbox.plot(ax=ax, color='none', edgecolor='red', linewidth=2)
    positions.plot(ax=ax, marker='o', markersize=1, alpha=0.3)
    plt.title("Spatial Extent of AIS Data")
    plt.savefig('reports/spatial_extent.png', dpi=300)
```

**Livrables** :
- Script : `spatial_analysis/calculate_extent.py`
- Table : `spatial_extent`
- Graphique : `reports/spatial_extent.png`
- Statistiques : area_km2, dimensions en degrés

---

### 2.1.2 Création de grille spatiale

**Objectif** : Diviser la zone d'étude en cellules régulières pour analyse de densité

**Grille rectangulaire (carrés)** :
```sql
-- Fonction pour créer grille
CREATE OR REPLACE FUNCTION create_spatial_grid(
    bbox geometry,
    cell_size_degrees float
) RETURNS TABLE(grid_id int, geom geometry) AS $$
BEGIN
    RETURN QUERY
    WITH bounds AS (
        SELECT
            ST_XMin(bbox) AS xmin,
            ST_YMin(bbox) AS ymin,
            ST_XMax(bbox) AS xmax,
            ST_YMax(bbox) AS ymax
    ),
    grid AS (
        SELECT
            row_number() OVER ()::int AS grid_id,
            ST_MakeEnvelope(
                x, y,
                x + cell_size_degrees,
                y + cell_size_degrees,
                4326
            ) AS geom
        FROM bounds,
             generate_series(xmin, xmax, cell_size_degrees) AS x,
             generate_series(ymin, ymax, cell_size_degrees) AS y
    )
    SELECT * FROM grid;
END;
$$ LANGUAGE plpgsql;

-- Créer grille 0.1° x 0.1° (~11km x 11km)
CREATE TABLE spatial_grid AS
SELECT grid_id, geom
FROM create_spatial_grid(
    (SELECT geom FROM spatial_extent),
    0.1
);

CREATE INDEX idx_spatial_grid_geom ON spatial_grid USING GIST (geom);
```

**Grille hexagonale (plus homogène)** :
```python
import h3
import geopandas as gpd
from shapely.geometry import Polygon

def create_h3_grid(bbox, resolution=7):
    """
    Crée grille hexagonale H3
    Resolution 7 : ~5.16 km² par hexagone
    Resolution 8 : ~0.74 km² par hexagone
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    
    hexagons = h3.polyfill_geojson({
        'type': 'Polygon',
        'coordinates': [[
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat]
        ]]
    }, resolution)
    
    polygons = []
    for h in hexagons:
        boundary = h3.h3_to_geo_boundary(h, geo_json=True)
        polygons.append({
            'hex_id': h,
            'geometry': Polygon(boundary)
        })
    
    gdf = gpd.GeoDataFrame(polygons, crs='EPSG:4326')
    return gdf

# Créer et sauvegarder
bbox = (-125.5, 32.5, -117.0, 48.8)
grid_h3 = create_h3_grid(bbox, resolution=7)
grid_h3.to_postgis('spatial_grid_h3', engine, if_exists='replace')
```

**Livrables** :
- Fonction SQL : `create_spatial_grid()`
- Table : `spatial_grid` (grille rectangulaire)
- Table : `spatial_grid_h3` (grille hexagonale H3)
- Script Python : `spatial_analysis/create_grid.py`

---

### 2.1.3 Calcul de densité de trafic par cellule

**Objectif** : Compter le nombre de positions AIS dans chaque cellule de la grille

**Requête d'agrégation spatiale** :
```sql
CREATE TABLE grid_traffic_density AS
SELECT
    g.grid_id,
    g.geom,
    COUNT(pv.id) AS position_count,
    COUNT(DISTINCT pv.vessel_id) AS unique_vessels,
    AVG(pv.sog) AS avg_sog,
    COUNT(*) FILTER (WHERE pv.is_moving) AS moving_count,
    COUNT(DISTINCT pv.vessel_id) FILTER (
        WHERE pv.is_moving
    ) AS unique_moving_vessels
FROM spatial_grid g
LEFT JOIN position_vessel pv ON ST_Intersects(g.geom, pv.geom)
WHERE pv.is_valid = true
GROUP BY g.grid_id, g.geom;

CREATE INDEX idx_grid_density ON grid_traffic_density(position_count DESC);
```

**Densité normalisée (positions par km²)** :
```sql
ALTER TABLE grid_traffic_density
ADD COLUMN area_km2 FLOAT,
ADD COLUMN density_per_km2 FLOAT;

UPDATE grid_traffic_density
SET area_km2 = ST_Area(geom::geography) / 1000000,
    density_per_km2 = position_count / (ST_Area(geom::geography) / 1000000);
```

**Heatmap avec Folium** :
```python
import folium
from folium.plugins import HeatMap
import pandas as pd

def create_traffic_heatmap():
    # Charger données de densité
    query = """
    SELECT
        ST_Y(ST_Centroid(geom)) AS lat,
        ST_X(ST_Centroid(geom)) AS lon,
        density_per_km2 AS weight
    FROM grid_traffic_density
    WHERE position_count > 0
    """
    df = pd.read_sql(query, engine)
    
    # Créer carte
    center_lat = df['lat'].mean()
    center_lon = df['lon'].mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='CartoDB positron'
    )
    
    # Ajouter heatmap
    heat_data = [[row['lat'], row['lon'], row['weight']] 
                 for idx, row in df.iterrows()]
    
    HeatMap(
        heat_data,
        min_opacity=0.3,
        radius=15,
        blur=20,
        max_zoom=13,
        gradient={
            0.0: 'blue',
            0.5: 'lime',
            0.7: 'yellow',
            1.0: 'red'
        }
    ).add_to(m)
    
    m.save('reports/traffic_heatmap.html')
    return m
```

**Livrables** :
- Table : `grid_traffic_density`
- Script : `spatial_analysis/calculate_density.py`
- Carte interactive : `reports/traffic_heatmap.html`
- Statistiques : top 20 cellules les plus denses

---

### 2.1.4 Identification des hotspots (zones de forte activité)

**Objectif** : Identifier statistiquement les zones anormalement denses

**Méthode : Percentile 95** :
```sql
-- Identifier cellules au-dessus du 95e percentile
CREATE TABLE traffic_hotspots AS
SELECT
    grid_id,
    geom,
    position_count,
    density_per_km2,
    unique_vessels
FROM grid_traffic_density
WHERE density_per_km2 > (
    SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY density_per_km2)
    FROM grid_traffic_density
    WHERE position_count > 0
)
ORDER BY density_per_km2 DESC;

-- Statistiques
SELECT
    COUNT(*) AS hotspot_count,
    AVG(density_per_km2) AS avg_density,
    SUM(position_count) AS total_positions,
    SUM(unique_vessels) AS total_unique_vessels
FROM traffic_hotspots;
```

**Méthode : DBSCAN clustering** :
```python
from sklearn.cluster import DBSCAN
import numpy as np

def identify_hotspots_dbscan():
    # Charger centres de cellules avec densité
    query = """
    SELECT
        ST_Y(ST_Centroid(geom)) AS lat,
        ST_X(ST_Centroid(geom)) AS lon,
        density_per_km2
    FROM grid_traffic_density
    WHERE position_count > 0
    """
    df = pd.read_sql(query, engine)
    
    # Pondérer par densité
    coords = df[['lat', 'lon']].values
    weights = df['density_per_km2'].values
    
    # Répéter points selon poids (normaliser)
    coords_weighted = np.repeat(
        coords,
        (weights / weights.min()).astype(int),
        axis=0
    )
    
    # DBSCAN clustering
    clustering = DBSCAN(
        eps=0.05,  # ~5.5 km
        min_samples=10
    ).fit(coords_weighted)
    
    df['cluster_id'] = clustering.labels_[:len(df)]
    
    # Identifier clusters = hotspots
    hotspots = df[df['cluster_id'] != -1].groupby('cluster_id').agg({
        'lat': 'mean',
        'lon': 'mean',
        'density_per_km2': 'sum'
    })
    
    return hotspots

# Sauvegarder
hotspots = identify_hotspots_dbscan()
hotspots.to_csv('reports/hotspots_dbscan.csv')
```

**Visualisation des hotspots** :
```python
def visualize_hotspots():
    hotspots_gdf = gpd.read_postgis(
        "SELECT * FROM traffic_hotspots",
        engine,
        geom_col='geom'
    )
    
    fig, ax = plt.subplots(figsize=(15, 12))
    
    # Fond : toutes les cellules
    all_cells = gpd.read_postgis(
        "SELECT geom, density_per_km2 FROM grid_traffic_density",
        engine,
        geom_col='geom'
    )
    all_cells.plot(
        ax=ax,
        column='density_per_km2',
        cmap='YlOrRd',
        alpha=0.3,
        legend=True
    )
    
    # Hotspots en surbrillance
    hotspots_gdf.plot(
        ax=ax,
        color='red',
        edgecolor='darkred',
        linewidth=2,
        alpha=0.6
    )
    
    plt.title("Traffic Hotspots (95th Percentile)")
    plt.savefig('reports/hotspots_map.png', dpi=300, bbox_inches='tight')
```

**Livrables** :
- Table : `traffic_hotspots`
- Script : `spatial_analysis/identify_hotspots.py`
- Carte : `reports/hotspots_map.png`
- CSV : `reports/hotspots_dbscan.csv`

---

### 2.1.5 Création de ROI (Regions of Interest)

**Objectif** : Définir des zones géographiques nommées pour analyses futures

**Exemples de ROI** :
```sql
CREATE TABLE regions_of_interest (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    category VARCHAR(50),  -- 'port_area', 'shipping_lane', 'fishing_zone', etc.
    geom GEOMETRY(POLYGON, 4326),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ROI manuelles (exemples)
INSERT INTO regions_of_interest (name, category, geom) VALUES
('San Francisco Bay Area', 'port_area', 
 ST_MakeEnvelope(-122.6, 37.5, -122.0, 38.0, 4326)),
('Puget Sound', 'port_area',
 ST_MakeEnvelope(-123.0, 47.0, -122.2, 48.5, 4326)),
('Coastal Fishing Zone North', 'fishing_zone',
 ST_MakeEnvelope(-125.0, 45.0, -124.0, 47.0, 4326));

CREATE INDEX idx_roi_geom ON regions_of_interest USING GIST (geom);
```

**ROI automatiques depuis hotspots** :
```sql
-- Créer ROI depuis agrégation de hotspots adjacents
INSERT INTO regions_of_interest (name, category, geom)
SELECT
    'Hotspot Cluster ' || cluster_id AS name,
    'high_traffic' AS category,
    ST_Union(geom) AS geom
FROM (
    SELECT
        grid_id,
        geom,
        ST_ClusterDBSCAN(geom, eps := 0.05, minpoints := 3) OVER () AS cluster_id
    FROM traffic_hotspots
) clustered
WHERE cluster_id IS NOT NULL
GROUP BY cluster_id;
```

**Analyse de trafic par ROI** :
```sql
CREATE MATERIALIZED VIEW roi_traffic_stats AS
SELECT
    roi.id AS roi_id,
    roi.name,
    roi.category,
    COUNT(pv.id) AS total_positions,
    COUNT(DISTINCT pv.vessel_id) AS unique_vessels,
    AVG(pv.sog) AS avg_speed,
    COUNT(DISTINCT DATE(pv.base_date_time)) AS active_days
FROM regions_of_interest roi
LEFT JOIN position_vessel pv ON ST_Intersects(roi.geom, pv.geom)
WHERE pv.is_valid = true
GROUP BY roi.id, roi.name, roi.category;

-- Rafraîchir la vue
REFRESH MATERIALIZED VIEW roi_traffic_stats;
```

**Livrables** :
- Table : `regions_of_interest`
- Vue : `roi_traffic_stats`
- Script : `spatial_analysis/create_roi.py`
- Carte interactive avec ROI délimitées

---

## 2.2 Proximité Portuaire

### 2.2.1 Définition des positions des ports

**Objectif** : Créer base de données des ports principaux

**Sources de données** :
- World Port Index (WPI) : https://msi.nga.mil/Publications/WPI
- OpenStreetMap (tag: harbour, port)
- Bases commerciales (MarineTraffic, etc.)

**Structure de table** :
```sql
CREATE TABLE ports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    country VARCHAR(100),
    port_code VARCHAR(10),  -- UNLOCODE
    latitude FLOAT,
    longitude FLOAT,
    geom GEOMETRY(POINT, 4326),
    port_size VARCHAR(20),  -- 'major', 'medium', 'small'
    max_vessel_size INTEGER,  -- en TEU ou DWT
    harbor_type VARCHAR(50),  -- 'seaport', 'river port', 'fishing'
    buffer_radius_m INTEGER DEFAULT 5000,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ports_geom ON ports USING GIST (geom);
```

**Import depuis CSV** :
```python
import pandas as pd

def import_ports_from_wpi(csv_path):
    df = pd.read_csv(csv_path)
    
    # Mapper colonnes WPI
    ports = df[[
        'Main Port Name',
        'Country',
        'World Port Index Number',
        'Latitude',
        'Longitude',
        'Harbor Size'
    ]].copy()
    
    ports.columns = ['name', 'country', 'port_code', 'latitude', 'longitude', 'port_size']
    
    # Créer géométrie
    from shapely.geometry import Point
    ports['geom'] = ports.apply(
        lambda row: Point(row['longitude'], row['latitude']), 
        axis=1
    )
    
    # Sauvegarder
    gdf = gpd.GeoDataFrame(ports, geometry='geom', crs='EPSG:4326')
    gdf.to_postgis('ports', engine, if_exists='replace', index=False)

import_ports_from_wpi('data/world_port_index.csv')
```

**Ports fictifs pour test** :
```sql
-- Exemple : Ports Californie
INSERT INTO ports (name, country, latitude, longitude, geom, port_size) VALUES
('Port of Los Angeles', 'USA', 33.7405, -118.2722, 
 ST_SetSRID(ST_MakePoint(-118.2722, 33.7405), 4326), 'major'),
('Port of Long Beach', 'USA', 33.7701, -118.1937,
 ST_SetSRID(ST_MakePoint(-118.1937, 33.7701), 4326), 'major'),
('Port of San Francisco', 'USA', 37.8024, -122.4058,
 ST_SetSRID(ST_MakePoint(-122.4058, 37.8024), 4326), 'medium'),
('Port of Oakland', 'USA', 37.7955, -122.2799,
 ST_SetSRID(ST_MakePoint(-122.2799, 37.7955), 4326), 'major'),
('Port of Seattle', 'USA', 47.5951, -122.3316,
 ST_SetSRID(ST_MakePoint(-122.3316, 47.5951), 4326), 'major');
```

**Livrables** :
- Table : `ports`
- Script : `data_import/import_ports.py`
- CSV source : `data/ports_database.csv`

---

### 2.2.2 Calcul de distance au port le plus proche

**Objectif** : Pour chaque position, calculer distance au port le plus proche

**Méthode optimisée (éviter N×M calculs)** :
```sql
-- Ajouter colonnes
ALTER TABLE position_vessel
ADD COLUMN nearest_port_id INTEGER,
ADD COLUMN distance_to_nearest_port_m FLOAT;

-- Mise à jour par batch (par zone géographique)
WITH nearest_ports AS (
    SELECT DISTINCT ON (pv.id)
        pv.id AS position_id,
        p.id AS port_id,
        ST_Distance(pv.geom::geography, p.geom::geography) AS distance_m
    FROM position_vessel pv
    CROSS JOIN LATERAL (
        SELECT id, geom
        FROM ports
        ORDER BY pv.geom <-> geom  -- KNN index
        LIMIT 5
    ) p
    ORDER BY pv.id, ST_Distance(pv.geom::geography, p.geom::geography)
)
UPDATE position_vessel pv
SET
    nearest_port_id = np.port_id,
    distance_to_nearest_port_m = np.distance_m
FROM nearest_ports np
WHERE pv.id = np.position_id;

-- Convertir en nautical miles
ALTER TABLE position_vessel ADD COLUMN distance_to_nearest_port_nm FLOAT;
UPDATE position_vessel SET distance_to_nearest_port_nm = distance_to_nearest_port_m / 1852.0;

CREATE INDEX idx_distance_to_port ON position_vessel(distance_to_nearest_port_nm);
```

**Version Python (plus flexible)** :
```python
from scipy.spatial import cKDTree
import numpy as np

def calculate_nearest_port_distances():
    # Charger ports
    ports = gpd.read_postgis("SELECT id, geom FROM ports", engine, geom_col='geom')
    port_coords = np.array([[p.y, p.x] for p in ports.geometry])
    
    # Construire KD-Tree
    tree = cKDTree(port_coords)
    
    # Traiter positions par batch
    batch_size = 100000
    offset = 0
    
    while True:
        query = f"""
        SELECT id, ST_Y(geom) AS lat, ST_X(geom) AS lon
        FROM position_vessel
        ORDER BY id
        LIMIT {batch_size} OFFSET {offset}
        """
        df = pd.read_sql(query, engine)
        
        if len(df) == 0:
            break
        
        # Calculer distances
        position_coords = df[['lat', 'lon']].values
        distances, indices = tree.query(position_coords)
        
        # Distances en mètres (approximation sphérique)
        distances_m = distances * 111320  # 1 degré ≈ 111.32 km
        
        # Mise à jour DB
        for i, row in df.iterrows():
            update_query = f"""
            UPDATE position_vessel
            SET nearest_port_id = {ports.iloc[indices[i]]['id']},
                distance_to_nearest_port_m = {distances_m[i]},
                distance_to_nearest_port_nm = {distances_m[i] / 1852.0}
            WHERE id = {row['id']}
            """
            engine.execute(update_query)
        
        offset += batch_size
        print(f"Processed {offset} positions...")
```

**Livrables** :
- Colonnes : `nearest_port_id`, `distance_to_nearest_port_nm`
- Script : `spatial_analysis/calculate_port_distances.py`
- Statistiques : distribution des distances au port

---

### 2.2.3 Identification des entrées/sorties de zones portuaires

**Objectif** : Détecter quand un navire entre ou sort d'une zone portuaire

**Définir zones portuaires (buffers)** :
```sql
CREATE TABLE port_zones AS
SELECT
    id AS port_id,
    name,
    ST_Buffer(geom::geography, buffer_radius_m)::geometry AS zone_geom
FROM ports;

CREATE INDEX idx_port_zones_geom ON port_zones USING GIST (zone_geom);
```

**Détecter transitions** :
```sql
CREATE TABLE port_events AS
WITH position_with_port AS (
    SELECT
        pv.id,
        pv.vessel_id,
        pv.base_date_time,
        pv.geom,
        pz.port_id,
        LAG(pz.port_id) OVER (
            PARTITION BY pv.vessel_id 
            ORDER BY pv.base_date_time
        ) AS prev_port_id
    FROM position_vessel pv
    LEFT JOIN port_zones pz ON ST_Intersects(pv.geom, pz.zone_geom)
    ORDER BY pv.vessel_id, pv.base_date_time
)
SELECT
    vessel_id,
    base_date_time AS event_time,
    port_id,
    CASE
        WHEN port_id IS NOT NULL AND prev_port_id IS NULL THEN 'ARRIVAL'
        WHEN port_id IS NULL AND prev_port_id IS NOT NULL THEN 'DEPARTURE'
        WHEN port_id IS NOT NULL AND port_id != prev_port_id THEN 'TRANSIT'
        ELSE NULL
    END AS event_type
FROM position_with_port
WHERE port_id IS NOT NULL OR prev_port_id IS NOT NULL;

-- Nettoyer NULL
DELETE FROM port_events WHERE event_type IS NULL;

CREATE INDEX idx_port_events_vessel ON port_events(vessel_id, event_time);
```

**Statistiques des événements** :
```sql
SELECT
    p.name AS port_name,
    pe.event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT pe.vessel_id) AS unique_vessels
FROM port_events pe
JOIN ports p ON pe.port_id = p.id
GROUP BY p.name, pe.event_type
ORDER BY event_count DESC;
```

**Livrables** :
- Table : `port_zones`
- Table : `port_events`
- Script : `spatial_analysis/detect_port_events.py`
- Rapport : statistiques d'entrées/sorties par port

---

### 2.2.4 Temps passé en zone portuaire par navire

**Objectif** : Calculer durée totale au port pour chaque navire

**Calcul des séjours portuaires** :
```sql
CREATE TABLE port_visits AS
WITH arrivals AS (
    SELECT
        vessel_id,
        port_id,
        event_time AS arrival_time,
        LEAD(event_time) OVER (
            PARTITION BY vessel_id, port_id 
            ORDER BY event_time
        ) AS next_event_time,
        LEAD(event_type) OVER (
            PARTITION BY vessel_id, port_id 
            ORDER BY event_time
        ) AS next_event_type
    FROM port_events
    WHERE event_type = 'ARRIVAL'
)
SELECT
    vessel_id,
    port_id,
    arrival_time,
    next_event_time AS departure_time,
    EXTRACT(EPOCH FROM (next_event_time - arrival_time)) / 3600 AS duration_hours
FROM arrivals
WHERE next_event_type = 'DEPARTURE'
  AND next_event_time IS NOT NULL;

CREATE INDEX idx_port_visits_vessel ON port_visits(vessel_id);
CREATE INDEX idx_port_visits_port ON port_visits(port_id);
```

**Statistiques par navire** :
```sql
CREATE MATERIALIZED VIEW vessel_port_statistics AS
SELECT
    v.id AS vessel_id,
    v.mmsi,
    vt.vessel_group,
    COUNT(pv.id) AS visit_count,
    SUM(pv.duration_hours) AS total_hours_in_port,
    AVG(pv.duration_hours) AS avg_visit_duration_hours,
    MIN(pv.duration_hours) AS min_visit_duration_hours,
    MAX(pv.duration_hours) AS max_visit_duration_hours
FROM vessel v
JOIN vessel_type vt ON v.vessel_type_id = vt.id
LEFT JOIN port_visits pv ON v.id = pv.vessel_id
GROUP BY v.id, v.mmsi, vt.vessel_group;
```

**Statistiques par port** :
```sql
CREATE MATERIALIZED VIEW port_activity_statistics AS
SELECT
    p.id AS port_id,
    p.name AS port_name,
    COUNT(pv.id) AS total_visits,
    COUNT(DISTINCT pv.vessel_id) AS unique_vessels,
    AVG(pv.duration_hours) AS avg_stay_duration_hours,
    SUM(pv.duration_hours) AS total_vessel_hours
FROM ports p
LEFT JOIN port_visits pv ON p.id = pv.port_id
GROUP BY p.id, p.name;
```

**Livrables** :
- Table : `port_visits`
- Vue : `vessel_port_statistics`
- Vue : `port_activity_statistics`
- Rapport : top navires par temps au port

---

### 2.2.5 Détection de navires à quai

**Objectif** : Identifier navires stationnaires en zone portuaire

**Critères** :
- Vitesse SOG < 0.5 nœud
- En zone portuaire (< 1 km du port)
- Durée > 30 minutes

**Requête de détection** :
```sql
CREATE TABLE vessels_at_berth AS
WITH stationary_in_port AS (
    SELECT
        pv.vessel_id,
        pv.base_date_time,
        pv.geom,
        pv.sog,
        p.id AS port_id,
        p.name AS port_name,
        ST_Distance(pv.geom::geography, p.geom::geography) AS distance_m
    FROM position_vessel pv
    CROSS JOIN LATERAL (
        SELECT id, name, geom
        FROM ports
        ORDER BY pv.geom <-> geom
        LIMIT 1
    ) p
    WHERE pv.sog < 0.5
      AND ST_DWithin(pv.geom::geography, p.geom::geography, 1000)  -- < 1 km
),
berth_periods AS (
    SELECT
        vessel_id,
        port_id,
        port_name,
        MIN(base_date_time) AS berth_start,
        MAX(base_date_time) AS berth_end,
        EXTRACT(EPOCH FROM (MAX(base_date_time) - MIN(base_date_time))) / 3600 AS duration_hours,
        AVG(ST_Y(geom)) AS avg_lat,
        AVG(ST_X(geom)) AS avg_lon
    FROM stationary_in_port
    GROUP BY vessel_id, port_id, port_name,
             -- Grouper périodes consécutives (gap < 30 min)
             (base_date_time - INTERVAL '30 minutes' * 
              (ROW_NUMBER() OVER (PARTITION BY vessel_id ORDER BY base_date_time)))
)
SELECT *
FROM berth_periods
WHERE duration_hours > 0.5;  -- Minimum 30 minutes

CREATE INDEX idx_berth_vessel ON vessels_at_berth(vessel_id);
CREATE INDEX idx_berth_port ON vessels_at_berth(port_id);
```

**Visualisation des navires à quai** :
```python
def visualize_vessels_at_berth(port_name):
    query = f"""
    SELECT
        v.mmsi,
        vt.vessel_group,
        vab.avg_lat,
        vab.avg_lon,
        vab.duration_hours
    FROM vessels_at_berth vab
    JOIN vessel v ON vab.vessel_id = v.id
    JOIN vessel_type vt ON v.vessel_type_id = vt.id
    WHERE vab.port_name = '{port_name}'
      AND vab.berth_end > NOW() - INTERVAL '24 hours'
    """
    df = pd.read_sql(query, engine)
    
    m = folium.Map(
        location=[df['avg_lat'].mean(), df['avg_lon'].mean()],
        zoom_start=13
    )
    
    for idx, row in df.iterrows():
        folium.CircleMarker(
            location=[row['avg_lat'], row['avg_lon']],
            radius=8,
            popup=f"MMSI: {row['mmsi']}<br>Type: {row['vessel_group']}<br>Duration: {row['duration_hours']:.1f}h",
            color='red',
            fill=True,
            fillColor='red'
        ).add_to(m)
    
    m.save(f'reports/berth_vessels_{port_name.replace(" ", "_")}.html')
```

**Livrables** :
- Table : `vessels_at_berth`
- Script : `spatial_analysis/detect_berth.py`
- Carte interactive par port : `reports/berth_vessels_{port}.html`

---

## 2.3 Analyse de Trajectoires

### 2.3.1 Extraction de trajectoires complètes par MMSI

**Objectif** : Construire LineString représentant le parcours de chaque navire

**Créer trajectoires géométriques** :
```sql
CREATE TABLE vessel_trajectories AS
SELECT
    vessel_id,
    COUNT(*) AS position_count,
    MIN(base_date_time) AS trajectory_start,
    MAX(base_date_time) AS trajectory_end,
    EXTRACT(EPOCH FROM (MAX(base_date_time) - MIN(base_date_time))) / 3600 AS duration_hours,
    ST_MakeLine(geom ORDER BY base_date_time) AS trajectory_geom
FROM position_vessel
WHERE is_valid = true
  AND is_moving = true
GROUP BY vessel_id
HAVING COUNT(*) >= 2;  -- Au moins 2 points

CREATE INDEX idx_trajectories_geom ON vessel_trajectories USING GIST (trajectory_geom);
CREATE INDEX idx_trajectories_vessel ON vessel_trajectories(vessel_id);
```

**Simplification des trajectoires (Douglas-Peucker)** :
```sql
-- Pour visualisation (réduire nombre de points)
ALTER TABLE vessel_trajectories ADD COLUMN trajectory_simplified GEOMETRY(LINESTRING, 4326);

UPDATE vessel_trajectories
SET trajectory_simplified = ST_Simplify(trajectory_geom, 0.001);  -- Tolérance 0.001°
```

**Export GeoJSON pour visualisation web** :
```python
def export_trajectories_geojson(vessel_ids=None, output_path='trajectories.geojson'):
    if vessel_ids:
        vessel_filter = f"AND vessel_id IN ({','.join(map(str, vessel_ids))})"
    else:
        vessel_filter = ""
    
    query = f"""
    SELECT
        vt.vessel_id,
        v.mmsi,
        vt.position_count,
        vt.trajectory_start,
        vt.trajectory_end,
        vt.duration_hours,
        ST_AsGeoJSON(vt.trajectory_simplified) AS geometry
    FROM vessel_trajectories vt
    JOIN vessel v ON vt.vessel_id = v.id
    WHERE 1=1 {vessel_filter}
    """
    
    df = pd.read_sql(query, engine)
    
    # Construire GeoJSON
    features = []
    for idx, row in df.iterrows():
        feature = {
            'type': 'Feature',
            'geometry': eval(row['geometry']),
            'properties': {
                'vessel_id': row['vessel_id'],
                'mmsi': row['mmsi'],
                'position_count': row['position_count'],
                'start': str(row['trajectory_start']),
                'end': str(row['trajectory_end']),
                'duration_hours': row['duration_hours']
            }
        }
        features.append(feature)
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    import json
    with open(output_path, 'w') as f:
        json.dump(geojson, f)
```

**Livrables** :
- Table : `vessel_trajectories`
- Script : `spatial_analysis/extract_trajectories.py`
- Export : `data/trajectories.geojson`

---

### 2.3.2 Calcul de la longueur totale des trajectoires

**Objectif** : Mesurer distance totale parcourue par chaque navire

**Calcul géodésique** :
```sql
ALTER TABLE vessel_trajectories
ADD COLUMN trajectory_length_km FLOAT,
ADD COLUMN trajectory_length_nm FLOAT;

UPDATE vessel_trajectories
SET
    trajectory_length_km = ST_Length(trajectory_geom::geography) / 1000,
    trajectory_length_nm = ST_Length(trajectory_geom::geography) / 1852;
```

**Statistiques par type de navire** :
```sql
SELECT
    vt.vessel_group,
    COUNT(DISTINCT tr.vessel_id) AS vessel_count,
    AVG(tr.trajectory_length_nm) AS avg_distance_nm,
    STDDEV(tr.trajectory_length_nm) AS std_distance_nm,
    MIN(tr.trajectory_length_nm) AS min_distance_nm,
    MAX(tr.trajectory_length_nm) AS max_distance_nm,
    SUM(tr.trajectory_length_nm) AS total_distance_nm
FROM vessel_trajectories tr
JOIN vessel v ON tr.vessel_id = v.id
JOIN vessel_type vt ON v.vessel_type_id = vt.id
GROUP BY vt.vessel_group
ORDER BY total_distance_nm DESC;
```

**Distribution graphique** :
```python
def plot_trajectory_length_distribution():
    query = """
    SELECT
        vt.vessel_group,
        tr.trajectory_length_nm
    FROM vessel_trajectories tr
    JOIN vessel v ON tr.vessel_id = v.id
    JOIN vessel_type vt ON v.vessel_type_id = vt.id
    WHERE tr.trajectory_length_nm > 0
    """
    df = pd.read_sql(query, engine)
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Histogramme
    df.groupby('vessel_group')['trajectory_length_nm'].plot(
        kind='hist',
        alpha=0.6,
        bins=50,
        ax=axes[0],
        legend=True
    )
    axes[0].set_xlabel('Trajectory Length (nm)')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('Distribution of Trajectory Lengths by Vessel Type')
    
    # Boxplot
    df.boxplot(column='trajectory_length_nm', by='vessel_group', ax=axes[1])
    axes[1].set_xlabel('Vessel Type')
    axes[1].set_ylabel('Trajectory Length (nm)')
    axes[1].set_title('Trajectory Length Comparison')
    
    plt.tight_layout()
    plt.savefig('reports/trajectory_length_distribution.png', dpi=300)
```

**Livrables** :
- Colonnes : `trajectory_length_km`, `trajectory_length_nm`
- Graphique : `reports/trajectory_length_distribution.png`
- CSV : `reports/trajectory_statistics_by_type.csv`

---

### 2.3.3 Identification des points de départ et d'arrivée

**Objectif** : Extraire premier et dernier point de chaque trajectoire

**Requête SQL** :
```sql
CREATE TABLE trajectory_endpoints AS
SELECT
    tr.vessel_id,
    v.mmsi,
    tr.trajectory_start,
    tr.trajectory_end,
    ST_StartPoint(tr.trajectory_geom) AS start_point,
    ST_EndPoint(tr.trajectory_geom) AS end_point,
    ST_Y(ST_StartPoint(tr.trajectory_geom)) AS start_lat,
    ST_X(ST_StartPoint(tr.trajectory_geom)) AS start_lon,
    ST_Y(ST_EndPoint(tr.trajectory_geom)) AS end_lat,
    ST_X(ST_EndPoint(tr.trajectory_geom)) AS end_lon,
    ST_Distance(
        ST_StartPoint(tr.trajectory_geom)::geography,
        ST_EndPoint(tr.trajectory_geom)::geography
    ) / 1852 AS start_end_distance_nm
FROM vessel_trajectories tr
JOIN vessel v ON tr.vessel_id = v.id;

CREATE INDEX idx_endpoints_start ON trajectory_endpoints USING GIST (start_point);
CREATE INDEX idx_endpoints_end ON trajectory_endpoints USING GIST (end_point);
```

**Identifier ports de départ/arrivée** :
```sql
ALTER TABLE trajectory_endpoints
ADD COLUMN departure_port_id INTEGER,
ADD COLUMN departure_port_name VARCHAR(200),
ADD COLUMN arrival_port_id INTEGER,
ADD COLUMN arrival_port_name VARCHAR(200);

-- Port de départ (port le plus proche du start_point)
UPDATE trajectory_endpoints te
SET
    departure_port_id = p.id,
    departure_port_name = p.name
FROM LATERAL (
    SELECT id, name
    FROM ports
    ORDER BY te.start_point <-> ports.geom
    LIMIT 1
) p
WHERE ST_DWithin(te.start_point::geography, 
                 (SELECT geom::geography FROM ports WHERE id = p.id),
                 10000);  -- < 10 km

-- Port d'arrivée
UPDATE trajectory_endpoints te
SET
    arrival_port_id = p.id,
    arrival_port_name = p.name
FROM LATERAL (
    SELECT id, name
    FROM ports
    ORDER BY te.end_point <-> ports.geom
    LIMIT 1
) p
WHERE ST_DWithin(te.end_point::geography,
                 (SELECT geom::geography FROM ports WHERE id = p.id),
                 10000);
```

**Routes portuaires les plus fréquentes** :
```sql
SELECT
    departure_port_name,
    arrival_port_name,
    COUNT(*) AS trip_count,
    AVG(start_end_distance_nm) AS avg_distance_nm
FROM trajectory_endpoints
WHERE departure_port_name IS NOT NULL
  AND arrival_port_name IS NOT NULL
  AND departure_port_name != arrival_port_name
GROUP BY departure_port_name, arrival_port_name
HAVING COUNT(*) >= 5
ORDER BY trip_count DESC
LIMIT 20;
```

**Livrables** :
- Table : `trajectory_endpoints`
- Requête : routes portuaires fréquentes
- Carte : origines/destinations par port

---

### 2.3.4 Détection de boucles et retours en arrière

**Objectif** : Identifier trajectoires non-linéaires (pêche, patrouille, recherche)

**Méthode : Self-intersection** :
```sql
CREATE TABLE trajectory_self_intersections AS
SELECT
    vessel_id,
    trajectory_geom,
    ST_IsSimple(trajectory_geom) AS is_simple,  -- false = self-intersects
    CASE
        WHEN ST_IsSimple(trajectory_geom) THEN 0
        ELSE ST_NumGeometries(ST_Node(trajectory_geom)) - ST_NumPoints(trajectory_geom) + 1
    END AS intersection_count
FROM vessel_trajectories;

-- Identifier navires avec boucles
SELECT
    v.mmsi,
    vt.vessel_group,
    tsi.intersection_count
FROM trajectory_self_intersections tsi
JOIN vessel v ON tsi.vessel_id = v.id
JOIN vessel_type vt ON v.vessel_type_id = vt.id
WHERE tsi.intersection_count > 0
ORDER BY tsi.intersection_count DESC;
```

**Méthode : Tortuosité (ratio longueur réelle / distance directe)** :
```sql
ALTER TABLE vessel_trajectories ADD COLUMN tortuosity FLOAT;

UPDATE vessel_trajectories
SET tortuosity = trajectory_length_km / NULLIF(
    ST_Distance(
        ST_StartPoint(trajectory_geom)::geography,
        ST_EndPoint(trajectory_geom)::geography
    ) / 1000,
    0
);

-- tortuosity = 1 : ligne droite parfaite
-- tortuosity > 2 : trajectoire très sinueuse
```

**Analyse par type** :
```sql
SELECT
    vt.vessel_group,
    AVG(tr.tortuosity) AS avg_tortuosity,
    STDDEV(tr.tortuosity) AS std_tortuosity,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tr.tortuosity) AS median_tortuosity
FROM vessel_trajectories tr
JOIN vessel v ON tr.vessel_id = v.id
JOIN vessel_type vt ON v.vessel_type_id = vt.id
WHERE tr.tortuosity IS NOT NULL
  AND tr.tortuosity < 100  -- Filtrer valeurs aberrantes
GROUP BY vt.vessel_group
ORDER BY avg_tortuosity DESC;
```

**Interprétation** :
- **Fishing vessels** : tortuosité élevée (5-15)
- **Cargo/Tanker** : tortuosité basse (1-2)
- **Tug/Tow** : tortuosité moyenne (2-4)

**Livrables** :
- Table : `trajectory_self_intersections`
- Colonne : `tortuosity`
- Graphique : tortuosité par type de navire

---

### 2.3.5 Calcul de la tortuosité des trajectoires

**Objectif** : Quantifier la sinuosité du parcours (déjà couvert en 2.3.4)

**Méthodes alternatives** :

**1. Sinuosity Index** :
```python
def calculate_sinuosity(trajectory_geom):
    """
    Sinuosity = longueur_réelle / distance_euclidienne
    """
    from shapely import wkb
    traj = wkb.loads(trajectory_geom)
    
    actual_length = traj.length
    straight_distance = traj.coords[0].distance(traj.coords[-1])
    
    if straight_distance == 0:
        return None
    
    sinuosity = actual_length / straight_distance
    return sinuosity
```

**2. Fractal Dimension** :
```python
from scipy.spatial.distance import pdist, squareform

def fractal_dimension_box_counting(coords, max_box_size=10, min_box_size=1):
    """
    Calcule dimension fractale (complexité de la trajectoire)
    """
    import numpy as np
    
    scales = np.logspace(np.log10(min_box_size), np.log10(max_box_size), num=10)
    counts = []
    
    for scale in scales:
        # Grille
        grid = {}
        for x, y in coords:
            grid_x = int(x / scale)
            grid_y = int(y / scale)
            grid[(grid_x, grid_y)] = True
        counts.append(len(grid))
    
    # Régression linéaire log-log
    coeffs = np.polyfit(np.log(scales), np.log(counts), 1)
    return -coeffs[0]  # Dimension fractale
```

**Livrables** :
- Fonction : `calculate_sinuosity()`
- Rapport : navires avec sinuosité anormale

---

## 📊 Livrables de la Phase 2

### Nouvelles Tables
```sql
-- Grilles spatiales
spatial_grid
spatial_grid_h3
grid_traffic_density
traffic_hotspots

-- ROI
regions_of_interest
roi_traffic_stats

-- Ports
ports
port_zones
port_events
port_visits
vessels_at_berth

-- Trajectoires
vessel_trajectories
trajectory_endpoints
trajectory_self_intersections
```

### Nouvelles Colonnes
```sql
ALTER TABLE position_vessel
ADD COLUMN nearest_port_id INTEGER,
ADD COLUMN distance_to_nearest_port_m FLOAT,
ADD COLUMN distance_to_nearest_port_nm FLOAT;

ALTER TABLE vessel_trajectories
ADD COLUMN trajectory_simplified GEOMETRY,
ADD COLUMN trajectory_length_km FLOAT,
ADD COLUMN trajectory_length_nm FLOAT,
ADD COLUMN tortuosity FLOAT;
```

### Scripts Python
```
spatial_analysis/
├── calculate_extent.py
├── create_grid.py
├── calculate_density.py
├── identify_hotspots.py
├── create_roi.py
├── calculate_port_distances.py
├── detect_port_events.py
├── detect_berth.py
├── extract_trajectories.py
└── analyze_tortuosity.py
```

### Visualisations
```
reports/
├── spatial_extent.png
├── traffic_heatmap.html
├── hotspots_map.png
├── berth_vessels_{port}.html
├── trajectory_length_distribution.png
└── tortuosity_by_type.png
```

### Vues Matérialisées
```sql
roi_traffic_stats
vessel_port_statistics
port_activity_statistics
```

---

## ✅ Critères de Validation

**Phase 2 considérée terminée si** :

1. ✅ **Grille spatiale créée**
   - Cellules couvrent 100% de la zone
   - Densité calculée pour chaque cellule

2. ✅ **Hotspots identifiés**
   - Au moins 10 zones de forte activité
   - Statistiques par hotspot calculées

3. ✅ **Ports intégrés**
   - Minimum 20 ports principaux référencés
   - Distance au port calculée pour toutes positions

4. ✅ **Événements portuaires détectés**
   - Entrées/sorties identifiées
   - Temps au port calculé par navire

5. ✅ **Trajectoires extraites**
   - LineString créées pour tous navires
   - Longueur et tortuosité calculées

---

## 🔄 Pipeline d'Exécution

```python
# run_phase2_spatial_analysis.py

def run_phase2():
    steps = [
        ("2.1.1", calculate_spatial_extent),
        ("2.1.2", create_spatial_grid),
        ("2.1.3", calculate_traffic_density),
        ("2.1.4", identify_hotspots),
        ("2.1.5", create_regions_of_interest),
        ("2.2.1", import_ports_database),
        ("2.2.2", calculate_port_distances),
        ("2.2.3", detect_port_events),
        ("2.2.4", calculate_port_time),
        ("2.2.5", detect_vessels_at_berth),
        ("2.3.1", extract_vessel_trajectories),
        ("2.3.2", calculate_trajectory_lengths),
        ("2.3.3", identify_trajectory_endpoints),
        ("2.3.4", detect_loops_and_intersections),
        ("2.3.5", calculate_tortuosity)
    ]
    
    for step_id, func in steps:
        print(f"Running step {step_id}: {func.__name__}")
        try:
            func()
            log_success(step_id)
        except Exception as e:
            log_error(step_id, str(e))
            raise
    
    print("Phase 2 completed!")
    generate_spatial_report()

if __name__ == "__main__":
    run_phase2()
```

---

**Fin de SPECS_PHASE_02.md**

> **Prochaine étape** : **SPECS_PHASE_03.md** (Analyse par Type de Navire) ?
