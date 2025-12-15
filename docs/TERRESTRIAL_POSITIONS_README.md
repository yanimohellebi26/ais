# Détection et Gestion des Positions Terrestres (Navires sur Terre)

## Vue d'ensemble

Ce module permet de détecter et gérer les positions de navires qui se trouvent incorrectement sur terre. Ces positions aberrantes peuvent provenir de:
- Erreurs GPS
- Transmission de données corrompues
- Équipement AIS défectueux
- Problèmes de traitement des données

## Composants

### 1. Module de Transformation ETL
**Fichier**: `etl/etl/transform/transform_terrestrial_positions.py`

Module principal qui fournit les fonctions de détection et de gestion des positions terrestres.

#### Fonctions principales

##### `detect_terrestrial_positions(context, action, distance_threshold_meters)`
Fonction principale de détection des positions terrestres.

**Paramètres**:
- `context`: PipelineContext contenant le DataFrame avec les positions
- `action`: Stratégie de gestion (voir ci-dessous)
- `distance_threshold_meters`: Seuil de distance au rivage (défaut: 100m)

**Actions disponibles**:
- `"flag"`: Ajoute une colonne `is_on_land` sans supprimer les données
- `"remove"`: Supprime toutes les positions terrestres
- `"move_to_shore"`: Corrige les positions proches du rivage, supprime les autres
- `"report"`: Génère uniquement des statistiques sans modification

**Retour**: PipelineContext mis à jour

##### `create_land_geometry_table(simplification_tolerance)`
Crée la table `land_polygons` pour stocker les géométries terrestres.

**Note**: Vous devez ensuite peupler cette table avec des données géographiques réelles (Natural Earth, OpenStreetMap, etc.)

### 2. Migration Base de Données
**Fichier**: `db/migrations/V10__create_land_polygons_table.sql`

Crée:
- Table `land_polygons` pour stocker les géométries de terre
- Colonnes `is_on_land` et `position_corrected` dans `position_vessel`
- Index spatiaux pour performance optimale
- Fonctions utilitaires PostgreSQL/PostGIS
- Vue `positions_on_land` pour requêtes faciles

#### Fonctions SQL créées

##### `is_position_on_land(lat, lon, threshold_meters)`
Vérifie si une position est sur terre.

```sql
SELECT is_position_on_land(43.3, 5.4, 100);  -- Returns boolean
```

##### `distance_to_nearest_land(lat, lon)`
Calcule la distance au rivage le plus proche.

```sql
SELECT distance_to_nearest_land(43.3, 5.4);  -- Returns distance in meters
```

### 3. Tests Unitaires
**Fichier**: `etl/tests/test_terrestrial_positions.py`

Suite complète de tests couvrant:
- Détection avec DataFrame vide
- Gestion des colonnes manquantes
- Coordonnées invalides
- Toutes les stratégies d'action
- Scénarios d'intégration (entrée de port, pêche, etc.)
- Traitement par lots

**Exécution des tests**:
```bash
cd etl
pytest tests/test_terrestrial_positions.py -v
```

### 4. Notebook d'Analyse
**Fichier**: `notebooks/terrestrial_positions_detection.ipynb`

Notebook Jupyter interactif pour:
- Charger et analyser les positions
- Détecter les positions terrestres
- Visualiser sur carte interactive
- Analyser par type de navire, temporellement
- Générer des rapports et recommandations
- Exporter les résultats

## Installation et Configuration

### 1. Prérequis
```bash
# PostGIS doit être installé dans PostgreSQL
sudo apt-get install postgis

# Dans PostgreSQL
CREATE EXTENSION IF NOT EXISTS postgis;
```

### 2. Appliquer la Migration
```bash
cd db
# Utiliser Flyway ou votre outil de migration
flyway migrate
```

### 3. Charger des Données Géographiques (Recommandé)

#### Option A: Natural Earth Data (Recommandé pour production)
```bash
# Télécharger les données
wget https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_land.zip
unzip ne_10m_land.zip

# Importer dans PostgreSQL
ogr2ogr -f PostgreSQL \
  PG:"host=localhost dbname=ais user=postgres password=yourpass" \
  ne_10m_land.shp \
  -nln land_polygons \
  -append \
  -t_srs EPSG:4326
```

