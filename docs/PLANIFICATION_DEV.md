# 📋 Planification Développement - Projet AIS

## 📊 RÉSUMÉ DES FONCTIONS DÉJÀ IMPLÉMENTÉES

### ✅ ETL Pipeline (Production-Ready)

#### Extract
- ✅ `extract_data_from_file` - Charger CSV
- ✅ `AISDownloader` - Téléchargement automatique des données AIS

#### Transform
- ✅ `normalize_ais` - Normalisation des types de données
- ✅ `remove_rows_with_empty` - Suppression lignes vides
- ✅ `remove_rows_with_wrong_format` - Validation format
- ✅ `clean_vessel_duplication` - Suppression doublons
- ✅ `clean_and_validate_ais` - Nettoyage complet
- ✅ `get_vessels_db` - Récupération vessels depuis DB
- ✅ `transform_vessel_delta` - Détection nouveaux/modifiés
- ✅ `downsample_ais` - Réduction volume données
- ✅ `filter_small_movements` - Filtrage petits déplacements (<0.1km)
- ✅ `detect_vessel_incoherent_positions` - Détection vitesses aberrantes (>130km/h)
- ✅ `haversine_km` - Calcul distance géographique
- ✅ `speed_kmh` - Calcul vitesse dérivée

#### Load
- ✅ `load_vessel_to_db` - Insert/Update vessels (upsert)
- ✅ `load_position_db` - Insert bulk positions (COPY)
- ✅ `load_vessel_type` - Génération SQL vessel types

### ✅ Notebooks d'Analyse (Exploration)
- ✅ `data_quality_gps_cleaning.ipynb` - Nettoyage GPS
- ✅ `data_quality_speed_outliers.ipynb` - Outliers vitesse
- ✅ `terrestrial_positions_detection.ipynb` - Détection positions terrestres
- ✅ `trajectoire_bateau.ipynb` - Analyse trajectoires
- ✅ `clustering_analysis.ipynb` - Clustering K-Means + DBSCAN

---

## 🚀 À AJOUTER DANS L'ETL (Production)

### 🔴 PRIORITÉ HAUTE - À ajouter dans `/etl/etl/transform/`

#### 1. `transform_gap_detection.py`
```python
def detect_ais_gaps(context, gap_threshold_hours=4):
    """Identifier les gaps AIS par navire (>4h sans signal)"""
    # Calculer delta_time entre positions successives
    # Flaguer gaps > threshold
    # Ajouter colonnes: has_gap, gap_duration_hours
```

#### 2. `transform_feature_engineering.py`
```python
def calculate_movement_features(context):
    """Feature engineering: accélération, changement cap, etc."""
    # Calculer accélération (delta SOG)
    # Calculer changement de cap (delta COG)
    # Flag navire en mouvement (SOG > 1 nœud)
    # Temps total en mer par navire

def calculate_time_at_sea(context):
    """Calculer temps total en mer par navire"""
    # Agrégation par MMSI
    # Retourner DataFrame avec MMSI, total_hours_at_sea
```

#### 3. `transform_status_validation.py`
```python
def validate_status_coherence(context):
    """Valider cohérence statut vs vitesse/position"""
    # Détecter incohérences (status=underway mais SOG=0)
    # Corriger ou flaguer
```

#### 4. `transform_temporal_coherence.py`
```python
def validate_temporal_order(context):
    """Valider ordre chronologique des timestamps"""
    # Trier par MMSI + timestamp
    # Détecter anomalies temporelles
```

### 🟡 PRIORITÉ MOYENNE - À ajouter dans `/etl/etl/load/`

#### 5. `load_statistics_db.py`
```python
def load_vessel_statistics(context):
    """Charger statistiques calculées dans table dédiée"""
    # Insert dans table vessel_statistics (nouvelle table)
```

### 🟠 PRIORITÉ HAUTE - À ajouter dans `/backend/` (API/Site Web)

#### 6. Backend Services pour l'API REST

**`/backend/src/main/java/services/` (ou Python si backend Python)**

##### `StatisticsService.py` / `StatisticsService.java`
```python
class StatisticsService:
    """Service pour calculer et servir les statistiques via API"""
    
    def get_global_statistics(self, date_range):
        """Statistiques globales du trafic"""
        # - Nombre total de navires actifs
        # - Nombre total de positions
        # - Zones les plus fréquentées
        # - Distribution par type de navire
        return {
            "total_vessels": 12500,
            "total_positions": 5_200_000,
            "active_vessels_today": 3200,
            "by_type": {...}
        }
    
    def get_vessel_statistics(self, mmsi):
        """Statistiques d'un navire spécifique"""
        # Query table vessel_statistics
        # Retourner stats du navire
    
    def get_traffic_heatmap_data(self, bounds, zoom_level):
        """Données pour heatmap de trafic"""
        # Agrégation spatiale des positions
        # Retourner GeoJSON avec densité
```

##### `RouteService.py` / `RouteService.java`
```python
class RouteService:
    """Service pour gérer les routes maritimes extraites"""
    
    def get_all_routes(self, vessel_type=None):
        """Récupérer toutes les routes maritimes"""
        # Query table maritime_routes
        # Filtrer par type si spécifié
        # Retourner GeoJSON des routes
    
    def get_route_by_id(self, route_id):
        """Détails d'une route spécifique"""
        # Stats de passage, types de navires, etc.
    
    def calculate_route_from_trajectory(self, mmsi, start_date, end_date):
        """Calculer route depuis trajectoire réelle"""
        # Simplification de trajectoire (Douglas-Peucker)
        # Retourner LineString simplifiée
```

##### `TrajectoryService.py` / `TrajectoryService.java`
```python
class TrajectoryService:
    """Service pour récupérer et analyser les trajectoires"""
    
    def get_vessel_trajectory(self, mmsi, start_date, end_date, simplify=True):
        """Récupérer trajectoire d'un navire"""
        # Query position_vessel
        # Optionnel: simplification pour réduire points
        # Retourner GeoJSON LineString
    
    def get_recent_positions(self, mmsi, limit=100):
        """Positions récentes d'un navire"""
        # Dernières N positions
    
    def get_vessels_in_area(self, bbox, vessel_type=None):
        """Navires dans une zone géographique"""
        # Query spatial avec ST_Within/ST_Intersects
        # Retourner liste de navires + dernière position
```

##### `AnomalyService.py` / `AnomalyService.java`
```python
class AnomalyService:
    """Service pour la détection d'anomalies"""
    
    def get_vessel_anomalies(self, mmsi, days=30):
        """Anomalies détectées pour un navire"""
        # Query table vessel_anomaly_score
        # Retourner liste anomalies avec severity
    
    def get_high_risk_vessels(self, date_range):
        """Liste des navires à haut risque"""
        # Navires avec anomalies severity='high' ou 'critical'
    
    def calculate_real_time_anomaly(self, position_data):
        """Calcul anomalie en temps réel (nouvelle position)"""
        # Charger modèle ML
        # Calculer score
        # Retourner score + alerte si nécessaire
```

##### `FilterService.py` / `FilterService.java`
```python
class FilterService:
    """Service pour filtres avancés et recherches"""
    
    def search_vessels(self, filters):
        """Recherche multicritères de navires"""
        # Filtres: type, zone, vitesse min/max, date, etc.
        # Construction requête SQL dynamique
        # Retourner résultats paginés
    
    def get_vessels_by_port(self, port_id, status='in_port'):
        """Navires dans/près d'un port"""
        # Query avec ST_DWithin(port_location)
    
    def filter_positions_by_criteria(self, criteria):
        """Filtrer positions selon critères complexes"""
        # Speed range, heading, status, etc.
```

##### `PortService.py` / `PortService.java`
```python
class PortService:
    """Service pour gestion des ports"""
    
    def get_all_ports(self):
        """Liste de tous les ports"""
        # Query table ports
    
    def get_port_statistics(self, port_id, date_range):
        """Statistiques d'un port"""
        # Nombre de visites, types navires, durées moyennes
    
    def get_vessels_near_port(self, port_id, radius_km=10):
        """Navires près d'un port"""
        # ST_DWithin query
```

##### `PredictionService.py` / `PredictionService.java`
```python
class PredictionService:
    """Service pour prédictions ML"""
    
    def predict_next_position(self, mmsi, horizon_minutes=30):
        """Prédire prochaine position"""
        # Charger modèle LSTM/Transformer
        # Prédire position à T+horizon
        # Retourner lat/lon + intervalle confiance
    
    def predict_eta(self, mmsi, destination_port_id):
        """Estimer temps d'arrivée (ETA)"""
        # Analyse trajectoire actuelle
        # Distance restante
        # Vitesse moyenne
        # Retourner ETA estimé
    
    def get_traffic_forecast(self, zone, date):
        """Prévision de trafic dans une zone"""
        # Modèle de forecast temporel
        # Retourner prédiction charge trafic
```

##### `ExportService.py` / `ExportService.java`
```python
class ExportService:
    """Service pour exports de données"""
    
    def export_trajectory_geojson(self, mmsi, start_date, end_date):
        """Export trajectoire en GeoJSON"""
    
    def export_statistics_csv(self, vessel_ids, date_range):
        """Export statistiques en CSV"""
    
    def export_heatmap_geotiff(self, bounds, resolution):
        """Export heatmap en GeoTIFF"""
```

---

