# Spécifications Techniques - Phase 4 : Extraction de Routes Maritimes

> **Objectif** : Identifier et extraire les routes maritimes principales par clustering spatial
> **Durée estimée** : 3 semaines
> **Priorité** : ⭐⭐⭐ HAUTE

---

## 📋 Vue d'ensemble

Cette phase utilise des algorithmes de clustering pour identifier les corridors de trafic maritime dense et extraire les routes commerciales principales. L'objectif est de créer une carte des "autoroutes maritimes" basée sur les données AIS réelles.

**Prérequis** :
- Phase 1, 2 et 3 complétées
- Positions nettoyées et validées
- Python avec scikit-learn, hdbscan, scipy

**Méthodes de clustering** :
- DBSCAN : simple, efficace pour formes arbitraires
- HDBSCAN : meilleur pour densités variables
- K-Means : pour segmentation uniforme
- Mean Shift : adaptatif

---

## 4.1 Clustering Spatial (DBSCAN/HDBSCAN)

### 4.1.1 Clustering global de toutes les positions

**Objectif** : Identifier zones de trafic dense sur l'ensemble des données

**Préparation des données** :
```python
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import geopandas as gpd

def load_positions_for_clustering(sample_size=None):
    """
    Charge positions pour clustering
    sample_size: nombre de positions (None = toutes)
    """
    if sample_size:
        query = f"""
        SELECT
            id,
            ST_Y(geom) AS latitude,
            ST_X(geom) AS longitude,
            sog,
            cog
        FROM position_vessel
        WHERE is_valid = true
          AND is_moving = true
        ORDER BY RANDOM()
        LIMIT {sample_size}
        """
    else:
        query = """
        SELECT
            id,
            ST_Y(geom) AS latitude,
            ST_X(geom) AS longitude,
            sog,
            cog
        FROM position_vessel
        WHERE is_valid = true
          AND is_moving = true
        """
    
    df = pd.read_sql(query, engine)
    print(f"Loaded {len(df):,} positions")
    return df

# Charger données
positions = load_positions_for_clustering(sample_size=1000000)  # 1M échantillon
```

**DBSCAN clustering** :
```python
def run_dbscan_clustering(df, eps_km=0.5, min_samples=50):
    """
    DBSCAN sur coordonnées géographiques
    eps_km: rayon en kilomètres
    min_samples: points minimum par cluster
    """
    # Convertir eps en degrés (approximation)
    # 1 degré ≈ 111 km
    eps_degrees = eps_km / 111.0
    
    # Extraire coordonnées
    coords = df[['latitude', 'longitude']].values
    
    # DBSCAN
    print(f"Running DBSCAN (eps={eps_km}km, min_samples={min_samples})...")
    clustering = DBSCAN(
        eps=eps_degrees,
        min_samples=min_samples,
        metric='haversine',  # Distance géodésique
        algorithm='ball_tree'
    )
    
    # Convertir en radians pour haversine
    coords_rad = np.radians(coords)
    labels = clustering.fit_predict(coords_rad)
    
    df['cluster_id'] = labels
    
    # Statistiques
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    
    print(f"Found {n_clusters} clusters")
    print(f"Noise points: {n_noise:,} ({n_noise/len(labels)*100:.1f}%)")
    
    return df, n_clusters

# Exécuter clustering
positions_clustered, n_clusters = run_dbscan_clustering(
    positions,
    eps_km=0.5,  # 500m rayon
    min_samples=50
)
```

**Sauvegarder résultats** :
```python
def save_clusters_to_db(df):
    """Sauvegarder clusters dans PostgreSQL"""
    
    # Créer table temporaire
    df_to_save = df[df['cluster_id'] != -1].copy()  # Exclure bruit
    
    # Grouper par cluster
    cluster_summary = df_to_save.groupby('cluster_id').agg({
        'id': 'count',
        'latitude': ['mean', 'std'],
        'longitude': ['mean', 'std'],
        'sog': 'mean'
    }).reset_index()
    
    cluster_summary.columns = [
        'cluster_id', 'position_count',
        'center_lat', 'std_lat',
        'center_lon', 'std_lon',
        'avg_sog'
    ]
    
    # Sauvegarder
    cluster_summary.to_sql(
        'traffic_clusters_global',
        engine,
        if_exists='replace',
        index=False
    )
    
    print(f"Saved {len(cluster_summary)} clusters to database")

save_clusters_to_db(positions_clustered)
```