#### Option B: OpenStreetMap Data
```bash
# Utiliser osm2pgsql ou osmium pour extraire les polygones terrestres
# Plus précis mais nécessite plus de traitement
```

### 4. Indexation (Important pour Performance)
```sql
-- Vérifier que les index sont créés
SELECT * FROM pg_indexes WHERE tablename = 'land_polygons';

-- Analyser la table pour optimisation
ANALYZE land_polygons;
ANALYZE position_vessel;
```

## Utilisation

### Dans un Pipeline ETL

```python
from etl.models.context import PipelineContext
from etl.transform.transform_terrestrial_positions import detect_terrestrial_positions

# Dans votre pipeline
def process_positions(df):
    context = PipelineContext(df=df)
    
    # Détecter et supprimer les positions terrestres
    context = detect_terrestrial_positions(
        context,
        action="remove",
        distance_threshold_meters=100.0
    )
    
    return context.df

# Exemple avec flag (ne supprime pas)
def flag_positions(df):
    context = PipelineContext(df=df)
    
    # Juste flaguer pour analyse ultérieure
    context = detect_terrestrial_positions(
        context,
        action="flag",
        distance_threshold_meters=50.0
    )
    
    return context.df
```

### Requêtes SQL Directes

```sql
-- Compter les positions terrestres
SELECT COUNT(*) 
FROM position_vessel 
WHERE is_on_land = TRUE;

-- Positions terrestres par navire
SELECT 
    v.mmsi,
    v.vessel_name,
    COUNT(*) as terrestrial_positions,
    MIN(pv.base_date_time) as first_occurrence,
    MAX(pv.base_date_time) as last_occurrence
FROM position_vessel pv
JOIN vessel v ON pv.vessel_id = v.id
WHERE pv.is_on_land = TRUE
GROUP BY v.mmsi, v.vessel_name
ORDER BY terrestrial_positions DESC;

-- Utiliser la vue
SELECT * FROM positions_on_land
WHERE base_date_time >= NOW() - INTERVAL '7 days'
ORDER BY base_date_time DESC;

-- Vérifier une position spécifique
SELECT 
    is_position_on_land(43.2965, 5.3698, 100) as is_marseille_on_land,
    is_position_on_land(43.0, 5.0, 100) as is_sea_on_land;
```

### Dans le Notebook

Ouvrir `notebooks/terrestrial_positions_detection.ipynb` et exécuter les cellules pour:
1. Charger les données
2. Détecter les positions terrestres
3. Visualiser sur carte
4. Analyser les patterns
5. Générer un rapport

## Configuration des Seuils

### Distance au Rivage
Le paramètre `distance_threshold_meters` définit à quelle distance du rivage une position est considérée comme "sur terre".

**Valeurs recommandées**:
- `0-50m`: Très strict, détecte uniquement les positions clairement sur terre
- `50-100m`: Balance entre précision GPS et détection (RECOMMANDÉ)
- `100-200m`: Plus tolérant, pour GPS moins précis
- `>200m`: Détecte aussi les positions en eaux très peu profondes

### Choix de l'Action

| Action | Quand l'utiliser |
|--------|------------------|
| `flag` | Analyse exploratoire, garder toutes les données |
| `remove` | Nettoyage des données, positions clairement erronées |
| `move_to_shore` | Positions proches du rivage (erreur GPS mineure) |
| `report` | Audit sans modification |

## Performance

### Optimisations

1. **Index Spatiaux**: Créés automatiquement par la migration
2. **Partitioning**: Pour de grandes tables `position_vessel`:
   ```sql
   -- Partitionner par date
   CREATE TABLE position_vessel_2025_01 PARTITION OF position_vessel
   FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
   ```

3. **Matérialized Views**: Pour statistiques fréquentes:
   ```sql
   CREATE MATERIALIZED VIEW terrestrial_stats AS
   SELECT 
       date_trunc('day', base_date_time) as day,
       COUNT(*) as total_positions,
       SUM(CASE WHEN is_on_land THEN 1 ELSE 0 END) as terrestrial_count
   FROM position_vessel
   GROUP BY date_trunc('day', base_date_time);
   
   -- Rafraîchir périodiquement
   REFRESH MATERIALIZED VIEW terrestrial_stats;
   ```