## 📓 À CRÉER EN NOTEBOOKS (Analyse/Exploration)

### 🔵 Analyses Spatiales - `/notebooks/`

#### 1. `spatial_analysis_zones.ipynb`
- Identifier bounding box global
- Créer grille spatiale (hexagones H3)
- Calculer densité de trafic par cellule
- Heatmaps interactives (Folium/Plotly)
- **Pas de nouvelle table BD** - Résultats en mémoire/fichiers

#### 2. `port_proximity_analysis.ipynb`
- Définir positions ports (liste lat/lon)
- Calculer distance au port le plus proche
- Identifier entrées/sorties zones portuaires
- **Possibilité**: Créer table `ports` si beaucoup de ports

#### 3. `trajectory_analysis_advanced.ipynb`
- Extraire trajectoires complètes par MMSI
- Calculer longueur/tortuosité
- Détecter boucles et retours
- Visualisations trajectoires animées
- **Pas de nouvelle table** - Analyses ad-hoc

### 🔵 Analyses Temporelles - `/notebooks/`

#### 4. `temporal_patterns_analysis.ipynb`
- Distribution horaire du trafic (0-24h)
- Patterns jour/semaine/mois
- Séries temporelles
- **Pas de nouvelle table** - Agrégations à la volée

#### 5. `gap_statistics_analysis.ipynb`
- Statistiques des gaps AIS
- Durées moyennes, fréquences
- Détection désactivations suspectes
- **Pas de nouvelle table** - Analyses exploratoires

### 🔵 Analyses par Type de Navire - `/notebooks/`

#### 6. `vessel_type_behavior_analysis.ipynb`
- Statistiques par vessel_group
- Comparaisons vitesses/zones/durées
- Patterns spécifiques (pêche, cargo, etc.)
- **Pas de nouvelle table** - Requêtes SQL + analyse

### 🔵 Machine Learning - `/notebooks/`

#### 7. `anomaly_detection_ml.ipynb`
- Isolation Forest sur features navigation
- One-Class SVM
- Détection comportements atypiques
- **Nouvelle table**: `vessel_anomaly_score` (MMSI, date, score, type)
- **⚠️ IMPORTANT**: Sauvegarder modèle final dans `/models/anomaly_detection/`

#### 8. `route_extraction_clustering.ipynb`
- Clustering avancé (HDBSCAN)
- Extraction corridors de trafic
- Lignes centrales des routes
- **Nouvelle table**: `maritime_routes` (route_id, geom, vessel_types, frequency)
- **⚠️ IMPORTANT**: Sauvegarder modèle final dans `/models/clustering/`

#### 9. `prediction_trajectory.ipynb`
- Prédiction positions futures (LSTM)
- ETA estimation
- **Nouvelle table**: `trajectory_predictions` (vessel_id, predicted_positions, confidence)
- **⚠️ IMPORTANT**: Sauvegarder modèle final dans `/models/trajectory_prediction/`

#### 10. `vessel_classification_ml.ipynb`
- Classification type de navire depuis comportement
- Random Forest / XGBoost
- Features: vitesse, trajectoire, zones fréquentées
- **⚠️ IMPORTANT**: Sauvegarder modèle final dans `/models/classification/`

#### 11. `speed_prediction_ml.ipynb`
- Prédiction vitesse future basée sur conditions
- Regression models
- **⚠️ IMPORTANT**: Sauvegarder modèle final dans `/models/speed_prediction/`

---

---

## 🌐 À CRÉER POUR LE FRONTEND (API Endpoints)

### API REST à implémenter dans `/backend/src/main/java/controllers/` ou `/etl/api/router/`

#### Endpoints Statistiques
- `GET /api/statistics/global?start_date=X&end_date=Y` - Stats globales
- `GET /api/statistics/vessel/{mmsi}` - Stats d'un navire
- `GET /api/statistics/by-type` - Stats par type de navire
- `GET /api/statistics/traffic-evolution` - Évolution trafic temporelle

#### Endpoints Trajectoires
- `GET /api/trajectory/{mmsi}?start_date=X&end_date=Y` - Trajectoire navire
- `GET /api/trajectory/{mmsi}/recent?limit=100` - Positions récentes
- `GET /api/trajectory/{mmsi}/simplified` - Trajectoire simplifiée
- `GET /api/vessels/in-area?bbox=minLon,minLat,maxLon,maxLat` - Navires dans zone

#### Endpoints Routes Maritimes
- `GET /api/routes` - Toutes les routes maritimes
- `GET /api/routes/{route_id}` - Détails d'une route
- `GET /api/routes/by-type/{vessel_type}` - Routes par type navire
- `GET /api/routes/near?lat=X&lon=Y&radius=Z` - Routes proches d'un point

#### Endpoints Filtres & Recherche
- `POST /api/search/vessels` - Recherche multicritères (body JSON)
- `GET /api/vessels?type=X&min_speed=Y&max_speed=Z` - Filtres GET
- `GET /api/vessels/active?date=X` - Navires actifs à une date
- `GET /api/vessels/by-port/{port_id}` - Navires d'un port

#### Endpoints Anomalies
- `GET /api/anomalies/vessel/{mmsi}` - Anomalies d'un navire
- `GET /api/anomalies/high-risk?date=X` - Navires à haut risque
- `GET /api/anomalies/recent?limit=50` - Dernières anomalies détectées
- `POST /api/anomalies/check` - Check anomalie position en temps réel

#### Endpoints Ports
- `GET /api/ports` - Liste des ports
- `GET /api/ports/{port_id}` - Détails port
- `GET /api/ports/{port_id}/statistics` - Stats port
- `GET /api/ports/{port_id}/vessels` - Navires au port

#### Endpoints Prédictions
- `GET /api/predict/position/{mmsi}?horizon=30` - Prédire position
- `GET /api/predict/eta/{mmsi}?destination_port_id=X` - Estimer ETA
- `GET /api/predict/traffic?zone_id=X&date=Y` - Forecast trafic

#### Endpoints Heatmaps & Visualisations
- `GET /api/heatmap/traffic?bounds=...&zoom=12` - Données heatmap
- `GET /api/heatmap/speed?bounds=...` - Heatmap vitesses
- `GET /api/heatmap/density?date=X` - Densité par zone

#### Endpoints Export
- `GET /api/export/trajectory/{mmsi}/geojson` - Export GeoJSON
- `GET /api/export/statistics/csv?vessel_ids=...` - Export CSV
- `GET /api/export/routes/kml` - Export routes KML

---

## 🎨 COMPOSANTS FRONTEND À CRÉER

### `/frontend/src/components/` (React/Vue)

#### Composants Carte
- **`MapView.jsx`** - Composant carte principal (Leaflet/MapboxGL)
- **`TrafficHeatmap.jsx`** - Layer heatmap de trafic
- **`VesselMarkers.jsx`** - Marqueurs navires en temps réel
- **`RouteLayer.jsx`** - Affichage routes maritimes
- **`TrajectoryLayer.jsx`** - Affichage trajectoire sélectionnée
- **`PortMarkers.jsx`** - Marqueurs des ports

#### Composants Filtres
- **`VesselFilterPanel.jsx`** - Panel filtres multicritères
- **`DateRangePicker.jsx`** - Sélection période temporelle
- **`VesselTypeSelector.jsx`** - Sélection types de navires
- **`SpeedRangeSlider.jsx`** - Slider vitesse min/max
- **`ZoneSelector.jsx`** - Sélection zone géographique

#### Composants Statistiques
- **`GlobalStatsCard.jsx`** - Card statistiques globales
- **`VesselStatsPanel.jsx`** - Panel stats navire sélectionné
- **`TrafficChart.jsx`** - Graphique évolution trafic
- **`VesselTypeDistribution.jsx`** - Chart distribution types
- **`SpeedDistributionChart.jsx`** - Histogramme vitesses

#### Composants Listes & Tables
- **`VesselList.jsx`** - Liste navires avec filtres
- **`VesselTable.jsx`** - Tableau navires (tri, pagination)
- **`AnomalyList.jsx`** - Liste anomalies détectées
- **`RouteList.jsx`** - Liste routes maritimes

#### Composants Détails
- **`VesselDetailModal.jsx`** - Modal détails navire
- **`TrajectoryViewer.jsx`** - Visualisation trajectoire
- **`VesselInfoCard.jsx`** - Card info navire
- **`AnomalyDetailPanel.jsx`** - Détails anomalie

#### Composants Prédictions
- **`PredictionLayer.jsx`** - Affichage prédictions sur carte
- **`ETACalculator.jsx`** - Calculateur ETA
- **`TrafficForecastChart.jsx`** - Graphique forecast

#### Composants Utilitaires
- **`SearchBar.jsx`** - Barre recherche MMSI/nom
- **`ExportButton.jsx`** - Bouton export données
- **`LoadingSpinner.jsx`** - Spinner chargement
- **`ErrorBoundary.jsx`** - Gestion erreurs

### `/frontend/src/pages/` (Pages principales)

- **`Dashboard.jsx`** - Page tableau de bord principal
- **`MapExplorer.jsx`** - Page carte interactive
- **`VesselDetails.jsx`** - Page détails navire
- **`RoutesAnalysis.jsx`** - Page analyse routes
- **`Statistics.jsx`** - Page statistiques complètes
- **`Anomalies.jsx`** - Page détection anomalies
- **`Predictions.jsx`** - Page prédictions