**Visualisation clusters** :
```python
import folium
from folium.plugins import MarkerCluster

def visualize_clusters(df, max_clusters=100):
    """Carte interactive des clusters"""
    
    # Filtrer top clusters
    cluster_counts = df[df['cluster_id'] != -1]['cluster_id'].value_counts()
    top_clusters = cluster_counts.head(max_clusters).index.tolist()
    
    df_top = df[df['cluster_id'].isin(top_clusters)]
    
    # Créer carte
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='CartoDB positron'
    )
    
    # Couleurs par cluster
    import matplotlib.cm as cm
    colors = cm.get_cmap('tab20', len(top_clusters))
    
    for i, cluster_id in enumerate(top_clusters):
        cluster_data = df_top[df_top['cluster_id'] == cluster_id]
        
        color = colors(i)
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(color[0]*255), int(color[1]*255), int(color[2]*255)
        )
        
        # Échantillonner pour performance
        sample = cluster_data.sample(min(1000, len(cluster_data)))
        
        for _, row in sample.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=2,
                color=hex_color,
                fill=True,
                fillOpacity=0.6,
                popup=f"Cluster {cluster_id}"
            ).add_to(m)
    
    m.save('reports/traffic_clusters_map.html')
    print("Map saved to reports/traffic_clusters_map.html")

visualize_clusters(positions_clustered, max_clusters=50)
```

**Livrables** :
- Script : `clustering/dbscan_global.py`
- Table : `traffic_clusters_global`
- Carte : `reports/traffic_clusters_map.html`
- Rapport : statistiques de clustering

---

### 4.1.2 Clustering par type de navire

**Objectif** : Identifier routes spécifiques à chaque type

**Clustering séparé par type** :
```python
def cluster_by_vessel_type(vessel_group, eps_km=1.0, min_samples=30):
    """Clustering pour un type de navire spécifique"""
    
    query = f"""
    SELECT
        pv.id,
        ST_Y(pv.geom) AS latitude,
        ST_X(pv.geom) AS longitude,
        pv.sog,
        pv.cog
    FROM position_vessel pv
    JOIN vessel v ON pv.vessel_id = v.id
    JOIN vessel_type vt ON v.vessel_type_id = vt.id
    WHERE pv.is_valid = true
      AND pv.is_moving = true
      AND vt.vessel_group = '{vessel_group}'
    """
    
    df = pd.read_sql(query, engine)
    print(f"\n{vessel_group}: {len(df):,} positions")
    
    if len(df) < min_samples * 10:
        print(f"Not enough data for {vessel_group}")
        return None
    
    # DBSCAN
    coords_rad = np.radians(df[['latitude', 'longitude']].values)
    eps_degrees = eps_km / 111.0
    
    clustering = DBSCAN(
        eps=eps_degrees,
        min_samples=min_samples,
        metric='haversine',
        algorithm='ball_tree'
    )
    
    df['cluster_id'] = clustering.fit_predict(coords_rad)
    
    n_clusters = len(set(df['cluster_id'])) - (1 if -1 in df['cluster_id'].values else 0)
    print(f"  → {n_clusters} clusters found")
    
    return df

# Clustering par type
vessel_types = ['Cargo', 'Tanker', 'Passenger', 'Fishing', 'Pleasure Craft']

for vtype in vessel_types:
    df_clustered = cluster_by_vessel_type(vtype, eps_km=1.0, min_samples=30)
    
    if df_clustered is not None:
        # Sauvegarder
        table_name = f"traffic_clusters_{vtype.lower().replace(' ', '_')}"
        
        cluster_summary = df_clustered[df_clustered['cluster_id'] != -1].groupby('cluster_id').agg({
            'id': 'count',
            'latitude': 'mean',
            'longitude': 'mean',
            'sog': 'mean'
        }).reset_index()
        
        cluster_summary.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"  → Saved to {table_name}")
```

**Livrables** :
- Tables : `traffic_clusters_{type}`
- Cartes par type de navire
- Comparaison inter-types

---

### 4.1.3 Identification des corridors de trafic dense

**Objectif** : Extraire lignes centrales des corridors