### Benchmarks Typiques

| Opération | Volume | Temps |
|-----------|--------|-------|
| Détection avec PostGIS | 10K positions | ~2-3 sec |
| Détection avec PostGIS | 100K positions | ~15-20 sec |
| Détection avec PostGIS | 1M positions | ~2-3 min |

*Note: Avec index spatiaux et données Natural Earth 10m*

## Cas Particuliers

### Navires à Quai
Les navires amarrés peuvent être détectés comme "sur terre" s'ils sont très proches du rivage.

**Solution**: Utiliser `action="move_to_shore"` avec un seuil de 50m.

### Dragueurs et Travaux Portuaires
Ces navires peuvent légitimement être très proches ou sur des zones de remblaiement.

**Solution**: Les exclure du filtre:
```python
# Exclure certains types
df_filtered = df[df['vessel_type'] != 'Dredging']
context = PipelineContext(df=df_filtered)
```

### Zones de Marée
Dans les zones à forte marée, le rivage change.

**Solution**: Utiliser des données bathymétriques et considérer les niveaux de marée.

## Monitoring et Alertes

### Métriques à Suivre

1. **Taux de positions terrestres** (objectif < 1%)
2. **Navires avec positions terrestres fréquentes**
3. **Distribution géographique des détections**
4. **Évolution temporelle**

### Créer une Alerte

```python
def check_terrestrial_threshold(df, threshold_pct=1.0):
    """Alerter si le taux dépasse le seuil."""
    if 'is_on_land' in df.columns:
        pct = (df['is_on_land'].sum() / len(df) * 100)
        if pct > threshold_pct:
            send_alert(f"⚠️ Taux de positions terrestres élevé: {pct:.2f}%")
```

## Troubleshooting

### Problème: Aucune position détectée comme terrestre

**Causes possibles**:
- Table `land_polygons` vide ou pas de données
- Données géographiques incorrectes
- Seuil de distance trop strict

**Solutions**:
1. Vérifier: `SELECT COUNT(*) FROM land_polygons;`
2. Charger des données Natural Earth
3. Augmenter le seuil de distance

### Problème: Trop de positions détectées

**Causes possibles**:
- Données géographiques trop simplifiées
- Seuil de distance trop large
- Positions réellement problématiques

**Solutions**:
1. Utiliser des données haute résolution
2. Réduire le seuil
3. Analyser les cas spécifiques

### Problème: Performance lente

**Causes possibles**:
- Index spatiaux manquants
- Table `land_polygons` non optimisée
- Trop de polygones

**Solutions**:
```sql
-- Vérifier les index
SELECT * FROM pg_indexes WHERE tablename IN ('land_polygons', 'position_vessel');

-- Simplifier les géométries
UPDATE land_polygons 
SET geom = ST_Simplify(geom::geometry, 0.01)::geography;

-- Analyser
ANALYZE land_polygons;
```

## Ressources

### Données Géographiques
- [Natural Earth](https://www.naturalearthdata.com/) - Données globales gratuites
- [OpenStreetMap](https://www.openstreetmap.org/) - Données collaboratives
- [GSHHG](https://www.ngdc.noaa.gov/mgg/shorelines/) - Côtes haute résolution

### Documentation
- [PostGIS Documentation](https://postgis.net/docs/)
- [Geography vs Geometry](https://postgis.net/workshops/postgis-intro/geography.html)
- [Spatial Indexing](https://postgis.net/workshops/postgis-intro/indexing.html)

## Contribution

Pour améliorer ce module:
1. Ajouter des tests pour nouveaux cas
2. Optimiser les requêtes PostGIS
3. Améliorer la détection heuristique
4. Documenter les cas particuliers rencontrés

## Changelog

### Version 1.0.0 (2025-11-10)
- ✓ Détection initiale avec PostGIS
- ✓ Support de 4 stratégies d'action
- ✓ Migration base de données
- ✓ Tests unitaires complets
- ✓ Notebook d'analyse
- ✓ Documentation complète