### `/frontend/src/services/` (Services API)

- **`api.js`** - Configuration Axios/Fetch
- **`vesselService.js`** - Appels API vessels
- **`statisticsService.js`** - Appels API stats
- **`routeService.js`** - Appels API routes
- **`anomalyService.js`** - Appels API anomalies
- **`predictionService.js`** - Appels API prédictions

---

## 🤖 MISE EN PRODUCTION DES MODÈLES ML (CRUCIAL!)

### 📦 Structure pour Sauvegarder les Modèles Entraînés

```
models/                           # Dossier racine pour tous les modèles ML
├── anomaly_detection/
│   ├── isolation_forest_v1.pkl   # Modèle Isolation Forest
│   ├── one_class_svm_v1.pkl      # Modèle One-Class SVM
│   ├── scaler.pkl                # Scaler pour normalisation
│   ├── feature_names.json        # Liste des features utilisées
│   └── metadata.json             # Infos: accuracy, date entraînement, etc.
│
├── clustering/
│   ├── dbscan_routes_v1.pkl      # Modèle DBSCAN pour routes
│   ├── hdbscan_zones_v1.pkl      # Modèle HDBSCAN pour zones
│   ├── kmeans_behavior_v1.pkl    # K-Means comportements
│   └── metadata.json
│
├── trajectory_prediction/
│   ├── lstm_model_v1.h5          # Modèle LSTM (Keras/TensorFlow)
│   ├── lstm_model_v1.pth         # Ou PyTorch
│   ├── scaler.pkl
│   ├── sequence_config.json      # Config: seq_length, features, etc.
│   └── metadata.json
│
├── classification/
│   ├── vessel_type_rf_v1.pkl     # Random Forest
│   ├── vessel_type_xgb_v1.pkl    # XGBoost
│   ├── scaler.pkl
│   ├── label_encoder.pkl         # Pour classes
│   └── metadata.json
│
├── speed_prediction/
│   ├── speed_regressor_v1.pkl    # Modèle régression
│   ├── scaler.pkl
│   └── metadata.json
│
└── route_prediction/
    ├── destination_classifier_v1.pkl
    ├── scaler.pkl
    └── metadata.json
```

---

### 🔧 Code Standard pour Sauvegarder un Modèle (Dans Notebook)

#### Exemple 1: Sauvegarder Isolation Forest (Anomaly Detection)

```python
# Dans anomaly_detection_ml.ipynb

import joblib
import json
from datetime import datetime

# 1. Entraîner le modèle
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Préparer données
X_train = df[['sog', 'cog', 'delta_time', 'distance_km', 'speed_kmh']]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)

# Entraîner
model = IsolationForest(contamination=0.1, random_state=42)
model.fit(X_scaled)

# 2. Évaluer le modèle
y_pred = model.predict(X_test)
accuracy = ...

# 3. SAUVEGARDER le modèle
model_dir = "../models/anomaly_detection/"
os.makedirs(model_dir, exist_ok=True)

# Sauvegarder modèle
joblib.dump(model, f"{model_dir}/isolation_forest_v1.pkl")

# Sauvegarder scaler
joblib.dump(scaler, f"{model_dir}/scaler.pkl")

# Sauvegarder features utilisées
feature_names = ['sog', 'cog', 'delta_time', 'distance_km', 'speed_kmh']
with open(f"{model_dir}/feature_names.json", 'w') as f:
    json.dump(feature_names, f)

# Sauvegarder metadata
metadata = {
    "model_name": "Isolation Forest Anomaly Detection",
    "version": "1.0",
    "trained_date": datetime.now().isoformat(),
    "accuracy": float(accuracy),
    "contamination": 0.1,
    "n_samples_trained": len(X_train),
    "features": feature_names,
    "description": "Détection anomalies navigation (vitesse, trajectoire)"
}
with open(f"{model_dir}/metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

print("✅ Modèle sauvegardé avec succès!")
```

#### Exemple 2: Sauvegarder LSTM (Trajectory Prediction)

```python
# Dans prediction_trajectory.ipynb

import tensorflow as tf
from tensorflow import keras
import joblib
import json

# 1. Entraîner LSTM
model = keras.Sequential([
    keras.layers.LSTM(128, return_sequences=True, input_shape=(seq_length, n_features)),
    keras.layers.LSTM(64),
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dense(2)  # lat, lon
])
model.compile(optimizer='adam', loss='mse')
model.fit(X_train, y_train, epochs=50, validation_split=0.2)

# 2. SAUVEGARDER
model_dir = "../models/trajectory_prediction/"
os.makedirs(model_dir, exist_ok=True)

# Sauvegarder modèle Keras
model.save(f"{model_dir}/lstm_model_v1.h5")

# Sauvegarder scaler
joblib.dump(scaler, f"{model_dir}/scaler.pkl")

# Sauvegarder config séquence
sequence_config = {
    "seq_length": 10,  # 10 positions précédentes
    "n_features": 5,   # lat, lon, sog, cog, timestamp
    "feature_names": ['lat', 'lon', 'sog', 'cog', 'timestamp_normalized'],
    "prediction_horizon_minutes": 30
}
with open(f"{model_dir}/sequence_config.json", 'w') as f:
    json.dump(sequence_config, f, indent=2)

# Metadata
metadata = {
    "model_name": "LSTM Trajectory Prediction",
    "version": "1.0",
    "trained_date": datetime.now().isoformat(),
    "val_loss": float(model.history.history['val_loss'][-1]),
    "n_epochs": 50,
    "description": "Prédiction position future à T+30min"
}
with open(f"{model_dir}/metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

print("✅ Modèle LSTM sauvegardé!")
```

---

### 🚀 Charger et Utiliser les Modèles dans le Backend

#### Backend Service: `MLModelService.py`

```python
# /backend/src/services/MLModelService.py

import joblib
import json
import os
from pathlib import Path
import numpy as np

class MLModelService:
    """Service pour charger et utiliser les modèles ML entraînés"""
    
    def __init__(self, models_base_path="../models"):
        self.models_base_path = Path(models_base_path)
        self.loaded_models = {}
        
    def load_anomaly_detection_model(self):
        """Charger le modèle de détection d'anomalies"""
        model_dir = self.models_base_path / "anomaly_detection"
        
        model = joblib.load(model_dir / "isolation_forest_v1.pkl")
        scaler = joblib.load(model_dir / "scaler.pkl")
        
        with open(model_dir / "feature_names.json") as f:
            feature_names = json.load(f)
        
        with open(model_dir / "metadata.json") as f:
            metadata = json.load(f)
        
        self.loaded_models['anomaly_detection'] = {
            'model': model,
            'scaler': scaler,
            'features': feature_names,
            'metadata': metadata
        }
        
        return model
    
    def predict_anomaly(self, vessel_data):
        """
        Prédire si les données d'un navire sont anormales
        
        Args:
            vessel_data: dict avec keys: sog, cog, delta_time, distance_km, speed_kmh
        
        Returns:
            dict: {
                'is_anomaly': bool,
                'anomaly_score': float,
                'confidence': float
            }
        """
        if 'anomaly_detection' not in self.loaded_models:
            self.load_anomaly_detection_model()
        
        model_data = self.loaded_models['anomaly_detection']
        model = model_data['model']
        scaler = model_data['scaler']
        features = model_data['features']
        
        # Préparer données
        X = np.array([[vessel_data[f] for f in features]])
        X_scaled = scaler.transform(X)
        
        # Prédire
        prediction = model.predict(X_scaled)[0]  # -1 = anomalie, 1 = normal
        anomaly_score = model.score_samples(X_scaled)[0]
        
        return {
            'is_anomaly': prediction == -1,
            'anomaly_score': float(anomaly_score),
            'confidence': float(abs(anomaly_score))
        }
    
    def load_trajectory_prediction_model(self):
        """Charger le modèle LSTM de prédiction de trajectoire"""
        from tensorflow import keras
        
        model_dir = self.models_base_path / "trajectory_prediction"
        
        model = keras.models.load_model(model_dir / "lstm_model_v1.h5")
        scaler = joblib.load(model_dir / "scaler.pkl")
        
        with open(model_dir / "sequence_config.json") as f:
            config = json.load(f)
        
        self.loaded_models['trajectory_prediction'] = {
            'model': model,
            'scaler': scaler,
            'config': config
        }
        
        return model
    
    def predict_next_position(self, vessel_history):
        """
        Prédire la prochaine position d'un navire
        
        Args:
            vessel_history: list of dicts avec dernières 10 positions
                [{lat, lon, sog, cog, timestamp}, ...]
        
        Returns:
            dict: {
                'predicted_lat': float,
                'predicted_lon': float,
                'confidence': float
            }
        """
        if 'trajectory_prediction' not in self.loaded_models:
            self.load_trajectory_prediction_model()
        
        model_data = self.loaded_models['trajectory_prediction']
        model = model_data['model']
        scaler = model_data['scaler']
        config = model_data['config']
        
        # Préparer séquence
        features = config['feature_names']
        X = np.array([[pos[f] for f in features] for pos in vessel_history])
        X = X.reshape(1, config['seq_length'], config['n_features'])
        X_scaled = scaler.transform(X.reshape(-1, config['n_features']))
        X_scaled = X_scaled.reshape(1, config['seq_length'], config['n_features'])
        
        # Prédire
        prediction = model.predict(X_scaled)[0]
        
        return {
            'predicted_lat': float(prediction[0]),
            'predicted_lon': float(prediction[1]),
            'prediction_horizon_minutes': config['prediction_horizon_minutes']
        }
    
    def load_clustering_model(self, model_type='dbscan_routes'):
        """Charger modèle de clustering"""
        model_dir = self.models_base_path / "clustering"
        model = joblib.load(model_dir / f"{model_type}_v1.pkl")
        
        self.loaded_models[model_type] = {'model': model}
        return model
    
    def predict_cluster(self, positions, model_type='dbscan_routes'):
        """Assigner positions à des clusters/routes"""
        if model_type not in self.loaded_models:
            self.load_clustering_model(model_type)
        
        model = self.loaded_models[model_type]['model']
        clusters = model.fit_predict(positions)
        
        return clusters.tolist()
```