**Méthode : Alpha Shapes pour contours** :
```python
from shapely.geometry import Point, MultiPoint, Polygon
from shapely.ops import unary_union
import alphashape

def extract_corridor_boundaries(df, cluster_id, alpha=0.05):
    """
    Extraire contour d'un cluster avec alpha shape
    alpha: plus petit = plus détaillé
    """
    cluster_points = df[df['cluster_id'] == cluster_id][['longitude', 'latitude']].values
    
    if len(cluster_points) < 3:
        return None
    
    points = MultiPoint([Point(x, y) for x, y in cluster_points])
    
    # Alpha shape
    try:
        alpha_shape = alphashape.alphashape(points, alpha)
        return alpha_shape
    except:
        # Fallback: convex hull
        return points.convex_hull

def create_corridor_polygons():
    """Créer polygones pour chaque corridor"""
    
    df = pd.read_sql(
        "SELECT * FROM traffic_clusters_global WHERE position_count > 100",
        engine
    )
    
    corridors = []
    
    for _, row in df.iterrows():
        cluster_id = row['cluster_id']
        
        # Charger positions du cluster
        positions = pd.read_sql(f"""
            SELECT ST_Y(geom) AS latitude, ST_X(geom) AS longitude
            FROM position_vessel
            WHERE cluster_id = {cluster_id}
            LIMIT 10000
        """, engine)
        
        polygon = extract_corridor_boundaries(positions, cluster_id)
        
        if polygon:
            corridors.append({
                'cluster_id': cluster_id,
                'geometry': polygon,
                'position_count': row['position_count']
            })
    
    # Créer GeoDataFrame
    gdf = gpd.GeoDataFrame(corridors, crs='EPSG:4326')
    gdf.to_postgis('maritime_corridors', engine, if_exists='replace')
    
    return gdf

corridors_gdf = create_corridor_polygons()
```

**Extraction ligne centrale (centerline)** :
```python
from shapely.ops import linemerge
from shapely.geometry import LineString

def extract_corridor_centerline(corridor_polygon):
    """
    Extraire ligne centrale d'un corridor
    Méthode: skeleton (medial axis)
    """
    from skimage.morphology import medial_axis
    from scipy.ndimage import distance_transform_edt
    
    # Simplifier si besoin
    if isinstance(corridor_polygon, Polygon):
        # Rasteriser
        from rasterio.features import rasterize
        # ... implémentation complexe
        # Alternative simple: utiliser convex hull
        return LineString(corridor_polygon.exterior.coords)
    
    return None

# Extraire centerlines
centerlines = []
for _, row in corridors_gdf.iterrows():
    centerline = extract_corridor_centerline(row['geometry'])
    if centerline:
        centerlines.append({
            'cluster_id': row['cluster_id'],
            'geometry': centerline
        })

centerlines_gdf = gpd.GeoDataFrame(centerlines, crs='EPSG:4326')
centerlines_gdf.to_postgis('corridor_centerlines', engine, if_exists='replace')
```

**Livrables** :
- Table : `maritime_corridors` (polygones)
- Table : `corridor_centerlines` (lignes)
- Carte : corridors avec centerlines

---

### 4.1.4 Calcul de la largeur moyenne des corridors

**Objectif** : Mesurer largeur typique des voies maritimes

**Méthode : Distance perpendiculaire** :
```sql
-- Largeur estimée depuis aire et longueur
CREATE TABLE corridor_dimensions AS
SELECT
    cluster_id,
    position_count,
    ST_Area(geometry::geography) / 1000000 AS area_km2,
    ST_Length(
        (SELECT geometry FROM corridor_centerlines cl 
         WHERE cl.cluster_id = mc.cluster_id)::geography
    ) / 1000 AS length_km,
    -- Largeur moyenne = aire / longueur
    (ST_Area(geometry::geography) / 1000000) / NULLIF(
        ST_Length(
            (SELECT geometry FROM corridor_centerlines cl 
             WHERE cl.cluster_id = mc.cluster_id)::geography
        ) / 1000,
        0
    ) AS avg_width_km
FROM maritime_corridors mc;
```

**Livrables** :
- Table : `corridor_dimensions`
- Statistiques : largeurs typiques par zone

---

### 4.1.5 Création de lignes centrales des routes

**Objectif** : Routes standardisées pour navigation

**Table finale des routes** :
```sql
CREATE TABLE maritime_routes AS
SELECT
    row_number() OVER () AS route_id,
    cl.cluster_id,
    cl.geometry AS route_geom,
    cd.length_km,
    cd.avg_width_km,
    cd.position_count AS traffic_volume,
    tcg.avg_sog AS typical_speed_knots
FROM corridor_centerlines cl
JOIN corridor_dimensions cd ON cl.cluster_id = cd.cluster_id
JOIN traffic_clusters_global tcg ON cl.cluster_id = tcg.cluster_id
WHERE cd.length_km > 5  -- Routes > 5 km
ORDER BY cd.position_count DESC;

CREATE INDEX idx_maritime_routes_geom ON maritime_routes USING GIST (route_geom);
```

**Export GeoJSON pour cartographie** :
```python
def export_routes_geojson():
    query = """
    SELECT
        route_id,
        cluster_id,
        length_km,
        avg_width_km,
        traffic_volume,
        typical_speed_knots,
        ST_AsGeoJSON(route_geom) AS geometry
    FROM maritime_routes
    ORDER BY traffic_volume DESC
    """
    
    df = pd.read_sql(query, engine)
    
    features = []
    for _, row in df.iterrows():
        feature = {
            'type': 'Feature',
            'geometry': eval(row['geometry']),
            'properties': {
                'route_id': row['route_id'],
                'length_km': row['length_km'],
                'width_km': row['avg_width_km'],
                'traffic_volume': row['traffic_volume'],
                'speed_knots': row['typical_speed_knots']
            }
        }
        features.append(feature)
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    import json
    with open('data/maritime_routes.geojson', 'w') as f:
        json.dump(geojson, f, indent=2)

export_routes_geojson()
```

**Livrables** :
- Table : `maritime_routes`
- GeoJSON : `data/maritime_routes.geojson`
- Carte interactive avec routes

---

## 4.2 Routes Commerciales

### 4.2.1 Extraction routes Cargo (70-79)

**Objectif** : Identifier routes principales du fret

**Requête spécifique Cargo** :
```sql
CREATE TABLE cargo_routes AS
WITH cargo_positions AS (
    SELECT
        pv.id,
        pv.vessel_id,
        pv.geom,
        pv.base_date_time,
        pv.sog,
        pv.cog
    FROM position_vessel pv
    JOIN vessel v ON pv.vessel_id = v.id
    JOIN vessel_type vt ON v.vessel_type_id = vt.id
    WHERE vt.type_code BETWEEN 70 AND 79
      AND pv.is_valid = true
      AND pv.is_moving = true
      AND pv.distance_to_nearest_port_nm > 10  -- Exclure zones portuaires
)
SELECT
    mr.route_id,
    mr.route_geom,
    COUNT(DISTINCT cp.vessel_id) AS cargo_vessels_count,
    COUNT(cp.id) AS cargo_positions_count,
    AVG(cp.sog) AS avg_cargo_speed,
    mr.length_km,
    mr.traffic_volume
FROM maritime_routes mr
JOIN cargo_positions cp ON ST_DWithin(
    mr.route_geom::geography,
    cp.geom::geography,
    1000  -- 1 km buffer
)
GROUP BY mr.route_id, mr.route_geom, mr.length_km, mr.traffic_volume
HAVING COUNT(DISTINCT cp.vessel_id) >= 10
ORDER BY cargo_positions_count DESC;
```

**Livrables** :
- Table : `cargo_routes`
- Carte : routes cargo principales
- Statistiques : top 20 routes cargo

---

### 4.2.2 Extraction routes Tanker (80-89)

**Objectif** : Routes pétroliers/chimiquiers

**Similarité avec cargo** :
```sql
CREATE TABLE tanker_routes AS
WITH tanker_positions AS (
    SELECT
        pv.id,
        pv.vessel_id,
        pv.geom,
        pv.sog
    FROM position_vessel pv
    JOIN vessel v ON pv.vessel_id = v.id
    JOIN vessel_type vt ON v.vessel_type_id = vt.id
    WHERE vt.type_code BETWEEN 80 AND 89
      AND pv.is_valid = true
      AND pv.is_moving = true
      AND pv.distance_to_nearest_port_nm > 10
)
SELECT
    mr.route_id,
    mr.route_geom,
    COUNT(DISTINCT tp.vessel_id) AS tanker_vessels_count,
    COUNT(tp.id) AS tanker_positions_count,
    AVG(tp.sog) AS avg_tanker_speed,
    mr.length_km
FROM maritime_routes mr
JOIN tanker_positions tp ON ST_DWithin(
    mr.route_geom::geography,
    tp.geom::geography,
    1000
)
GROUP BY mr.route_id, mr.route_geom, mr.length_km
HAVING COUNT(DISTINCT tp.vessel_id) >= 5
ORDER BY tanker_positions_count DESC;
```

**Livrables** :
- Table : `tanker_routes`
- Comparaison cargo vs tanker routes

---

### 4.2.3 Identification routes principales (> 100 passages)

**Objectif** : Routes à fort trafic

**Requête passages** :
```sql
CREATE MATERIALIZED VIEW high_traffic_routes AS
SELECT
    route_id,
    route_geom,
    length_km,
    traffic_volume,
    typical_speed_knots,
    traffic_volume / NULLIF(length_km, 0) AS traffic_density_per_km,
    CASE
        WHEN traffic_volume > 1000 THEN 'VERY_HIGH'
        WHEN traffic_volume > 500 THEN 'HIGH'
        WHEN traffic_volume > 100 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS traffic_level
FROM maritime_routes
WHERE traffic_volume >= 100
ORDER BY traffic_volume DESC;

-- Statistiques
SELECT
    traffic_level,
    COUNT(*) AS route_count,
    AVG(length_km) AS avg_length_km,
    SUM(traffic_volume) AS total_traffic
FROM high_traffic_routes
GROUP BY traffic_level;
```