#### Backend Controller: Utiliser MLModelService

```python
# /backend/src/controllers/PredictionController.py (ou .java)

from services.MLModelService import MLModelService
from flask import Flask, request, jsonify

app = Flask(__name__)
ml_service = MLModelService()

@app.route('/api/predict/anomaly', methods=['POST'])
def predict_anomaly():
    """
    Check si position actuelle d'un navire est anormale
    
    POST body:
    {
        "mmsi": 123456789,
        "sog": 15.5,
        "cog": 180.2,
        "delta_time": 300,
        "distance_km": 12.5,
        "speed_kmh": 28.0
    }
    """
    data = request.json
    
    result = ml_service.predict_anomaly(data)
    
    return jsonify({
        'mmsi': data['mmsi'],
        'is_anomaly': result['is_anomaly'],
        'anomaly_score': result['anomaly_score'],
        'severity': 'high' if result['is_anomaly'] else 'normal'
    })

@app.route('/api/predict/position/<int:mmsi>', methods=['GET'])
def predict_position(mmsi):
    """
    Prédire prochaine position d'un navire
    
    GET /api/predict/position/123456789?horizon=30
    """
    # Récupérer dernières N positions depuis DB
    vessel_history = get_vessel_recent_positions(mmsi, limit=10)
    
    prediction = ml_service.predict_next_position(vessel_history)
    
    return jsonify({
        'mmsi': mmsi,
        'current_position': {
            'lat': vessel_history[-1]['lat'],
            'lon': vessel_history[-1]['lon']
        },
        'predicted_position': {
            'lat': prediction['predicted_lat'],
            'lon': prediction['predicted_lon']
        },
        'prediction_horizon_minutes': prediction['prediction_horizon_minutes']
    })
```

---

## 🗄️ NOUVELLES TABLES À CRÉER EN BD

### 🔴 HAUTE PRIORITÉ

#### 1. Table `vessel_statistics` (pour ETL)
```sql
CREATE TABLE vessel_statistics (
    id SERIAL PRIMARY KEY,
    vessel_id INTEGER REFERENCES vessel(id),
    calculation_date DATE NOT NULL,
    total_hours_at_sea DECIMAL(10,2),
    total_distance_km DECIMAL(12,2),
    avg_speed_knots DECIMAL(6,2),
    max_speed_knots DECIMAL(6,2),
    total_positions INTEGER,
    gap_count INTEGER,
    avg_gap_duration_hours DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(vessel_id, calculation_date)
);
CREATE INDEX idx_vessel_stats_vessel ON vessel_statistics(vessel_id);
CREATE INDEX idx_vessel_stats_date ON vessel_statistics(calculation_date);
```

#### 2. Table `position_gaps` (pour ETL)
```sql
CREATE TABLE position_gaps (
    id SERIAL PRIMARY KEY,
    vessel_id INTEGER REFERENCES vessel(id),
    gap_start TIMESTAMP NOT NULL,
    gap_end TIMESTAMP NOT NULL,
    gap_duration_hours DECIMAL(8,2),
    last_position_before GEOGRAPHY(Point, 4326),
    first_position_after GEOGRAPHY(Point, 4326),
    distance_km DECIMAL(10,2),
    is_suspicious BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_gaps_vessel ON position_gaps(vessel_id);
CREATE INDEX idx_gaps_start ON position_gaps(gap_start);
```

### 🟡 PRIORITÉ MOYENNE

#### 3. Table `maritime_routes` (pour analyses)
```sql
CREATE TABLE maritime_routes (
    id SERIAL PRIMARY KEY,
    route_name VARCHAR(100),
    route_geom GEOGRAPHY(LineString, 4326),
    corridor_width_km DECIMAL(8,2),
    vessel_types INTEGER[],
    passage_count INTEGER,
    avg_vessels_per_day DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_routes_geom ON maritime_routes USING GIST(route_geom);
```

#### 4. Table `vessel_anomaly_score` (pour ML)
```sql
CREATE TABLE vessel_anomaly_score (
    id SERIAL PRIMARY KEY,
    vessel_id INTEGER REFERENCES vessel(id),
    detection_date DATE NOT NULL,
    anomaly_type VARCHAR(50), -- 'speed', 'trajectory', 'gap', 'zone'
    anomaly_score DECIMAL(5,4), -- 0-1
    severity VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_anomaly_vessel ON vessel_anomaly_score(vessel_id);
CREATE INDEX idx_anomaly_date ON vessel_anomaly_score(detection_date);
CREATE INDEX idx_anomaly_severity ON vessel_anomaly_score(severity);
```

#### 5. Table `ports` (pour analyses spatiales)
```sql
CREATE TABLE ports (
    id SERIAL PRIMARY KEY,
    port_name VARCHAR(200) NOT NULL,
    port_code VARCHAR(10) UNIQUE,
    country_code VARCHAR(3),
    port_location GEOGRAPHY(Point, 4326),
    port_zone_radius_km DECIMAL(6,2) DEFAULT 5.0,
    port_type VARCHAR(50), -- 'commercial', 'fishing', 'passenger', 'military'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_ports_location ON ports USING GIST(port_location);
```

### � PRIORITÉ MOYENNE (suite)

#### 6. Table `ml_models` (pour tracking des modèles ML)
```sql
CREATE TABLE ml_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50), -- 'anomaly_detection', 'clustering', 'prediction', 'classification'
    version VARCHAR(20) NOT NULL,
    file_path VARCHAR(500), -- Chemin vers le fichier .pkl/.h5
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'deprecated', 'testing'
    accuracy DECIMAL(5,4),
    metrics JSONB, -- Métriques d'évaluation (precision, recall, etc.)
    training_date TIMESTAMP NOT NULL,
    n_samples_trained INTEGER,
    features_used TEXT[],
    description TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_name, version)
);
CREATE INDEX idx_ml_models_type ON ml_models(model_type);
CREATE INDEX idx_ml_models_status ON ml_models(status);
```

### �🟢 PRIORITÉ BASSE (Future)

#### 7. Table `traffic_density_grid` (pour visualisations)
```sql
CREATE TABLE traffic_density_grid (
    id SERIAL PRIMARY KEY,
    h3_index VARCHAR(20) UNIQUE, -- Hexagone H3
    cell_geom GEOGRAPHY(Polygon, 4326),
    vessel_count INTEGER,
    avg_vessels_per_hour DECIMAL(8,2),
    dominant_vessel_type INTEGER,
    last_updated TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_density_h3 ON traffic_density_grid(h3_index);
```

---

## 📝 RECOMMANDATIONS DE DÉVELOPPEMENT

### Phase 1 (1-2 semaines) - ETL Robuste
1. ✅ **Compléter l'ETL de base** (déjà bien avancé!)
2. ➕ Ajouter `transform_gap_detection.py`
3. ➕ Ajouter `transform_feature_engineering.py`
4. ➕ Créer tables `vessel_statistics` + `position_gaps`
5. ➕ Ajouter pipeline `calculate-statistics` dans `pipelines.yaml`

### Phase 2 (2-3 semaines) - Analyses Spatiales
1. 📓 Créer notebooks analyses spatiales
2. 🗄️ Créer table `ports`
3. 📓 Notebooks proximité portuaire
4. 📓 Notebooks trajectoires avancées

### Phase 3 (2-4 semaines) - ML & Routes
1. 📓 Notebooks clustering avancé
2. 🗄️ Créer table `maritime_routes`
3. 📓 Notebooks anomaly detection
4. 🗄️ Créer table `vessel_anomaly_score`

### Phase 4 (3-4 semaines) - Prédictions
1. 📓 Notebooks LSTM/prédictions
2. 📓 Notebooks forecast trafic
3. 🗄️ Tables prédictions si nécessaire

---

## 🎯 PIPELINES À AJOUTER DANS `pipelines.yaml`

```yaml
calculate-statistics:
  desc: "Calculate vessel statistics and gaps"
  steps:
    - func: get_vessels_with_positions  # Nouvelle fonction
      kwargs: {}
    - func: calculate_ais_gaps
      kwargs:
        gap_threshold_hours: 4
    - func: calculate_movement_features
      kwargs: {}
    - func: calculate_vessel_statistics
      kwargs: {}
    - func: load_vessel_statistics
      kwargs: {}
    - func: load_position_gaps
      kwargs: {}

enrich-positions:
  desc: "Enrich positions with calculated features"
  steps:
    - func: extract_data_from_file
      kwargs:
        selected_map: ["mmsi","base_date_time","lon","lat","sog","cog","heading","status"]
    - func: normalize_ais
      kwargs: {}
    - func: calculate_movement_features
      kwargs: {}
    - func: calculate_acceleration
      kwargs: {}
    - func: load_enriched_positions
      kwargs: {}

detect-anomalies:
  desc: "Detect anomalies in vessel behavior (batch)"
  steps:
    - func: get_recent_positions
      kwargs:
        days: 7
    - func: calculate_anomaly_scores
      kwargs: {}
    - func: load_anomaly_scores
      kwargs: {}
```