**Livrables** :
- Vue : `high_traffic_routes`
- Carte : routes par niveau de trafic (couleurs)

---

### 4.2.4 Calcul de fréquence de passage par route

**Objectif** : Navires par jour/semaine/mois

**Calcul fréquence** :
```sql
CREATE TABLE route_passage_frequency AS
SELECT
    mr.route_id,
    COUNT(DISTINCT pv.vessel_id) AS unique_vessels,
    COUNT(DISTINCT DATE(pv.base_date_time)) AS active_days,
    COUNT(*) AS total_positions,
    COUNT(*) / NULLIF(COUNT(DISTINCT DATE(pv.base_date_time)), 0) AS avg_positions_per_day,
    COUNT(DISTINCT pv.vessel_id) / NULLIF(COUNT(DISTINCT DATE(pv.base_date_time)), 0) AS avg_vessels_per_day
FROM maritime_routes mr
JOIN position_vessel pv ON ST_DWithin(
    mr.route_geom::geography,
    pv.geom::geography,
    1000
)
WHERE pv.is_valid = true
  AND pv.is_moving = true
GROUP BY mr.route_id;
```

**Livrables** :
- Table : `route_passage_frequency`
- Graphique : fréquence par route

---

### 4.2.5 Identification heures de pointe par route

**Objectif** : Patterns temporels sur les routes

**Analyse horaire** :
```sql
CREATE TABLE route_hourly_traffic AS
SELECT
    mr.route_id,
    EXTRACT(HOUR FROM pv.base_date_time) AS hour_of_day,
    EXTRACT(DOW FROM pv.base_date_time) AS day_of_week,
    COUNT(*) AS position_count,
    COUNT(DISTINCT pv.vessel_id) AS vessel_count
FROM maritime_routes mr
JOIN position_vessel pv ON ST_DWithin(
    mr.route_geom::geography,
    pv.geom::geography,
    1000
)
WHERE pv.is_valid = true
GROUP BY mr.route_id, EXTRACT(HOUR FROM pv.base_date_time), 
         EXTRACT(DOW FROM pv.base_date_time);

-- Identifier heures de pointe
CREATE MATERIALIZED VIEW route_peak_hours AS
SELECT
    route_id,
    hour_of_day,
    SUM(position_count) AS total_traffic,
    AVG(vessel_count) AS avg_vessels
FROM route_hourly_traffic
GROUP BY route_id, hour_of_day
ORDER BY route_id, total_traffic DESC;
```

**Heatmap temporelle** :
```python
def plot_route_temporal_heatmap(route_id):
    query = f"""
    SELECT
        hour_of_day,
        day_of_week,
        SUM(position_count) AS traffic
    FROM route_hourly_traffic
    WHERE route_id = {route_id}
    GROUP BY hour_of_day, day_of_week
    """
    df = pd.read_sql(query, engine)
    
    # Pivot pour heatmap
    pivot = df.pivot(index='hour_of_day', columns='day_of_week', values='traffic')
    pivot = pivot.fillna(0)
    
    import seaborn as sns
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(pivot, cmap='YlOrRd', annot=True, fmt='.0f', ax=ax)
    ax.set_xlabel('Day of Week (0=Sun, 6=Sat)')
    ax.set_ylabel('Hour of Day')
    ax.set_title(f'Traffic Heatmap for Route {route_id}')
    
    plt.tight_layout()
    plt.savefig(f'reports/route_{route_id}_temporal_heatmap.png', dpi=300)
```

**Livrables** :
- Table : `route_hourly_traffic`
- Vue : `route_peak_hours`
- Heatmaps par route

---

## 4.3 Routes Spécialisées

### 4.3.1 Routes de pêche (zone + retour port)

**Objectif** : Identifier zones de pêche et trajets associés