---

## 📊 STRUCTURE FINALE RECOMMANDÉE

```
etl/etl/
├── extract/
│   ✅ extract_ais.py
│   ✅ AISDownloader.py
│
├── transform/
│   ✅ transform_general_ais.py
│   ✅ transform_ais_cleanup.py
│   ✅ transform_vessel_delta.py
│   ✅ transform_vessel_duplication.py
│   ✅ transform_vessel_position.py
│   ✅ transform_ais_downsampling.py
│   ➕ transform_gap_detection.py        # À CRÉER
│   ➕ transform_feature_engineering.py  # À CRÉER
│   ➕ transform_status_validation.py    # À CRÉER
│   ➕ transform_anomaly_detection.py    # À CRÉER (future)
│
├── load/
│   ✅ load_vessel_db.py
│   ✅ load_positions_db.py
│   ✅ generate_vessel_type.py
│   ➕ load_statistics_db.py             # À CRÉER
│   ➕ load_gaps_db.py                   # À CRÉER
│   ➕ load_anomalies_db.py              # À CRÉER (future)
│
└── models/
    ✅ context.py

notebooks/
├── ✅ data_quality_gps_cleaning.ipynb
├── ✅ data_quality_speed_outliers.ipynb
├── ✅ terrestrial_positions_detection.ipynb
├── ✅ trajectoire_bateau.ipynb
├── ✅ clustering_analysis.ipynb
├── ➕ spatial_analysis_zones.ipynb          # À CRÉER
├── ➕ port_proximity_analysis.ipynb         # À CRÉER
├── ➕ trajectory_analysis_advanced.ipynb    # À CRÉER
├── ➕ temporal_patterns_analysis.ipynb      # À CRÉER
├── ➕ gap_statistics_analysis.ipynb         # À CRÉER
├── ➕ vessel_type_behavior_analysis.ipynb   # À CRÉER
├── ➕ anomaly_detection_ml.ipynb            # À CRÉER
├── ➕ route_extraction_clustering.ipynb     # À CRÉER
└── ➕ prediction_trajectory.ipynb           # À CRÉER
```

---

## 🎓 RÈGLES DE DÉCISION

### ➡️ Mettre dans l'ETL (.py) si:
- ✅ Traitement répétitif/automatisable
- ✅ Besoin de performance (traitement bulk)
- ✅ Partie du pipeline de production
- ✅ Transformation des données brutes
- ✅ Calculs nécessaires pour tous les navires

### ➡️ Mettre dans Notebook (.ipynb) si:
- ✅ Analyse exploratoire
- ✅ Visualisations complexes
- ✅ Expérimentation ML
- ✅ Analyses ponctuelles
- ✅ Prototypage d'algorithmes
- ✅ Reporting/Documentation

### ➡️ Créer une table BD si:
- ✅ Données réutilisées fréquemment
- ✅ Besoin d'indexation/performance
- ✅ Données de référence (ports, routes)
- ✅ Historique de calculs (statistics, anomalies)
- ✅ Jointures SQL nécessaires

### ➡️ NE PAS créer de table si:
- ✅ Résultats temporaires/exploratoires
- ✅ Agrégations à la volée suffisantes
- ✅ Données qui changent souvent
- ✅ Analyses ponctuelles/reporting

---

## 🚀 QUICK START - Prochaines Étapes

### 📦 PHASE 1: ETL Robuste (Semaine 1-2)

**Backend ETL (`/etl/etl/`):**
1. ✏️ Créer `transform_gap_detection.py`
2. ✏️ Créer `transform_feature_engineering.py`
3. ✏️ Créer `load_statistics_db.py`
4. 🗄️ Créer migration SQL: `V10__create_vessel_statistics.sql`
5. 🗄️ Créer migration SQL: `V11__create_position_gaps.sql`
6. ⚙️ Ajouter pipeline `calculate-statistics` dans `pipelines.yaml`
7. ✅ Tester le nouveau pipeline

**Résultat:** Statistiques calculées automatiquement et stockées en BD

---

### 🗺️ PHASE 2: Analyses Spatiales (Semaine 3-4)

**Notebooks (`/notebooks/`):**
1. 📓 Créer `spatial_analysis_zones.ipynb` - Heatmaps & densité
2. 📓 Créer `port_proximity_analysis.ipynb` - Analyse ports
3. 📓 Créer `trajectory_analysis_advanced.ipynb` - Trajectoires détaillées

**Base de données:**
4. 🗄️ Créer migration SQL: `V12__create_ports.sql`
5. 📥 Peupler table `ports` avec données principales (top 50 ports)

**Résultat:** Visualisations spatiales + données ports disponibles

---

### 🎯 PHASE 3: Backend API pour le Site (Semaine 5-6)

**Backend Services (`/backend/src/.../services/`):**
1. ✏️ Créer `StatisticsService.java` (ou `.py`)
2. ✏️ Créer `TrajectoryService.java`
3. ✏️ Créer `RouteService.java`
4. ✏️ Créer `FilterService.java`
5. ✏️ Créer `PortService.java`

**Backend Controllers/API (`/backend/src/.../controllers/`):**
6. ✏️ Créer `StatisticsController.java` - Endpoints `/api/statistics/*`
7. ✏️ Créer `TrajectoryController.java` - Endpoints `/api/trajectory/*`
8. ✏️ Créer `RouteController.java` - Endpoints `/api/routes/*`
9. ✏️ Créer `FilterController.java` - Endpoints `/api/search/*`

**Résultat:** API REST fonctionnelle pour servir le frontend

---

### 🎨 PHASE 4: Frontend Site Web (Semaine 7-9)

**Frontend Components (`/frontend/src/components/`):**
1. ✏️ Créer `MapView.jsx` - Carte principale
2. ✏️ Créer `TrafficHeatmap.jsx` - Heatmap
3. ✏️ Créer `VesselFilterPanel.jsx` - Filtres
4. ✏️ Créer `GlobalStatsCard.jsx` - Stats globales
5. ✏️ Créer `VesselTable.jsx` - Table navires
6. ✏️ Créer `VesselDetailModal.jsx` - Détails navire

**Frontend Pages (`/frontend/src/pages/`):**
7. ✏️ Créer `Dashboard.jsx` - Page accueil
8. ✏️ Créer `MapExplorer.jsx` - Carte interactive
9. ✏️ Créer `Statistics.jsx` - Page stats

**Frontend Services (`/frontend/src/services/`):**
10. ✏️ Créer `vesselService.js` - API calls
11. ✏️ Créer `statisticsService.js` - API calls

**Résultat:** Site web fonctionnel avec carte et statistiques

---

### 🤖 PHASE 5: Machine Learning (Mois 3-4)

**Notebooks ML (`/notebooks/`):**
1. 📓 Créer `anomaly_detection_ml.ipynb`
2. 📓 Créer `route_extraction_clustering.ipynb`
3. 📓 Créer `prediction_trajectory.ipynb`

**Base de données:**
4. 🗄️ Créer `V13__create_maritime_routes.sql`
5. 🗄️ Créer `V14__create_vessel_anomaly_score.sql`

**Backend Services ML:**
6. ✏️ Créer `AnomalyService.java`
7. ✏️ Créer `PredictionService.java`
8. ✏️ Créer `AnomalyController.java`

**Frontend ML:**
9. ✏️ Créer `AnomalyList.jsx`
10. ✏️ Créer `PredictionLayer.jsx`
11. ✏️ Créer page `Anomalies.jsx`

**Résultat:** Détection anomalies + prédictions disponibles sur le site

---

## 📋 CHECKLIST COMPLÈTE PAR COMPOSANT

### ✅ ETL (Production Data Pipeline)
- [x] Extract + Transform + Load (déjà fait!)
- [ ] Gap detection (à créer)
- [ ] Feature engineering (à créer)
- [ ] Statistics calculation (à créer)

### ✅ Base de Données
- [x] Tables principales (vessel, position_vessel)
- [ ] vessel_statistics (à créer)
- [ ] position_gaps (à créer)
- [ ] ports (à créer)
- [ ] maritime_routes (à créer - future)
- [ ] vessel_anomaly_score (à créer - future)

### ✅ Backend API (Services + Controllers)
- [ ] StatisticsService + Controller (à créer)
- [ ] TrajectoryService + Controller (à créer)
- [ ] RouteService + Controller (à créer)
- [ ] FilterService + Controller (à créer)
- [ ] PortService + Controller (à créer)
- [ ] AnomalyService + Controller (à créer - future)
- [ ] PredictionService + Controller (à créer - future)

### ✅ Frontend (React/Vue Components)
- [ ] Composants Carte (MapView, Heatmap, etc.) (à créer)
- [ ] Composants Filtres (FilterPanel, etc.) (à créer)
- [ ] Composants Stats (Charts, Cards, etc.) (à créer)
- [ ] Composants Tables/Listes (à créer)
- [ ] Pages principales (Dashboard, Map, Stats) (à créer)
- [ ] Services API (vesselService.js, etc.) (à créer)

### ✅ Notebooks (Analyse & Prototypage)
- [x] Data quality (déjà fait!)
- [x] Clustering basique (déjà fait!)
- [ ] Analyses spatiales avancées (à créer)
- [ ] Analyses temporelles (à créer)
- [ ] ML avancé (anomalies, prédictions) (à créer - future)

---

## 🎯 PRIORITÉS RECOMMANDÉES

### 🔴 PRIORITÉ 1 (Faire d'abord)
1. Compléter ETL (gaps + features)
2. Créer tables `vessel_statistics` + `position_gaps`
3. Créer backend services de base (Statistics, Trajectory)
4. Créer API endpoints essentiels
5. Créer frontend carte + filtres basiques

### 🟡 PRIORITÉ 2 (Ensuite)
1. Notebooks analyses spatiales
2. Table `ports` + PortService
3. RouteService + extraction routes
4. Frontend avancé (stats, trajectoires)
5. Composants visualisation

### 🟢 PRIORITÉ 3 (Plus tard)
1. ML anomalies
2. Prédictions trajectoires
3. Frontend pages ML
4. Optimisations performances
5. Features avancées

---

## 📊 RÉSUMÉ STRUCTURE COMPLÈTE

```
Projet AIS/
│
├── etl/                          # Pipeline ETL
│   ├── etl/
│   │   ├── extract/              ✅ Fait
│   │   ├── transform/            🔴 À compléter (gaps, features)
│   │   └── load/                 🔴 À compléter (statistics)
│   └── pipelines.yaml            🔴 À enrichir
│
├── backend/                      # API REST
│   └── src/.../
│       ├── services/             🔴 À créer (7 services)
│       └── controllers/          🔴 À créer (7+ controllers)
│
├── frontend/                     # Site Web React
│   └── src/
│       ├── components/           🔴 À créer (20+ composants)
│       ├── pages/                🔴 À créer (7 pages)
│       └── services/             🔴 À créer (5 services API)
│
├── notebooks/                    # Analyses & ML
│   ├── ✅ data_quality_*.ipynb  (fait)
│   ├── ✅ clustering_*.ipynb    (fait)
│   ├── 🟡 spatial_*.ipynb       (à créer)
│   ├── 🟡 temporal_*.ipynb      (à créer)
│   └── 🟢 ml_*.ipynb            (à créer - future)
│
└── db/migrations/                # Base de données
    ├── ✅ V1-V9 (fait)
    ├── 🔴 V10-V12 (priorité)
    └── 🟢 V13-V14 (future)
```

---

**Bon développement! 🚀**

**Prochaine action recommandée:** Commencer par créer `transform_gap_detection.py` dans `/etl/etl/transform/`

---

## 🔄 WORKFLOW COMPLET: DU NOTEBOOK À LA PRODUCTION

### Étape 1: Développement dans Notebook (Local)
```
notebooks/anomaly_detection_ml.ipynb
├── 1. Exploration des données
├── 2. Feature engineering
├── 3. Entraînement modèle (Isolation Forest)
├── 4. Évaluation (accuracy, precision, recall)
├── 5. ✅ SAUVEGARDER modèle
│   └── joblib.dump(model, "../models/anomaly_detection/isolation_forest_v1.pkl")
└── 6. ✅ SAUVEGARDER metadata + features
```

### Étape 2: Enregistrer le Modèle en BD
```python
# Dans le notebook, après sauvegarde du modèle

from utils.db import get_session

with get_session() as session:
    session.execute("""
        INSERT INTO ml_models (
            model_name, model_type, version, file_path,
            status, accuracy, metrics, training_date,
            n_samples_trained, features_used, description
        ) VALUES (
            'Isolation Forest Anomaly Detection',
            'anomaly_detection',
            '1.0',
            '../models/anomaly_detection/isolation_forest_v1.pkl',
            'active',
            0.95,
            '{"precision": 0.93, "recall": 0.97}'::jsonb,
            NOW(),
            50000,
            ARRAY['sog', 'cog', 'delta_time', 'distance_km', 'speed_kmh'],
            'Détection anomalies basée sur comportement navigation'
        )
    """)
    session.commit()
```

### Étape 3: Charger le Modèle dans le Backend
```python
# /backend/src/services/MLModelService.py

class MLModelService:
    def get_active_models_from_db(self):
        """Récupérer liste des modèles actifs depuis BD"""
        with get_session() as session:
            results = session.execute("""
                SELECT model_name, model_type, version, file_path, metrics
                FROM ml_models
                WHERE status = 'active'
            """).fetchall()
        
        return results
    
    def auto_load_models(self):
        """Charger automatiquement tous les modèles actifs au démarrage"""
        models = self.get_active_models_from_db()
        
        for model_info in models:
            model_type = model_info['model_type']
            
            if model_type == 'anomaly_detection':
                self.load_anomaly_detection_model()
            elif model_type == 'trajectory_prediction':
                self.load_trajectory_prediction_model()
            # etc.
        
        print(f"✅ {len(models)} modèles chargés avec succès!")
```

### Étape 4: Exposer via API REST
```python
# /backend/src/controllers/PredictionController.py

ml_service = MLModelService()
ml_service.auto_load_models()  # Au démarrage de l'app

@app.route('/api/predict/anomaly', methods=['POST'])
def predict_anomaly():
    """Endpoint accessible par le frontend"""
    data = request.json
    result = ml_service.predict_anomaly(data)
    return jsonify(result)
```

### Étape 5: Consommer depuis le Frontend
```javascript
// /frontend/src/services/predictionService.js

export const checkVesselAnomaly = async (vesselData) => {
  const response = await fetch('/api/predict/anomaly', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      mmsi: vesselData.mmsi,
      sog: vesselData.sog,
      cog: vesselData.cog,
      delta_time: vesselData.delta_time,
      distance_km: vesselData.distance_km,
      speed_kmh: vesselData.speed_kmh
    })
  });
  
  return await response.json();
  // { is_anomaly: true, anomaly_score: -0.15, severity: 'high' }
};
```

```jsx
// /frontend/src/components/VesselDetailModal.jsx

import { checkVesselAnomaly } from '../services/predictionService';

const VesselDetailModal = ({ vessel }) => {
  const [anomalyResult, setAnomalyResult] = useState(null);
  
  useEffect(() => {
    checkVesselAnomaly(vessel).then(setAnomalyResult);
  }, [vessel]);
  
  return (
    <div>
      <h2>Navire {vessel.mmsi}</h2>
      
      {anomalyResult?.is_anomaly && (
        <Alert severity="warning">
          ⚠️ Comportement anormal détecté!
          Score: {anomalyResult.anomaly_score}
        </Alert>
      )}
      
      {/* Reste des infos navire */}
    </div>
  );
};
```

### 🔄 Cycle de Vie Complet

```
┌─────────────────────────────────────────────────────────────┐
│ 1. NOTEBOOK (Développement)                                  │
│    - Exploration données                                     │
│    - Entraînement modèle                                     │
│    - Évaluation                                              │
│    - ✅ Sauvegarde modèle (.pkl/.h5)                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. BASE DE DONNÉES                                           │
│    - Enregistrement metadata dans table ml_models           │
│    - Versioning des modèles                                  │
│    - Tracking des performances                               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. BACKEND SERVICE                                           │
│    - MLModelService charge modèles au démarrage             │
│    - Modèles en mémoire pour inférence rapide               │
│    - Cache des prédictions fréquentes                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. API REST                                                  │
│    - Endpoints /api/predict/*                                │
│    - Validation des inputs                                   │
│    - Rate limiting                                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. FRONTEND                                                  │
│    - Composants React consomment API                         │
│    - Visualisation résultats prédictions                     │
│    - Alertes en temps réel                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ CHECKLIST MISE EN PRODUCTION ML

### Pour chaque modèle ML entraîné:

- [ ] ✅ Sauvegarder modèle (.pkl/.h5/.pth)
- [ ] ✅ Sauvegarder scaler/encoders
- [ ] ✅ Sauvegarder feature_names.json
- [ ] ✅ Sauvegarder metadata.json (accuracy, date, etc.)
- [ ] ✅ Enregistrer dans table `ml_models`
- [ ] ✅ Créer méthode `load_xxx_model()` dans MLModelService
- [ ] ✅ Créer méthode `predict_xxx()` dans MLModelService
- [ ] ✅ Créer endpoint API `/api/predict/xxx`
- [ ] ✅ Tester endpoint avec Postman/curl
- [ ] ✅ Créer service frontend `xxxService.js`
- [ ] ✅ Intégrer dans composants React
- [ ] ✅ Documenter l'API (Swagger)
- [ ] ✅ Monitoring des performances en production

---

**🎯 RÉSULTAT FINAL:** Tous vos modèles ML entraînés dans les notebooks seront **automatiquement utilisables** par tous les utilisateurs via le site web ! 🚀

---

## 📊 ANALYSES & FILTRES: QUI FAIT QUOI?

### 🎯 RÈGLE GÉNÉRALE

**Il y a DEUX types d'analyses :**

1. **Analyses EXPLORATOIRES** (Notebooks) - Pour comprendre les données
2. **Analyses OPÉRATIONNELLES** (Backend) - Pour servir les utilisateurs du site

---

### 📓 ANALYSES DANS NOTEBOOKS (Exploration uniquement)

**À faire dans les notebooks** :
- 🔍 **Exploration initiale** des données (voir patterns, tendances)
- 📈 **Visualisations complexes** pour comprendre (graphiques avancés)
- 🧪 **Prototypage** d'analyses avant de les coder en backend
- 📊 **Rapports ponctuels** (ex: rapport mensuel pour présentation)
- 🔬 **Analyses de recherche** (nouvelles métriques, expérimentations)

**Exemples concrets** :
```python
# temporal_patterns_analysis.ipynb