**Extraction cycles de pêche** :
```sql
CREATE TABLE fishing_routes AS
WITH fishing_trips AS (
    SELECT
        v.id AS vessel_id,
        v.mmsi,
        MIN(pv.base_date_time) FILTER (WHERE pv.distance_to_nearest_port_nm < 2) AS departure_time,
        MAX(pv.base_date_time) FILTER (WHERE pv.distance_to_nearest_port_nm < 2) AS return_time,
        AVG(ST_Y(pv.geom)) FILTER (WHERE pv.distance_to_nearest_port_nm > 10 AND pv.sog < 5) AS fishing_zone_lat,
        AVG(ST_X(pv.geom)) FILTER (WHERE pv.distance_to_nearest_port_nm > 10 AND pv.sog < 5) AS fishing_zone_lon,
        pv.nearest_port_id
    FROM vessel v
    JOIN vessel_type vt ON v.vessel_type_id = vt.id
    JOIN position_vessel pv ON v.id = pv.vessel_id
    WHERE vt.type_code = 30  -- Fishing
      AND pv.is_valid = true
    GROUP BY v.id, v.mmsi, pv.nearest_port_id
    HAVING COUNT(*) FILTER (WHERE pv.distance_to_nearest_port_nm > 10) > 50
)
SELECT
    vessel_id,
    mmsi,
    nearest_port_id,
    COUNT(*) AS trip_count,
    AVG(fishing_zone_lat) AS avg_fishing_lat,
    AVG(fishing_zone_lon) AS avg_fishing_lon,
    ST_MakeLine(
        ST_SetSRID(ST_MakePoint(
            (SELECT ST_X(geom) FROM ports WHERE id = nearest_port_id),
            (SELECT ST_Y(geom) FROM ports WHERE id = nearest_port_id)
        ), 4326),
        ST_SetSRID(ST_MakePoint(AVG(fishing_zone_lon), AVG(fishing_zone_lat)), 4326)
    ) AS route_geom
FROM fishing_trips
GROUP BY vessel_id, mmsi, nearest_port_id;
```

**Livrables** :
- Table : `fishing_routes`
- Carte : routes de pêche par port d'attache

---

### 4.3.2 Routes de ferries/passenger

**Objectif** : Lignes régulières de passagers

**Déjà couvert en Phase 3.2.4**

---

### 4.3.3 Routes de plaisance (côtières)

**Objectif** : Circuits touristiques

**Extraction routes côtières** :
```sql
CREATE TABLE pleasure_craft_routes AS
SELECT
    vessel_id,
    COUNT(*) AS position_count,
    ST_MakeLine(geom ORDER BY base_date_time) AS route_geom,
    MIN(base_date_time) AS trip_start,
    MAX(base_date_time) AS trip_end,
    AVG(distance_to_nearest_port_nm) AS avg_distance_from_coast
FROM position_vessel pv
JOIN vessel v ON pv.vessel_id = v.id
JOIN vessel_type vt ON v.vessel_type_id = vt.id
WHERE vt.type_code = 37  -- Pleasure Craft
  AND pv.is_valid = true
  AND pv.is_moving = true
  AND pv.distance_to_nearest_port_nm < 20  -- Côtier
GROUP BY vessel_id
HAVING COUNT(*) >= 10;
```

**Livrables** :
- Table : `pleasure_craft_routes`
- Carte : circuits plaisance populaires

---

### 4.3.4 Routes saisonnières

**Objectif** : Identifier routes variant avec saisons

**Analyse saisonnière** :
```sql
CREATE TABLE seasonal_route_patterns AS
SELECT
    mr.route_id,
    EXTRACT(MONTH FROM pv.base_date_time) AS month,
    COUNT(*) AS traffic_count,
    COUNT(DISTINCT pv.vessel_id) AS vessel_count
FROM maritime_routes mr
JOIN position_vessel pv ON ST_DWithin(
    mr.route_geom::geography,
    pv.geom::geography,
    1000
)
WHERE pv.is_valid = true
GROUP BY mr.route_id, EXTRACT(MONTH FROM pv.base_date_time)
ORDER BY mr.route_id, month;

-- Identifier routes saisonnières (variance élevée)
CREATE MATERIALIZED VIEW seasonal_routes AS
SELECT
    route_id,
    STDDEV(traffic_count) AS traffic_stddev,
    AVG(traffic_count) AS avg_traffic,
    STDDEV(traffic_count) / NULLIF(AVG(traffic_count), 0) AS seasonality_coefficient
FROM seasonal_route_patterns
GROUP BY route_id
HAVING STDDEV(traffic_count) / NULLIF(AVG(traffic_count), 0) > 0.5  -- CV > 50%
ORDER BY seasonality_coefficient DESC;
```

**Livrables** :
- Table : `seasonal_route_patterns`
- Vue : `seasonal_routes`
- Graphiques : trafic mensuel par route

---

### 4.3.5 Carte des routes par catégorie

**Objectif** : Visualisation finale multi-layers