# ✅ Analyse exploratoire - RESTER DANS NOTEBOOK
# Comprendre les patterns horaires/journaliers
hourly_traffic = df.groupby(df['base_date_time'].dt.hour)['mmsi'].count()
plt.plot(hourly_traffic)  # Visualisation pour VOUS comprendre

# ✅ Identifier tendances saisonnières
monthly_stats = df.groupby(df['base_date_time'].dt.month).agg({...})
sns.heatmap(monthly_stats)  # Exploration visuelle

# ✅ Analyser distribution vitesses par type
speed_by_type = df.groupby('vessel_type_id')['sog'].describe()
# → Vous découvrez que les tankers vont en moyenne à 12 nœuds
```

**💡 SI l'analyse est utile → LA CODER EN BACKEND pour les utilisateurs !**

---

### 🖥️ ANALYSES DANS BACKEND (Pour les utilisateurs)

**À coder en backend** :
- 🎯 **Statistiques en temps réel** affichées sur le site
- 🔎 **Filtres et recherches** que les utilisateurs peuvent utiliser
- 📊 **Dashboards et graphiques** du site web
- 🗺️ **Données pour la carte** (heatmaps, trajectoires, etc.)
- 📈 **Analyses standardisées** (stats par navire, par zone, par type)

---

### 🔄 WORKFLOW: DU NOTEBOOK AU BACKEND

#### Étape 1: Exploration dans Notebook

```python
# notebooks/vessel_behavior_analysis.ipynb

# Vous découvrez une analyse intéressante:
# "Temps moyen passé en zone portuaire par type de navire"

port_time_by_type = df[df['in_port'] == True].groupby('vessel_type_id').agg({
    'base_date_time': lambda x: (x.max() - x.min()).total_seconds() / 3600
}).mean()

# Résultat: 
# - Cargo: 18h en moyenne au port
# - Tanker: 24h en moyenne
# - Passenger: 6h en moyenne
# → C'est intéressant pour les utilisateurs! ✅
```

#### Étape 2: Coder en Backend Service

```python
# /backend/src/services/AnalysisService.py

class AnalysisService:
    
    def get_port_time_by_vessel_type(self, port_id=None, date_range=None):
        """
        Calculer temps moyen au port par type de navire
        
        Returns:
            {
                "70": {"vessel_type": "Cargo", "avg_hours": 18.5, "count": 1250},
                "80": {"vessel_type": "Tanker", "avg_hours": 24.2, "count": 850},
                ...
            }
        """
        query = """
            WITH port_visits AS (
                SELECT 
                    v.vessel_type_id,
                    vt.vessel_group,
                    pv.vessel_id,
                    MIN(pv.base_date_time) as entry_time,
                    MAX(pv.base_date_time) as exit_time,
                    EXTRACT(EPOCH FROM (MAX(pv.base_date_time) - MIN(pv.base_date_time)))/3600 as hours_in_port
                FROM position_vessel pv
                JOIN vessel v ON v.id = pv.vessel_id
                JOIN vessel_type vt ON vt.id = v.vessel_type_id
                WHERE ST_DWithin(pv.geom, 
                    (SELECT port_location FROM ports WHERE id = :port_id), 
                    5000)  -- 5km du port
                GROUP BY v.vessel_type_id, vt.vessel_group, pv.vessel_id
            )
            SELECT 
                vessel_type_id,
                vessel_group,
                AVG(hours_in_port) as avg_hours,
                COUNT(*) as visit_count
            FROM port_visits
            GROUP BY vessel_type_id, vessel_group
            ORDER BY avg_hours DESC
        """
        
        with get_session() as session:
            results = session.execute(text(query), {"port_id": port_id}).fetchall()
        
        return {
            str(r['vessel_type_id']): {
                "vessel_type": r['vessel_group'],
                "avg_hours": round(r['avg_hours'], 2),
                "count": r['visit_count']
            }
            for r in results
        }
    
    def get_traffic_by_hour(self, date_range=None):
        """Distribution horaire du trafic"""
        query = """
            SELECT 
                EXTRACT(HOUR FROM base_date_time) as hour,
                COUNT(DISTINCT vessel_id) as vessel_count,
                COUNT(*) as position_count
            FROM position_vessel
            WHERE base_date_time >= :start_date 
              AND base_date_time <= :end_date
            GROUP BY EXTRACT(HOUR FROM base_date_time)
            ORDER BY hour
        """
        # ...
    
    def get_speed_distribution_by_type(self, vessel_type_id=None):
        """Distribution vitesses par type"""
        query = """
            SELECT 
                v.vessel_type_id,
                vt.vessel_group,
                AVG(pv.sog) as avg_speed,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pv.sog) as median_speed,
                MAX(pv.sog) as max_speed,
                MIN(pv.sog) as min_speed
            FROM position_vessel pv
            JOIN vessel v ON v.id = pv.vessel_id
            JOIN vessel_type vt ON vt.id = v.vessel_type_id
            WHERE pv.sog > 0
            GROUP BY v.vessel_type_id, vt.vessel_group
        """
        # ...
    
    def get_zone_statistics(self, bbox):
        """Stats d'une zone géographique"""
        query = """
            SELECT 
                COUNT(DISTINCT pv.vessel_id) as unique_vessels,
                COUNT(*) as total_positions,
                AVG(pv.sog) as avg_speed,
                COUNT(DISTINCT v.vessel_type_id) as vessel_types_count
            FROM position_vessel pv
            JOIN vessel v ON v.id = pv.vessel_id
            WHERE ST_Within(pv.geom, ST_MakeEnvelope(:minlon, :minlat, :maxlon, :maxlat, 4326))
        """
        # ...
```

#### Étape 3: Exposer via API

```python
# /backend/src/controllers/AnalysisController.py

from services.AnalysisService import AnalysisService

analysis_service = AnalysisService()

@app.route('/api/analysis/port-time-by-type', methods=['GET'])
def get_port_time_by_type():
    """
    GET /api/analysis/port-time-by-type?port_id=5
    
    Response:
    {
        "70": {"vessel_type": "Cargo", "avg_hours": 18.5, "count": 1250},
        "80": {"vessel_type": "Tanker", "avg_hours": 24.2, "count": 850}
    }
    """
    port_id = request.args.get('port_id')
    result = analysis_service.get_port_time_by_vessel_type(port_id)
    return jsonify(result)

@app.route('/api/analysis/traffic-by-hour', methods=['GET'])
def get_traffic_by_hour():
    """Distribution horaire du trafic"""
    date_range = {
        'start': request.args.get('start_date'),
        'end': request.args.get('end_date')
    }
    result = analysis_service.get_traffic_by_hour(date_range)
    return jsonify(result)

@app.route('/api/analysis/speed-distribution', methods=['GET'])
def get_speed_distribution():
    """Distribution vitesses par type"""
    vessel_type = request.args.get('vessel_type_id')
    result = analysis_service.get_speed_distribution_by_type(vessel_type)
    return jsonify(result)

@app.route('/api/analysis/zone-stats', methods=['POST'])
def get_zone_stats():
    """
    POST /api/analysis/zone-stats
    Body: {"bbox": [minLon, minLat, maxLon, maxLat]}
    """
    bbox = request.json.get('bbox')
    result = analysis_service.get_zone_statistics(bbox)
    return jsonify(result)
```

#### Étape 4: Consommer dans Frontend

```javascript
// /frontend/src/services/analysisService.js

export const getPortTimeByType = async (portId) => {
  const response = await fetch(`/api/analysis/port-time-by-type?port_id=${portId}`);
  return await response.json();
};

export const getTrafficByHour = async (startDate, endDate) => {
  const response = await fetch(
    `/api/analysis/traffic-by-hour?start_date=${startDate}&end_date=${endDate}`
  );
  return await response.json();
};

export const getZoneStatistics = async (bounds) => {
  const response = await fetch('/api/analysis/zone-stats', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bbox: bounds })
  });
  return await response.json();
};
```

```jsx
// /frontend/src/components/PortStatsChart.jsx

import { getPortTimeByType } from '../services/analysisService';
import { BarChart, Bar, XAxis, YAxis } from 'recharts';

const PortStatsChart = ({ portId }) => {
  const [data, setData] = useState([]);
  
  useEffect(() => {
    getPortTimeByType(portId).then(result => {
      const chartData = Object.values(result).map(item => ({
        type: item.vessel_type,
        hours: item.avg_hours,
        count: item.count
      }));
      setData(chartData);
    });
  }, [portId]);
  
  return (
    <div>
      <h3>Temps moyen au port par type de navire</h3>
      <BarChart width={600} height={300} data={data}>
        <XAxis dataKey="type" />
        <YAxis label="Heures" />
        <Bar dataKey="hours" fill="#8884d8" />
      </BarChart>
    </div>
  );
};
```

---

### 🔎 FILTRES: TOUJOURS DANS LE BACKEND

**Tous les filtres doivent être dans le backend** pour permettre aux utilisateurs de les utiliser.

#### Backend: FilterService

```python
# /backend/src/services/FilterService.py