**Carte Folium interactive** :
```python
def create_comprehensive_route_map():
    m = folium.Map(
        location=[37.5, -122.0],
        zoom_start=7,
        tiles='CartoDB positron'
    )
    
    # Layer 1: Cargo routes
    cargo = gpd.read_postgis("SELECT * FROM cargo_routes", engine, geom_col='route_geom')
    folium.GeoJson(
        cargo,
        name='Cargo Routes',
        style_function=lambda x: {
            'color': 'blue',
            'weight': 3,
            'opacity': 0.7
        }
    ).add_to(m)
    
    # Layer 2: Tanker routes
    tanker = gpd.read_postgis("SELECT * FROM tanker_routes", engine, geom_col='route_geom')
    folium.GeoJson(
        tanker,
        name='Tanker Routes',
        style_function=lambda x: {
            'color': 'red',
            'weight': 3,
            'opacity': 0.7
        }
    ).add_to(m)
    
    # Layer 3: Fishing routes
    fishing = gpd.read_postgis("SELECT * FROM fishing_routes", engine, geom_col='route_geom')
    folium.GeoJson(
        fishing,
        name='Fishing Routes',
        style_function=lambda x: {
            'color': 'green',
            'weight': 2,
            'opacity': 0.6
        }
    ).add_to(m)
    
    # Layer control
    folium.LayerControl().add_to(m)
    
    m.save('reports/maritime_routes_by_category.html')

create_comprehensive_route_map()
```

**Livrables** :
- Carte : `reports/maritime_routes_by_category.html`
- Légende complète par type

---

## 4.4 Points d'Intérêt

### 4.4.1 Points de croisement majeurs

**Objectif** : Identifier intersections de routes

**Détection intersections** :
```sql
CREATE TABLE route_intersections AS
SELECT
    r1.route_id AS route_1_id,
    r2.route_id AS route_2_id,
    ST_Intersection(r1.route_geom, r2.route_geom) AS intersection_geom,
    r1.traffic_volume + r2.traffic_volume AS combined_traffic
FROM maritime_routes r1
JOIN maritime_routes r2 ON r1.route_id < r2.route_id
WHERE ST_Intersects(r1.route_geom, r2.route_geom)
  AND ST_GeometryType(ST_Intersection(r1.route_geom, r2.route_geom)) = 'ST_Point';

-- Top intersections
SELECT
    route_1_id,
    route_2_id,
    combined_traffic,
    ST_Y(intersection_geom) AS lat,
    ST_X(intersection_geom) AS lon
FROM route_intersections
ORDER BY combined_traffic DESC
LIMIT 20;
```

**Livrables** :
- Table : `route_intersections`
- Carte : points de croisement critiques

---

### 4.4.2 Zones d'attente (ancrage)

**Objectif** : Identifier zones de mouillage fréquentes

**Détection anchorage** :
```sql
CREATE TABLE anchorage_zones AS
WITH stationary_positions AS (
    SELECT
        vessel_id,
        geom,
        base_date_time,
        sog
    FROM position_vessel
    WHERE is_valid = true
      AND sog < 0.5
      AND distance_to_nearest_port_nm BETWEEN 1 AND 10
)
SELECT
    ST_ClusterDBSCAN(geom, eps := 0.01, minpoints := 50) OVER () AS zone_id,
    COUNT(*) AS position_count,
    AVG(ST_Y(geom)) AS center_lat,
    AVG(ST_X(geom)) AS center_lon,
    ST_ConvexHull(ST_Collect(geom)) AS zone_boundary
FROM stationary_positions
GROUP BY zone_id
HAVING zone_id IS NOT NULL
ORDER BY position_count DESC;
```

**Livrables** :
- Table : `anchorage_zones`
- Carte : zones d'attente identifiées

---

### 4.4.3 Zones de transbordement

**Objectif** : Ship-to-ship transfers

**Détection rencontres** :
```sql
CREATE TABLE potential_transhipment_zones AS
WITH close_encounters AS (
    SELECT
        p1.vessel_id AS vessel_1,
        p2.vessel_id AS vessel_2,
        p1.base_date_time,
        ST_Distance(p1.geom::geography, p2.geom::geography) AS distance_m,
        (p1.geom + p2.geom) / 2 AS meeting_point  -- Point milieu
    FROM position_vessel p1
    JOIN position_vessel p2 ON p1.id < p2.id
        AND p1.base_date_time = p2.base_date_time
        AND ST_DWithin(p1.geom::geography, p2.geom::geography, 200)  -- < 200m
    WHERE p1.sog < 2 AND p2.sog < 2  -- Stationnaires
      AND p1.distance_to_nearest_port_nm > 5
      AND p2.distance_to_nearest_port_nm > 5
)
SELECT
    ST_ClusterDBSCAN(meeting_point, eps := 0.05, minpoints := 3) OVER () AS zone_id,
    COUNT(*) AS encounter_count,
    AVG(ST_Y(meeting_point)) AS center_lat,
    AVG(ST_X(meeting_point)) AS center_lon
FROM close_encounters
GROUP BY zone_id
HAVING zone_id IS NOT NULL;
```