class FilterService:
    
    def filter_vessels(self, filters):
        """
        Filtrer navires selon critères multiples
        
        Args:
            filters: {
                "vessel_types": [70, 71, 72],  # Types de navires
                "min_speed": 5.0,              # Vitesse min (nœuds)
                "max_speed": 20.0,             # Vitesse max
                "min_length": 50,              # Longueur min (m)
                "max_length": 300,
                "in_zone": {                    # Dans zone géographique
                    "type": "bbox",
                    "coords": [minLon, minLat, maxLon, maxLat]
                },
                "date_range": {
                    "start": "2024-01-01",
                    "end": "2024-12-31"
                },
                "has_anomaly": True,            # Avec anomalies détectées
                "status": [0, 1, 5]             # Statuts navigation
            }
        
        Returns:
            Liste de navires correspondant aux critères
        """
        
        # Construction requête SQL dynamique
        query = """
            SELECT DISTINCT 
                v.id, v.mmsi, v.vessel_name, v.vessel_type_id,
                vt.vessel_group, v.length, v.width,
                pv.sog, pv.cog, pv.base_date_time,
                ST_Y(pv.geom::geometry) as lat,
                ST_X(pv.geom::geometry) as lon
            FROM vessel v
            JOIN vessel_type vt ON vt.id = v.vessel_type_id
            LEFT JOIN LATERAL (
                SELECT * FROM position_vessel 
                WHERE vessel_id = v.id 
                ORDER BY base_date_time DESC 
                LIMIT 1
            ) pv ON true
            WHERE 1=1
        """
        
        params = {}
        
        # Filtre types
        if filters.get('vessel_types'):
            query += " AND v.vessel_type_id = ANY(:vessel_types)"
            params['vessel_types'] = filters['vessel_types']
        
        # Filtre vitesse
        if filters.get('min_speed') is not None:
            query += " AND pv.sog >= :min_speed"
            params['min_speed'] = filters['min_speed']
        
        if filters.get('max_speed') is not None:
            query += " AND pv.sog <= :max_speed"
            params['max_speed'] = filters['max_speed']
        
        # Filtre dimensions
        if filters.get('min_length'):
            query += " AND v.length >= :min_length"
            params['min_length'] = filters['min_length']
        
        # Filtre zone géographique
        if filters.get('in_zone'):
            zone = filters['in_zone']
            if zone['type'] == 'bbox':
                query += """ AND ST_Within(pv.geom, 
                    ST_MakeEnvelope(:minlon, :minlat, :maxlon, :maxlat, 4326))
                """
                params.update({
                    'minlon': zone['coords'][0],
                    'minlat': zone['coords'][1],
                    'maxlon': zone['coords'][2],
                    'maxlat': zone['coords'][3]
                })
        
        # Filtre date
        if filters.get('date_range'):
            query += " AND pv.base_date_time BETWEEN :start_date AND :end_date"
            params['start_date'] = filters['date_range']['start']
            params['end_date'] = filters['date_range']['end']
        
        # Filtre anomalies
        if filters.get('has_anomaly'):
            query += """
                AND EXISTS (
                    SELECT 1 FROM vessel_anomaly_score vas
                    WHERE vas.vessel_id = v.id
                      AND vas.severity IN ('high', 'critical')
                      AND vas.detection_date >= CURRENT_DATE - INTERVAL '7 days'
                )
            """
        
        # Exécuter requête
        with get_session() as session:
            results = session.execute(text(query), params).fetchall()
        
        return [dict(row) for row in results]
    
    def get_vessels_in_port(self, port_id, radius_km=5):
        """Navires actuellement dans un port"""
        # ...
    
    def get_vessels_on_route(self, route_id):
        """Navires sur une route maritime spécifique"""
        # ...
```

#### API Endpoint pour Filtres

```python
@app.route('/api/vessels/filter', methods=['POST'])
def filter_vessels():
    """
    POST /api/vessels/filter
    
    Body:
    {
        "vessel_types": [70, 71, 72],
        "min_speed": 5.0,
        "max_speed": 20.0,
        "in_zone": {
            "type": "bbox",
            "coords": [-5.5, 48.0, -5.0, 48.5]
        }
    }
    
    Response:
    [
        {
            "mmsi": 123456789,
            "vessel_name": "CARGO SHIP",
            "vessel_type": "Cargo",
            "sog": 12.5,
            "lat": 48.25,
            "lon": -5.25
        },
        ...
    ]
    """
    filters = request.json
    results = filter_service.filter_vessels(filters)
    
    return jsonify({
        "count": len(results),
        "vessels": results
    })
```

#### Frontend: Panel de Filtres

```jsx
// /frontend/src/components/VesselFilterPanel.jsx

const VesselFilterPanel = ({ onFilterChange }) => {
  const [filters, setFilters] = useState({
    vessel_types: [],
    min_speed: 0,
    max_speed: 50,
    min_length: 0,
    has_anomaly: false
  });
  
  const applyFilters = async () => {
    const response = await fetch('/api/vessels/filter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filters)
    });
    
    const data = await response.json();
    onFilterChange(data.vessels);
  };
  
  return (
    <div className="filter-panel">
      <h3>Filtres</h3>
      
      <div>
        <label>Types de navires:</label>
        <MultiSelect
          options={[
            {value: 70, label: 'Cargo'},
            {value: 80, label: 'Tanker'},
            {value: 60, label: 'Passenger'}
          ]}
          value={filters.vessel_types}
          onChange={(val) => setFilters({...filters, vessel_types: val})}
        />
      </div>
      
      <div>
        <label>Vitesse (nœuds):</label>
        <RangeSlider
          min={0}
          max={50}
          value={[filters.min_speed, filters.max_speed]}
          onChange={([min, max]) => setFilters({
            ...filters,
            min_speed: min,
            max_speed: max
          })}
        />
      </div>
      
      <div>
        <label>
          <input
            type="checkbox"
            checked={filters.has_anomaly}
            onChange={(e) => setFilters({
              ...filters,
              has_anomaly: e.target.checked
            })}
          />
          Avec anomalies détectées
        </label>
      </div>
      
      <button onClick={applyFilters}>
        Appliquer les filtres
      </button>
    </div>
  );
};
```

---

### 📊 TABLEAU RÉCAPITULATIF

| Type d'analyse | Où la faire | Pourquoi | Exemple |
|---|---|---|---|
| **Exploration initiale** | 📓 Notebook | Comprendre les données | "Quelle est la distribution des vitesses?" |
| **Visualisations complexes** | 📓 Notebook | Graphiques avancés pour analyse | Heatmap corrélations, clustering 3D |
| **Prototypage analyse** | 📓 Notebook | Tester avant de coder en backend | Test de nouvelles métriques |
| **Rapports ponctuels** | 📓 Notebook | Présentation, rapport mensuel | Rapport stats du mois |
| **Statistiques temps réel** | 🖥️ Backend | Affichage sur le site | "3,542 navires actifs aujourd'hui" |
| **Filtres utilisateurs** | 🖥️ Backend | Recherche interactive | "Montrer cargos > 200m" |
| **Graphiques du site** | 🖥️ Backend | Dashboard utilisateur | Chart trafic par heure |
| **Données pour carte** | 🖥️ Backend | Affichage carte interactive | Heatmap densité trafic |
| **Analyses standardisées** | 🖥️ Backend | API pour utilisateurs | Stats par navire/zone |

---

### ✅ CHECKLIST: QUELLE APPROCHE CHOISIR?

**Faites dans un NOTEBOOK si** :
- ✅ C'est pour VOUS comprendre les données
- ✅ C'est une analyse ponctuelle (rapport, présentation)
- ✅ Vous expérimentez de nouvelles métriques
- ✅ Visualisations complexes pour exploration
- ✅ Prototypage avant implémentation backend

**Codez dans le BACKEND si** :
- ✅ Les utilisateurs doivent y avoir accès
- ✅ C'est un filtre ou une recherche
- ✅ Ça doit s'afficher sur le site web
- ✅ Besoin de temps réel / actualisation
- ✅ Besoin de performance (SQL optimisé)

---

## 🎯 RÉSUMÉ FINAL COMPLET

```
📓 NOTEBOOKS          →  🖥️ BACKEND SERVICE    →  🌐 API REST         →  🎨 FRONTEND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. MODÈLES ML          → MLModelService        → /api/predict/*     → Alertes anomalies
   (entraînement)        (.load_models())         (prédictions)        Prédictions carte

2. ANALYSES            → AnalysisService       → /api/analysis/*    → Graphiques stats
   (exploration)         (.get_statistics())      (stats/metrics)      Dashboards

3. FILTRES             → FilterService         → /api/vessels/      → Panel de filtres
   (prototypage)         (.filter_vessels())      filter               Recherche avancée

4. CLUSTERING          → RouteService          → /api/routes/*      → Routes sur carte
   (extraction routes)   (.get_routes())          (corridors)          Zones de trafic
```

**🚀 TOUT est accessible aux utilisateurs du site !**