**Livrables** :
- Table : `potential_transhipment_zones`
- Alertes : zones suspectes

---

### 4.4.4 Temps moyen par segment de route

**Objectif** : Calculer durée typique de transit

**Segmentation routes** :
```sql
-- Diviser routes en segments
CREATE TABLE route_segments AS
SELECT
    route_id,
    generate_series(1, ST_NumPoints(route_geom) - 1) AS segment_number,
    ST_MakeLine(
        ST_PointN(route_geom, generate_series),
        ST_PointN(route_geom, generate_series + 1)
    ) AS segment_geom
FROM maritime_routes;

-- Calculer temps par segment
CREATE TABLE segment_transit_times AS
SELECT
    rs.route_id,
    rs.segment_number,
    AVG(EXTRACT(EPOCH FROM (p2.base_date_time - p1.base_date_time)) / 3600) AS avg_transit_hours,
    COUNT(*) AS sample_count
FROM route_segments rs
JOIN position_vessel p1 ON ST_DWithin(ST_StartPoint(rs.segment_geom)::geography, p1.geom::geography, 500)
JOIN position_vessel p2 ON ST_DWithin(ST_EndPoint(rs.segment_geom)::geography, p2.geom::geography, 500)
    AND p2.vessel_id = p1.vessel_id
    AND p2.base_date_time > p1.base_date_time
    AND p2.base_date_time < p1.base_date_time + INTERVAL '6 hours'
GROUP BY rs.route_id, rs.segment_number
HAVING COUNT(*) >= 5;
```

**Livrables** :
- Table : `segment_transit_times`
- Carte : routes colorées par vitesse moyenne

---

### 4.4.5 Goulots d'étranglement

**Objectif** : Identifier zones de congestion

**Détection bottlenecks** :
```sql
CREATE TABLE traffic_bottlenecks AS
WITH narrow_corridors AS (
    SELECT
        route_id,
        route_geom,
        avg_width_km,
        traffic_volume
    FROM maritime_routes
    WHERE avg_width_km < 2  -- Largeur < 2 km
      AND traffic_volume > 100
),
high_density_points AS (
    SELECT
        nc.route_id,
        ST_LineInterpolatePoint(nc.route_geom, generate_series(0, 1, 0.1)) AS point,
        nc.traffic_volume / nc.avg_width_km AS density
    FROM narrow_corridors nc
)
SELECT
    route_id,
    ST_Y(point) AS lat,
    ST_X(point) AS lon,
    density AS congestion_index
FROM high_density_points
WHERE density > 50  -- Seuil empirique
ORDER BY density DESC;
```

**Livrables** :
- Table : `traffic_bottlenecks`
- Carte : zones de congestion
- Alertes : goulots critiques

---

## 📊 Livrables de la Phase 4

### Tables Principales
```sql
traffic_clusters_global
maritime_corridors
corridor_centerlines
corridor_dimensions
maritime_routes
cargo_routes
tanker_routes
fishing_routes
pleasure_craft_routes
route_passage_frequency
route_hourly_traffic
route_intersections
anchorage_zones
potential_transhipment_zones
route_segments
segment_transit_times
traffic_bottlenecks
seasonal_route_patterns
```

### Scripts Python
```
clustering/
├── dbscan_global.py
├── cluster_by_vessel_type.py
├── extract_corridors.py
├── analyze_route_frequency.py
└── identify_bottlenecks.py
```

### Visualisations
```
reports/
├── traffic_clusters_map.html
├── maritime_routes_by_category.html
├── route_temporal_heatmaps/
├── intersection_points_map.html
└── bottlenecks_map.html
```

### Exports
```
data/
├── maritime_routes.geojson
├── cargo_routes.geojson
├── tanker_routes.geojson
└── fishing_routes.geojson
```

---

## ✅ Critères de Validation

**Phase 4 considérée terminée si** :

1. ✅ **Clustering réussi**
   - Minimum 50 clusters identifiés
   - Corridors extraits avec polygones

2. ✅ **Routes définies**
   - Centerlines créées
   - Routes par type de navire

3. ✅ **Analyse de trafic**
   - Fréquence calculée par route
   - Heures de pointe identifiées

4. ✅ **Points d'intérêt identifiés**
   - Intersections détectées
   - Zones d'attente localisées

5. ✅ **Exports et cartes**
   - GeoJSON générés
   - Carte interactive complète

---

**Fin de SPECS_PHASE_04.md**

> **Prochaine étape** : **SPECS_PHASE_05.md** (Analyse Temporelle) ?
