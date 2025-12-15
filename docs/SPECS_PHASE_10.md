# Spécifications Techniques - Phase 10 : Analyse Environnementale

> **Objectif** : Estimer impact environnemental du trafic maritime (émissions, consommation, pollution)
> **Durée estimée** : 3-4 semaines
> **Priorité** : ⭐⭐⭐ HAUTE (Réglementation environnementale)

---

## 📋 Vue d'ensemble

Cette phase implémente des modèles d'estimation de l'impact environnemental du trafic maritime : calcul émissions CO2/NOx/SOx, consommation carburant, efficacité énergétique, respect zones protégées. Focus sur conformité réglementations IMO et identification opportunités optimisation.

**Prérequis** :
- Phases 1-9 complétées
- Données trajectoires enrichies
- Caractéristiques navires (dimensions, type, motorisation)
- Zones géographiques définies
- Zones marines protégées (AMP)

**Objectifs** :
- Estimation émissions CO2, NOx, SOx par navire
- Calcul consommation carburant
- Score efficacité énergétique (EEOI, CII)
- Détection passages zones protégées
- Recommandations optimisation
- Conformité IMO 2023+ regulations

**Réglementations** :
- **IMO MARPOL Annex VI** : émissions atmosphériques
- **CII (Carbon Intensity Indicator)** : rating A-E depuis 2023
- **EEOI (Energy Efficiency Operational Indicator)**
- **ECA (Emission Control Areas)** : zones basse émission
- **Zones SECA** : SOx < 0.1%
- **Aires Marines Protégées** : restrictions navigation

**Technologies** :
- **Python** : calculs scientifiques
- **NumPy/Pandas** : manipulation données
- **SciPy** : modèles physiques
- **Geopandas** : zones géographiques
- **PostgreSQL/PostGIS** : géo-requêtes
- **Matplotlib/Plotly** : visualisations

---

## 10.1 Estimation Émissions

### 10.1.1 Modèle consommation carburant par type

**Objectif** : Estimer consommation fuel selon caractéristiques navire

**Fonctionnalités** :
- Modèles consommation par type navire
- Paramètres : puissance moteur, vitesse, charge
- Formules IMO/MEPC
- Ajustement conditions réelles
- Validation données AIS

**Technologies** :
- **Modèles physiques** : lois puissance/vitesse
- **Regression** : calibration paramètres
- **Marine engineering formulas**
- **IMO guidelines** : Fourth IMO GHG Study

**Bases théoriques** :

**1. Puissance requise (Admiralty formula)**
```
P = (Displacement^(2/3) × Speed^3) / C
```
- P : Puissance (kW)
- Displacement : Déplacement navire (tonnes)
- Speed : Vitesse (nœuds)
- C : Constante Admiralty (type navire)

**2. Consommation fuel**
```
FC = P × SFOC × t
```
- FC : Fuel Consumption (tonnes)
- P : Puissance (kW)
- SFOC : Specific Fuel Oil Consumption (g/kWh)
- t : Temps (heures)

**Paramètres par type navire** :

```python
# Constantes Admiralty par type
ADMIRALTY_CONSTANTS = {
    'Cargo': 500,
    'Container': 550,
    'Tanker': 450,
    'Bulk Carrier': 400,
    'Passenger': 600,
    'Fishing': 350,
    'Tug': 300
}

# SFOC par type moteur (g/kWh)
SFOC_VALUES = {
    'Slow Speed Diesel': 170,    # 2-stroke (cargo, tanker)
    'Medium Speed Diesel': 190,  # 4-stroke (container, passenger)
    'High Speed Diesel': 210,    # petits navires
    'Steam Turbine': 250,        # anciens navires
    'Gas Turbine': 280          # ferries rapides
}

# Type moteur par vessel_type
ENGINE_TYPE_MAP = {
    'Cargo': 'Slow Speed Diesel',
    'Container': 'Medium Speed Diesel',
    'Tanker': 'Slow Speed Diesel',
    'Passenger': 'Medium Speed Diesel',
    'Fishing': 'High Speed Diesel'
}
```

**Implémentation modèle** :

```python
import numpy as np
import pandas as pd

class FuelConsumptionModel:
    """Modèle estimation consommation carburant"""
    
    def __init__(self):
        self.admiralty_constants = ADMIRALTY_CONSTANTS
        self.sfoc_values = SFOC_VALUES
        self.engine_map = ENGINE_TYPE_MAP
    
    def estimate_displacement(self, vessel_type, length, width, draft):
        """Estimer déplacement depuis dimensions"""
        # Formule approximative : Displacement ≈ L × W × D × Cb × ρ
        # Cb : Block coefficient (0.6-0.85 selon type)
        cb = self._get_block_coefficient(vessel_type)
        rho = 1.025  # Densité eau mer (t/m³)
        
        displacement = length * width * draft * cb * rho
        return displacement
    
    def _get_block_coefficient(self, vessel_type):
        """Coefficient de bloc par type"""
        cb_map = {
            'Cargo': 0.75,
            'Container': 0.65,
            'Tanker': 0.82,
            'Bulk Carrier': 0.85,
            'Passenger': 0.60,
            'Fishing': 0.55
        }
        return cb_map.get(vessel_type, 0.70)
    
    def calculate_power(self, displacement, speed_knots, vessel_type):
        """Calculer puissance requise (kW)"""
        c = self.admiralty_constants.get(vessel_type, 450)
        power_kw = (displacement**(2/3) * speed_knots**3) / c
        return power_kw
    
    def calculate_fuel_consumption(self, power_kw, time_hours, vessel_type):
        """Calculer consommation fuel (tonnes)"""
        engine_type = self.engine_map.get(vessel_type, 'Medium Speed Diesel')
        sfoc = self.sfoc_values[engine_type]  # g/kWh
        
        # FC (tonnes) = P (kW) × SFOC (g/kWh) × t (h) / 1e6
        fuel_tonnes = (power_kw * sfoc * time_hours) / 1e6
        return fuel_tonnes
    
    def estimate_voyage_fuel(self, trajectory_df, vessel_info):
        """Estimer consommation pour un voyage"""
        vessel_type = vessel_info['vessel_type']
        length = vessel_info['length']
        width = vessel_info['width']
        draft = vessel_info['draft']
        
        # Déplacement
        displacement = self.estimate_displacement(vessel_type, length, width, draft)
        
        # Calcul par segment
        fuel_total = 0
        for i in range(len(trajectory_df) - 1):
            sog = trajectory_df.iloc[i]['sog']  # nœuds
            
            # Delta temps
            t1 = trajectory_df.iloc[i]['base_date_time']
            t2 = trajectory_df.iloc[i+1]['base_date_time']
            delta_hours = (t2 - t1).total_seconds() / 3600
            
            # Puissance et fuel
            if sog > 1:  # Navire en mouvement
                power = self.calculate_power(displacement, sog, vessel_type)
                fuel_segment = self.calculate_fuel_consumption(
                    power, delta_hours, vessel_type
                )
                fuel_total += fuel_segment
        
        return fuel_total

# Utilisation
model = FuelConsumptionModel()

vessel_info = {
    'vessel_type': 'Container',
    'length': 300,
    'width': 40,
    'draft': 14
}

fuel_consumed = model.estimate_voyage_fuel(trajectory_df, vessel_info)
print(f"Fuel consumed: {fuel_consumed:.2f} tonnes")
```

**Modèle avancé avec charge** :

```python
def calculate_fuel_with_load(self, power_base, load_factor):
    """Ajuster consommation selon charge navire"""
    # load_factor : 0.0 (vide) à 1.0 (pleine charge)
    # Consommation augmente avec charge
    load_multiplier = 0.7 + (0.3 * load_factor)
    return power_base * load_multiplier
```

**Calibration avec données réelles** :

```python
from sklearn.linear_model import LinearRegression

class CalibratedFuelModel(FuelConsumptionModel):
    """Modèle calibré avec données réelles"""
    
    def __init__(self):
        super().__init__()
        self.calibration_model = None
    
    def calibrate(self, X_features, y_fuel_actual):
        """Calibrer avec fuel consumption réel"""
        # Features : [displacement, speed, time, vessel_type_encoded]
        self.calibration_model = LinearRegression()
        self.calibration_model.fit(X_features, y_fuel_actual)
    
    def predict_calibrated(self, features):
        """Prédiction calibrée"""
        if self.calibration_model is None:
            raise ValueError("Model not calibrated")
        return self.calibration_model.predict(features)
```

**Validation modèle** :

```python
def validate_fuel_estimates(estimated, actual):
    """Valider estimations vs consommations réelles"""
    from sklearn.metrics import mean_absolute_error, r2_score
    
    mae = mean_absolute_error(actual, estimated)
    mape = np.mean(np.abs((actual - estimated) / actual)) * 100
    r2 = r2_score(actual, estimated)
    
    print(f"MAE: {mae:.2f} tonnes")
    print(f"MAPE: {mape:.2f}%")
    print(f"R²: {r2:.3f}")
    
    # Plot
    import matplotlib.pyplot as plt
    plt.figure(figsize=(8, 6))
    plt.scatter(actual, estimated, alpha=0.5)
    plt.plot([0, max(actual)], [0, max(actual)], 'r--', label='Perfect')
    plt.xlabel('Actual Fuel (tonnes)')
    plt.ylabel('Estimated Fuel (tonnes)')
    plt.title('Fuel Consumption Validation')
    plt.legend()
    plt.show()
```

**Livrables** :
- Classe FuelConsumptionModel : `fuel_model.py`
- Paramètres calibrés : `config/fuel_parameters.json`
- Table : `fuel_consumption_estimates`
- Validation report : `reports/fuel_model_validation.pdf`
- Notebook : `notebooks/fuel_consumption_analysis.ipynb`

---

### 10.1.2 Calculer émissions CO2 par navire

**Objectif** : Calculer émissions CO2 depuis consommation fuel

**Fonctionnalités** :
- Conversion fuel → CO2
- Facteurs émission par type fuel
- Émissions totales par navire/voyage
- Time-series émissions
- Agrégations spatiales

**Facteurs émission CO2** :

```python
# Facteurs émission CO2 (tonnes CO2 / tonne fuel)
# Source: IMO Fourth GHG Study 2020
CO2_EMISSION_FACTORS = {
    'HFO': 3.114,      # Heavy Fuel Oil
    'MDO': 3.206,      # Marine Diesel Oil
    'MGO': 3.206,      # Marine Gas Oil
    'LNG': 2.750,      # Liquefied Natural Gas
    'Methanol': 1.375,
    'LPG': 3.000
}

# Type fuel par vessel type (défaut)
DEFAULT_FUEL_TYPE = {
    'Cargo': 'HFO',
    'Container': 'HFO',
    'Tanker': 'HFO',
    'Bulk Carrier': 'HFO',
    'Passenger': 'MDO',
    'Fishing': 'MGO',
    'Tug': 'MGO'
}
```

**Calcul émissions CO2** :

```python
class CO2EmissionCalculator:
    """Calculateur émissions CO2"""
    
    def __init__(self):
        self.emission_factors = CO2_EMISSION_FACTORS
        self.default_fuels = DEFAULT_FUEL_TYPE
    
    def calculate_co2(self, fuel_consumed_tonnes, fuel_type='HFO'):
        """Calculer émissions CO2"""
        factor = self.emission_factors.get(fuel_type, 3.114)
        co2_tonnes = fuel_consumed_tonnes * factor
        return co2_tonnes
    
    def calculate_voyage_co2(self, trajectory_df, vessel_info, fuel_model):
        """Calculer CO2 pour un voyage"""
        # Consommation fuel
        fuel_consumed = fuel_model.estimate_voyage_fuel(trajectory_df, vessel_info)
        
        # Type fuel
        vessel_type = vessel_info['vessel_type']
        fuel_type = vessel_info.get('fuel_type') or self.default_fuels.get(vessel_type, 'HFO')
        
        # Émissions CO2
        co2_tonnes = self.calculate_co2(fuel_consumed, fuel_type)
        
        return {
            'fuel_consumed_tonnes': fuel_consumed,
            'fuel_type': fuel_type,
            'co2_emissions_tonnes': co2_tonnes,
            'distance_nm': self._calculate_distance(trajectory_df),
            'duration_hours': self._calculate_duration(trajectory_df)
        }
    
    def _calculate_distance(self, trajectory_df):
        """Distance parcourue (nautical miles)"""
        from geopy.distance import geodesic
        
        total_distance = 0
        for i in range(len(trajectory_df) - 1):
            coord1 = (trajectory_df.iloc[i]['latitude'], trajectory_df.iloc[i]['longitude'])
            coord2 = (trajectory_df.iloc[i+1]['latitude'], trajectory_df.iloc[i+1]['longitude'])
            distance_km = geodesic(coord1, coord2).kilometers
            distance_nm = distance_km / 1.852
            total_distance += distance_nm
        
        return total_distance
    
    def _calculate_duration(self, trajectory_df):
        """Durée voyage (heures)"""
        t_start = trajectory_df.iloc[0]['base_date_time']
        t_end = trajectory_df.iloc[-1]['base_date_time']
        duration = (t_end - t_start).total_seconds() / 3600
        return duration

# Utilisation
co2_calc = CO2EmissionCalculator()

emissions_data = co2_calc.calculate_voyage_co2(
    trajectory_df,
    vessel_info,
    fuel_model
)

print(f"CO2 emissions: {emissions_data['co2_emissions_tonnes']:.2f} tonnes")
print(f"Distance: {emissions_data['distance_nm']:.1f} nm")
print(f"Duration: {emissions_data['duration_hours']:.1f} hours")
```

**Émissions par segment** :

```python
def calculate_co2_by_segment(self, trajectory_df, vessel_info, fuel_model):
    """CO2 par segment trajectoire"""
    segments = []
    
    for i in range(len(trajectory_df) - 1):
        segment_df = trajectory_df.iloc[i:i+2]
        
        # Fuel pour ce segment
        fuel_seg = fuel_model.estimate_voyage_fuel(segment_df, vessel_info)
        
        # CO2
        fuel_type = vessel_info.get('fuel_type', 'HFO')
        co2_seg = self.calculate_co2(fuel_seg, fuel_type)
        
        segments.append({
            'segment_id': i,
            'lat_start': trajectory_df.iloc[i]['latitude'],
            'lon_start': trajectory_df.iloc[i]['longitude'],
            'lat_end': trajectory_df.iloc[i+1]['latitude'],
            'lon_end': trajectory_df.iloc[i+1]['longitude'],
            'timestamp': trajectory_df.iloc[i]['base_date_time'],
            'fuel_tonnes': fuel_seg,
            'co2_tonnes': co2_seg
        })
    
    return pd.DataFrame(segments)
```

**Agrégations** :

```python
# Par navire
def aggregate_by_vessel(emissions_df):
    """Agrégation par navire"""
    return emissions_df.groupby('vessel_id').agg({
        'co2_tonnes': 'sum',
        'fuel_tonnes': 'sum',
        'distance_nm': 'sum',
        'duration_hours': 'sum'
    }).reset_index()

# Par zone géographique
def aggregate_by_zone(emissions_df, grid_size=0.1):
    """Agrégation par zone géographique"""
    # Créer grille
    emissions_df['lat_bin'] = (emissions_df['latitude'] // grid_size) * grid_size
    emissions_df['lon_bin'] = (emissions_df['longitude'] // grid_size) * grid_size
    
    return emissions_df.groupby(['lat_bin', 'lon_bin']).agg({
        'co2_tonnes': 'sum',
        'fuel_tonnes': 'sum'
    }).reset_index()

# Par période temporelle
def aggregate_by_period(emissions_df, freq='D'):
    """Agrégation temporelle"""
    emissions_df.set_index('timestamp', inplace=True)
    return emissions_df.resample(freq).agg({
        'co2_tonnes': 'sum',
        'fuel_tonnes': 'sum',
        'vessel_id': 'nunique'
    })
```

**Time-series émissions** :

```python
def create_emission_timeseries(vessel_id, start_date, end_date):
    """Série temporelle émissions navire"""
    query = f"""
    SELECT 
        DATE_TRUNC('day', base_date_time) as date,
        SUM(co2_emissions) as daily_co2,
        SUM(fuel_consumption) as daily_fuel,
        COUNT(*) as positions
    FROM emission_estimates
    WHERE vessel_id = {vessel_id}
      AND base_date_time BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY date
    ORDER BY date
    """
    
    df = pd.read_sql(query, db_connection)
    
    # Plot
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    ax[0].plot(df['date'], df['daily_co2'], marker='o')
    ax[0].set_ylabel('CO2 Emissions (tonnes)')
    ax[0].set_title(f'Daily CO2 Emissions - Vessel {vessel_id}')
    ax[0].grid(True)
    
    ax[1].plot(df['date'], df['daily_fuel'], marker='s', color='orange')
    ax[1].set_ylabel('Fuel Consumption (tonnes)')
    ax[1].set_xlabel('Date')
    ax[1].grid(True)
    
    plt.tight_layout()
    plt.show()
    
    return df
```

**Livrables** :
- Classe CO2EmissionCalculator : `co2_calculator.py`
- Table : `co2_emissions_by_vessel`
- Table : `co2_emissions_by_segment`
- Dashboard : `dashboards/emissions_monitoring.html`
- Rapport : `reports/fleet_emissions_report.pdf`

---

### 10.1.3 Calculer émissions totales par zone

**Objectif** : Cartographier émissions CO2 spatiales

**Fonctionnalités** :
- Grille spatiale émissions
- Heatmap CO2 par zone
- Identification hotspots pollution
- Évolution temporelle zones
- Comparaison zones réglementées

**Implémentation** :

```python
import geopandas as gpd
from shapely.geometry import Point, Polygon
import numpy as np

class SpatialEmissionAnalyzer:
    """Analyse spatiale émissions"""
    
    def __init__(self, grid_size_deg=0.1):
        self.grid_size = grid_size_deg
    
    def create_grid(self, bounds):
        """Créer grille spatiale"""
        # bounds : (min_lon, min_lat, max_lon, max_lat)
        min_lon, min_lat, max_lon, max_lat = bounds
        
        # Grille
        lons = np.arange(min_lon, max_lon, self.grid_size)
        lats = np.arange(min_lat, max_lat, self.grid_size)
        
        cells = []
        for lon in lons:
            for lat in lats:
                # Polygone cellule
                cell_poly = Polygon([
                    (lon, lat),
                    (lon + self.grid_size, lat),
                    (lon + self.grid_size, lat + self.grid_size),
                    (lon, lat + self.grid_size)
                ])
                cells.append({
                    'geometry': cell_poly,
                    'lon': lon,
                    'lat': lat,
                    'cell_id': f"{lat:.2f}_{lon:.2f}"
                })
        
        return gpd.GeoDataFrame(cells, crs='EPSG:4326')
    
    def aggregate_emissions_to_grid(self, emissions_df, grid_gdf):
        """Agréger émissions sur grille"""
        # Créer GeoDataFrame positions
        geometry = [Point(xy) for xy in zip(emissions_df['longitude'], emissions_df['latitude'])]
        emissions_gdf = gpd.GeoDataFrame(emissions_df, geometry=geometry, crs='EPSG:4326')
        
        # Spatial join
        joined = gpd.sjoin(emissions_gdf, grid_gdf, how='left', predicate='within')
        
        # Agrégation par cellule
        grid_emissions = joined.groupby('cell_id').agg({
            'co2_tonnes': 'sum',
            'fuel_tonnes': 'sum',
            'vessel_id': 'nunique'
        }).reset_index()
        
        # Merger avec grille
        grid_gdf = grid_gdf.merge(grid_emissions, on='cell_id', how='left')
        grid_gdf.fillna(0, inplace=True)
        
        return grid_gdf
    
    def create_emission_heatmap(self, grid_gdf, output_file='emission_heatmap.html'):
        """Créer heatmap interactive"""
        import folium
        from folium.plugins import HeatMap
        
        # Préparer données heatmap
        heat_data = []
        for idx, row in grid_gdf.iterrows():
            if row['co2_tonnes'] > 0:
                centroid = row['geometry'].centroid
                heat_data.append([
                    centroid.y,
                    centroid.x,
                    float(row['co2_tonnes'])
                ])
        
        # Carte
        center_lat = grid_gdf.geometry.centroid.y.mean()
        center_lon = grid_gdf.geometry.centroid.x.mean()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
        
        # Heatmap
        HeatMap(
            heat_data,
            min_opacity=0.3,
            max_zoom=13,
            radius=15,
            blur=25,
            gradient={
                0.0: 'blue',
                0.5: 'yellow',
                0.7: 'orange',
                1.0: 'red'
            }
        ).add_to(m)
        
        # Sauvegarder
        m.save(output_file)
        print(f"Heatmap saved to {output_file}")
        
        return m
    
    def identify_hotspots(self, grid_gdf, threshold_percentile=90):
        """Identifier zones forte émission"""
        threshold = grid_gdf['co2_tonnes'].quantile(threshold_percentile / 100)
        
        hotspots = grid_gdf[grid_gdf['co2_tonnes'] >= threshold].copy()
        hotspots = hotspots.sort_values('co2_tonnes', ascending=False)
        
        print(f"Identified {len(hotspots)} hotspots (>{threshold:.2f} tonnes CO2)")
        print("\nTop 10 hotspots:")
        print(hotspots[['cell_id', 'co2_tonnes', 'vessel_id']].head(10))
        
        return hotspots

# Utilisation
analyzer = SpatialEmissionAnalyzer(grid_size_deg=0.1)

# Bounds zone d'intérêt
bounds = (-5.5, 47.0, 1.5, 51.0)  # Exemple: Manche

# Créer grille
grid_gdf = analyzer.create_grid(bounds)

# Agréger émissions
grid_emissions = analyzer.aggregate_emissions_to_grid(emissions_df, grid_gdf)

# Heatmap
analyzer.create_emission_heatmap(grid_emissions, 'co2_heatmap_channel.html')

# Hotspots
hotspots = analyzer.identify_hotspots(grid_emissions, threshold_percentile=95)
```

**Analyse temporelle zones** :

```python
def analyze_zone_emission_trends(zone_polygon, emissions_df, freq='M'):
    """Analyser évolution émissions zone"""
    # Filtrer positions dans zone
    geometry = [Point(xy) for xy in zip(emissions_df['longitude'], emissions_df['latitude'])]
    gdf = gpd.GeoDataFrame(emissions_df, geometry=geometry, crs='EPSG:4326')
    
    zone_emissions = gdf[gdf.within(zone_polygon)]
    
    # Agrégation temporelle
    zone_emissions.set_index('timestamp', inplace=True)
    trend = zone_emissions.resample(freq).agg({
        'co2_tonnes': 'sum',
        'vessel_id': 'nunique'
    })
    
    # Plot
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(trend.index, trend['co2_tonnes'], marker='o', linewidth=2)
    ax.set_xlabel('Period')
    ax.set_ylabel('CO2 Emissions (tonnes)')
    ax.set_title('CO2 Emissions Trend in Zone')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    return trend
```

**Comparaison zones** :

```python
def compare_zones(zones_dict, emissions_df):
    """Comparer émissions entre zones"""
    results = []
    
    for zone_name, zone_polygon in zones_dict.items():
        # Filtrer
        geometry = [Point(xy) for xy in zip(emissions_df['longitude'], emissions_df['latitude'])]
        gdf = gpd.GeoDataFrame(emissions_df, geometry=geometry, crs='EPSG:4326')
        zone_data = gdf[gdf.within(zone_polygon)]
        
        # Statistiques
        results.append({
            'zone': zone_name,
            'total_co2_tonnes': zone_data['co2_tonnes'].sum(),
            'avg_co2_per_vessel': zone_data.groupby('vessel_id')['co2_tonnes'].sum().mean(),
            'n_vessels': zone_data['vessel_id'].nunique(),
            'area_km2': zone_polygon.area * 111**2  # Approx deg² to km²
        })
    
    comparison_df = pd.DataFrame(results)
    comparison_df['co2_density'] = comparison_df['total_co2_tonnes'] / comparison_df['area_km2']
    
    return comparison_df.sort_values('total_co2_tonnes', ascending=False)
```

**Livrables** :
- Classe SpatialEmissionAnalyzer : `spatial_emissions.py`
- Grille émissions : `grids/emission_grid.geojson`
- Heatmaps : `maps/co2_heatmap_*.html`
- Hotspots analysis : `reports/emission_hotspots.pdf`
- Table : `spatial_emissions_grid`

---

### 10.1.4 Identifier navires les plus polluants

**Objectif** : Ranking navires par émissions CO2

**Fonctionnalités** :
- Top pollueurs absolus (tonnes CO2)
- Top pollueurs relatifs (CO2/distance)
- Comparaison vs moyenne type
- Évolution dans temps
- Identification opportunités optimisation

**Implémentation** :

```python
class VesselEmissionRanking:
    """Ranking navires par émissions"""
    
    def __init__(self, emissions_df):
        self.emissions_df = emissions_df
    
    def rank_absolute_emissions(self, top_n=50):
        """Top pollueurs absolus"""
        ranking = self.emissions_df.groupby('vessel_id').agg({
            'co2_tonnes': 'sum',
            'fuel_tonnes': 'sum',
            'distance_nm': 'sum',
            'duration_hours': 'sum',
            'vessel_type': 'first',
            'vessel_name': 'first'
        }).reset_index()
        
        ranking = ranking.sort_values('co2_tonnes', ascending=False)
        ranking['rank'] = range(1, len(ranking) + 1)
        
        return ranking.head(top_n)
    
    def rank_relative_emissions(self, top_n=50):
        """Top pollueurs relatifs (CO2 intensity)"""
        ranking = self.emissions_df.groupby('vessel_id').agg({
            'co2_tonnes': 'sum',
            'distance_nm': 'sum',
            'vessel_type': 'first',
            'vessel_name': 'first'
        }).reset_index()
        
        # CO2 intensity (grammes CO2 par tonne-mile)
        # Pour simplifier: grammes CO2 par nautical mile
        ranking['co2_per_nm'] = (ranking['co2_tonnes'] * 1e6) / ranking['distance_nm']
        
        ranking = ranking[ranking['distance_nm'] > 100]  # Minimum distance
        ranking = ranking.sort_values('co2_per_nm', ascending=False)
        ranking['rank'] = range(1, len(ranking) + 1)
        
        return ranking.head(top_n)
    
    def compare_to_fleet_average(self, vessel_id):
        """Comparer navire à moyenne flotte son type"""
        # Données navire
        vessel_data = self.emissions_df[self.emissions_df['vessel_id'] == vessel_id]
        vessel_type = vessel_data['vessel_type'].iloc[0]
        vessel_co2_total = vessel_data['co2_tonnes'].sum()
        vessel_distance = vessel_data['distance_nm'].sum()
        vessel_co2_per_nm = vessel_co2_total / vessel_distance if vessel_distance > 0 else 0
        
        # Moyenne type
        type_data = self.emissions_df[self.emissions_df['vessel_type'] == vessel_type]
        type_avg_co2 = type_data.groupby('vessel_id')['co2_tonnes'].sum().mean()
        type_avg_distance = type_data.groupby('vessel_id')['distance_nm'].sum().mean()
        type_avg_co2_per_nm = type_avg_co2 / type_avg_distance if type_avg_distance > 0 else 0
        
        # Comparaison
        ratio_absolute = vessel_co2_total / type_avg_co2 if type_avg_co2 > 0 else 0
        ratio_intensity = vessel_co2_per_nm / type_avg_co2_per_nm if type_avg_co2_per_nm > 0 else 0
        
        result = {
            'vessel_id': vessel_id,
            'vessel_type': vessel_type,
            'vessel_co2_total': vessel_co2_total,
            'vessel_co2_per_nm': vessel_co2_per_nm,
            'type_avg_co2': type_avg_co2,
            'type_avg_co2_per_nm': type_avg_co2_per_nm,
            'ratio_vs_avg_absolute': ratio_absolute,
            'ratio_vs_avg_intensity': ratio_intensity,
            'performance': self._classify_performance(ratio_intensity)
        }
        
        return result
    
    def _classify_performance(self, ratio):
        """Classifier performance environnementale"""
        if ratio < 0.8:
            return 'Excellent'
        elif ratio < 0.95:
            return 'Good'
        elif ratio < 1.05:
            return 'Average'
        elif ratio < 1.2:
            return 'Below Average'
        else:
            return 'Poor'
    
    def identify_improvement_opportunities(self, threshold_ratio=1.2):
        """Identifier navires avec opportunités amélioration"""
        opportunities = []
        
        for vessel_id in self.emissions_df['vessel_id'].unique():
            comparison = self.compare_to_fleet_average(vessel_id)
            
            if comparison['ratio_vs_avg_intensity'] > threshold_ratio:
                # Calcul potentiel économies
                current_co2 = comparison['vessel_co2_total']
                target_co2 = comparison['type_avg_co2']
                potential_reduction = current_co2 - target_co2
                
                opportunities.append({
                    'vessel_id': vessel_id,
                    'vessel_type': comparison['vessel_type'],
                    'current_co2_tonnes': current_co2,
                    'target_co2_tonnes': target_co2,
                    'potential_reduction_tonnes': potential_reduction,
                    'reduction_percent': (potential_reduction / current_co2 * 100) if current_co2 > 0 else 0,
                    'performance_ratio': comparison['ratio_vs_avg_intensity']
                })
        
        opportunities_df = pd.DataFrame(opportunities)
        opportunities_df = opportunities_df.sort_values('potential_reduction_tonnes', ascending=False)
        
        return opportunities_df
    
    def create_ranking_visualization(self, top_n=20):
        """Visualisation ranking"""
        import matplotlib.pyplot as plt
        
        # Top absolute
        top_absolute = self.rank_absolute_emissions(top_n)
        
        # Top relative
        top_relative = self.rank_relative_emissions(top_n)
        
        # Plot
        fig, axes = plt.subplots(1, 2, figsize=(16, 8))
        
        # Absolute
        axes[0].barh(range(len(top_absolute)), top_absolute['co2_tonnes'], color='steelblue')
        axes[0].set_yticks(range(len(top_absolute)))
        axes[0].set_yticklabels([f"{row['vessel_name'][:20]}" for _, row in top_absolute.iterrows()], fontsize=8)
        axes[0].set_xlabel('Total CO2 Emissions (tonnes)')
        axes[0].set_title(f'Top {top_n} Absolute Emitters')
        axes[0].invert_yaxis()
        
        # Relative
        axes[1].barh(range(len(top_relative)), top_relative['co2_per_nm'], color='coral')
        axes[1].set_yticks(range(len(top_relative)))
        axes[1].set_yticklabels([f"{row['vessel_name'][:20]}" for _, row in top_relative.iterrows()], fontsize=8)
        axes[1].set_xlabel('CO2 Intensity (g/nm)')
        axes[1].set_title(f'Top {top_n} Relative Emitters')
        axes[1].invert_yaxis()
        
        plt.tight_layout()
        plt.savefig('vessel_emission_rankings.png', dpi=300, bbox_inches='tight')
        plt.show()

# Utilisation
ranker = VesselEmissionRanking(emissions_df)

# Top pollueurs
top_absolute = ranker.rank_absolute_emissions(top_n=50)
print("Top 10 absolute emitters:")
print(top_absolute[['rank', 'vessel_name', 'vessel_type', 'co2_tonnes']].head(10))

top_relative = ranker.rank_relative_emissions(top_n=50)
print("\nTop 10 relative emitters:")
print(top_relative[['rank', 'vessel_name', 'vessel_type', 'co2_per_nm']].head(10))

# Opportunités amélioration
opportunities = ranker.identify_improvement_opportunities(threshold_ratio=1.2)
print(f"\nIdentified {len(opportunities)} vessels with improvement opportunities")
print("Top 10 opportunities:")
print(opportunities[['vessel_id', 'vessel_type', 'potential_reduction_tonnes', 'reduction_percent']].head(10))

# Visualisation
ranker.create_ranking_visualization(top_n=20)
```

**Dashboard interactif** :

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_emission_dashboard(emissions_df):
    """Dashboard interactif émissions"""
    # Agrégation par navire
    vessel_stats = emissions_df.groupby(['vessel_id', 'vessel_name', 'vessel_type']).agg({
        'co2_tonnes': 'sum',
        'fuel_tonnes': 'sum',
        'distance_nm': 'sum'
    }).reset_index()
    
    vessel_stats['co2_per_nm'] = vessel_stats['co2_tonnes'] / vessel_stats['distance_nm']
    
    # Subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'CO2 Emissions by Vessel Type',
            'Top 10 Emitters',
            'CO2 Intensity Distribution',
            'Fuel vs CO2 Correlation'
        ),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'histogram'}, {'type': 'scatter'}]]
    )
    
    # 1. Emissions par type
    type_emissions = vessel_stats.groupby('vessel_type')['co2_tonnes'].sum().sort_values(ascending=False)
    fig.add_trace(
        go.Bar(x=type_emissions.index, y=type_emissions.values, name='CO2 by Type'),
        row=1, col=1
    )
    
    # 2. Top 10
    top10 = vessel_stats.nlargest(10, 'co2_tonnes')
    fig.add_trace(
        go.Bar(x=top10['vessel_name'], y=top10['co2_tonnes'], name='Top 10'),
        row=1, col=2
    )
    
    # 3. Distribution intensité
    fig.add_trace(
        go.Histogram(x=vessel_stats['co2_per_nm'], nbinsx=50, name='CO2 Intensity'),
        row=2, col=1
    )
    
    # 4. Fuel vs CO2
    fig.add_trace(
        go.Scatter(
            x=vessel_stats['fuel_tonnes'],
            y=vessel_stats['co2_tonnes'],
            mode='markers',
            text=vessel_stats['vessel_name'],
            name='Fuel vs CO2'
        ),
        row=2, col=2
    )
    
    fig.update_layout(height=800, showlegend=False, title_text="Fleet Emissions Dashboard")
    fig.write_html('fleet_emissions_dashboard.html')
    fig.show()
```

**Livrables** :
- Classe VesselEmissionRanking : `vessel_ranking.py`
- Rankings : `reports/top_emitters_*.csv`
- Opportunities : `reports/improvement_opportunities.csv`
- Dashboard : `dashboards/emission_rankings.html`
- Visualisations : `plots/vessel_rankings.png`

---

### 10.1.5 Comparer émissions par type navire

**Objectif** : Benchmark émissions entre types navires

**Implémentation** :

```python
class VesselTypeEmissionComparison:
    """Comparaison émissions par type"""
    
    def __init__(self, emissions_df):
        self.emissions_df = emissions_df
    
    def compare_types(self):
        """Statistiques par type"""
        comparison = self.emissions_df.groupby('vessel_type').agg({
            'vessel_id': 'nunique',
            'co2_tonnes': ['sum', 'mean', 'median', 'std'],
            'fuel_tonnes': ['sum', 'mean'],
            'distance_nm': ['sum', 'mean'],
            'duration_hours': ['sum', 'mean']
        }).reset_index()
        
        # Flatten columns
        comparison.columns = ['_'.join(col).strip('_') for col in comparison.columns.values]
        
        # CO2 intensity
        comparison['co2_intensity_g_per_nm'] = (
            comparison['co2_tonnes_sum'] * 1e6 / comparison['distance_nm_sum']
        )
        
        return comparison.sort_values('co2_tonnes_sum', ascending=False)
    
    def create_comparison_plots(self, comparison_df):
        """Visualisations comparaison"""
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Total CO2 par type
        axes[0, 0].bar(comparison_df['vessel_type'], comparison_df['co2_tonnes_sum'])
        axes[0, 0].set_xlabel('Vessel Type')
        axes[0, 0].set_ylabel('Total CO2 (tonnes)')
        axes[0, 0].set_title('Total CO2 Emissions by Type')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. CO2 moyen par navire
        axes[0, 1].bar(comparison_df['vessel_type'], comparison_df['co2_tonnes_mean'], color='orange')
        axes[0, 1].set_xlabel('Vessel Type')
        axes[0, 1].set_ylabel('Average CO2 per Vessel (tonnes)')
        axes[0, 1].set_title('Average CO2 Emissions per Vessel')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. CO2 intensity
        axes[1, 0].bar(comparison_df['vessel_type'], comparison_df['co2_intensity_g_per_nm'], color='green')
        axes[1, 0].set_xlabel('Vessel Type')
        axes[1, 0].set_ylabel('CO2 Intensity (g/nm)')
        axes[1, 0].set_title('CO2 Intensity by Type')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 4. Nombre navires
        axes[1, 1].bar(comparison_df['vessel_type'], comparison_df['vessel_id_nunique'], color='purple')
        axes[1, 1].set_xlabel('Vessel Type')
        axes[1, 1].set_ylabel('Number of Vessels')
        axes[1, 1].set_title('Fleet Size by Type')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('vessel_type_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()

# Utilisation
comparator = VesselTypeEmissionComparison(emissions_df)
comparison = comparator.compare_types()
print(comparison)
comparator.create_comparison_plots(comparison)
```

**Livrables** :
- Classe VesselTypeEmissionComparison : `type_comparison.py`
- Rapport comparatif : `reports/emission_by_type.pdf`
- Visualisations : `plots/type_comparison.png`

---

## 10.2 Efficacité Énergétique

### 10.2.1 Calculer ratio distance/vitesse optimale

**Objectif** : Identifier écarts à vitesse optimale consommation

**Théorie** :
- Consommation fuel ∝ Vitesse³
- Vitesse optimale : compromise temps/fuel
- Slow steaming : réduction vitesse → économies

**Implémentation** :

```python
class EnergyEfficiencyAnalyzer:
    """Analyse efficacité énergétique"""
    
    def __init__(self):
        # Vitesses optimales par type (nœuds)
        self.optimal_speeds = {
            'Cargo': 14,
            'Container': 18,
            'Tanker': 13,
            'Bulk Carrier': 13,
            'Passenger': 20,
            'Fishing': 10
        }
    
    def calculate_optimal_speed_deviation(self, trajectory_df, vessel_type):
        """Écart à vitesse optimale"""
        optimal_speed = self.optimal_speeds.get(vessel_type, 14)
        
        trajectory_df['speed_deviation'] = trajectory_df['sog'] - optimal_speed
        trajectory_df['speed_deviation_pct'] = (
            trajectory_df['speed_deviation'] / optimal_speed * 100
        )
        
        # Surconsommation estimée
        # Formule simplifiée : overconsumption ∝ (v_actual/v_optimal)³ - 1
        trajectory_df['overconsumption_factor'] = (
            (trajectory_df['sog'] / optimal_speed)**3 - 1
        )
        
        return trajectory_df
    
    def estimate_fuel_savings_potential(self, trajectory_df, vessel_type, fuel_model):
        """Potentiel économies en naviguant à vitesse optimale"""
        optimal_speed = self.optimal_speeds.get(vessel_type, 14)
        
        # Fuel consommé actuel
        actual_fuel = fuel_model.estimate_voyage_fuel(trajectory_df, vessel_info)
        
        # Fuel si vitesse optimale
        trajectory_optimal = trajectory_df.copy()
        trajectory_optimal['sog'] = optimal_speed
        optimal_fuel = fuel_model.estimate_voyage_fuel(trajectory_optimal, vessel_info)
        
        savings = actual_fuel - optimal_fuel
        savings_pct = (savings / actual_fuel * 100) if actual_fuel > 0 else 0
        
        return {
            'actual_fuel_tonnes': actual_fuel,
            'optimal_fuel_tonnes': optimal_fuel,
            'potential_savings_tonnes': savings,
            'potential_savings_pct': savings_pct,
            'actual_avg_speed': trajectory_df['sog'].mean(),
            'optimal_speed': optimal_speed
        }
```

**Livrables** :
- Classe EnergyEfficiencyAnalyzer : `energy_efficiency.py`
- Table : `speed_optimization_analysis`
- Rapport : `reports/fuel_savings_potential.pdf`

---

### 10.2.2 Score efficacité par navire (EEOI, CII)

**Objectif** : Calculer indicateurs réglementaires IMO

**EEOI (Energy Efficiency Operational Indicator)** :
```
EEOI = (Fuel Consumed × CO2 Factor) / (Cargo Carried × Distance)
Unit: grams CO2 per tonne-nautical mile
```

**CII (Carbon Intensity Indicator)** :
```
CII = CO2 Emissions / (Capacity × Distance)
Rating: A (best) to E (worst)
```

**Implémentation** :

```python
class IMOComplianceCalculator:
    """Calcul indicateurs IMO"""
    
    def __init__(self):
        self.co2_factors = CO2_EMISSION_FACTORS
    
    def calculate_eeoi(self, fuel_consumed, fuel_type, cargo_tonnes, distance_nm):
        """Calculate EEOI"""
        if cargo_tonnes == 0 or distance_nm == 0:
            return None
        
        co2_factor = self.co2_factors.get(fuel_type, 3.114)
        co2_tonnes = fuel_consumed * co2_factor
        
        eeoi = (co2_tonnes * 1e6) / (cargo_tonnes * distance_nm)  # g CO2 / tonne-nm
        
        return eeoi
    
    def calculate_cii(self, co2_tonnes, capacity_dwt, distance_nm, vessel_type):
        """Calculate CII"""
        if capacity_dwt == 0 or distance_nm == 0:
            return None
        
        cii = co2_tonnes / (capacity_dwt * distance_nm)
        
        # Rating
        rating = self._get_cii_rating(cii, vessel_type, capacity_dwt)
        
        return {
            'cii_value': cii,
            'cii_rating': rating
        }
    
    def _get_cii_rating(self, cii, vessel_type, capacity_dwt):
        """Déterminer rating CII (A-E)"""
        # Référence boundaries IMO (simplifiés)
        # Formule: CII_ref = a × capacity^(-c)
        
        # Paramètres par type (exemples)
        params = {
            'Cargo': {'a': 4745, 'c': 0.622},
            'Container': {'a': 1984, 'c': 0.489},
            'Tanker': {'a': 5247, 'c': 0.610},
            'Bulk Carrier': {'a': 4745, 'c': 0.622}
        }
        
        p = params.get(vessel_type, params['Cargo'])
        cii_ref = p['a'] * (capacity_dwt ** (-p['c']))
        
        # Thresholds (IMO 2023)
        ratio = cii / cii_ref
        
        if ratio < 0.86:
            return 'A'  # Major superior
        elif ratio < 0.94:
            return 'B'  # Minor superior
        elif ratio < 1.06:
            return 'C'  # Moderate
        elif ratio < 1.18:
            return 'D'  # Minor inferior
        else:
            return 'E'  # Inferior (action required)
    
    def calculate_vessel_scores(self, vessel_id, emissions_df, vessel_info):
        """Calculer tous scores pour un navire"""
        vessel_data = emissions_df[emissions_df['vessel_id'] == vessel_id]
        
        # Agrégation
        total_fuel = vessel_data['fuel_tonnes'].sum()
        total_co2 = vessel_data['co2_tonnes'].sum()
        total_distance = vessel_data['distance_nm'].sum()
        
        # EEOI (estimation cargo à 70% capacity)
        capacity_dwt = vessel_info.get('deadweight', 0)
        avg_cargo = capacity_dwt * 0.7
        fuel_type = vessel_info.get('fuel_type', 'HFO')
        
        eeoi = self.calculate_eeoi(total_fuel, fuel_type, avg_cargo, total_distance)
        
        # CII
        vessel_type = vessel_info['vessel_type']
        cii_result = self.calculate_cii(total_co2, capacity_dwt, total_distance, vessel_type)
        
        return {
            'vessel_id': vessel_id,
            'vessel_type': vessel_type,
            'eeoi': eeoi,
            'cii_value': cii_result['cii_value'] if cii_result else None,
            'cii_rating': cii_result['cii_rating'] if cii_result else None,
            'total_co2_tonnes': total_co2,
            'total_distance_nm': total_distance
        }

# Utilisation
imo_calc = IMOComplianceCalculator()

scores = imo_calc.calculate_vessel_scores(vessel_id, emissions_df, vessel_info)
print(f"EEOI: {scores['eeoi']:.2f} g CO2/tonne-nm")
print(f"CII Rating: {scores['cii_rating']}")
```

**Livrables** :
- Classe IMOComplianceCalculator : `imo_compliance.py`
- Table : `vessel_efficiency_scores`
- Dashboard : `dashboards/cii_ratings.html`
- Rapport conformité : `reports/imo_compliance_report.pdf`

---

## 10.3 Impact Environnemental

### 10.3.1 Identifier passages zones protégées

**Objectif** : Détecter navigations dans aires marines protégées

**Implémentation** :

```python
import geopandas as gpd

class ProtectedAreaAnalyzer:
    """Analyse passages zones protégées"""
    
    def __init__(self, mpa_shapefile):
        """Load Marine Protected Areas"""
        self.mpas = gpd.read_file(mpa_shapefile)
    
    def detect_mpa_passages(self, trajectory_df):
        """Détecter passages dans MPAs"""
        # Créer GeoDataFrame trajectoire
        geometry = [Point(xy) for xy in zip(trajectory_df['longitude'], trajectory_df['latitude'])]
        traj_gdf = gpd.GeoDataFrame(trajectory_df, geometry=geometry, crs='EPSG:4326')
        
        # Spatial join avec MPAs
        passages = gpd.sjoin(traj_gdf, self.mpas, how='inner', predicate='within')
        
        return passages
    
    def calculate_time_in_mpa(self, passages_df):
        """Temps passé dans chaque MPA"""
        mpa_stats = passages_df.groupby('mpa_name').agg({
            'base_date_time': ['min', 'max', 'count'],
            'vessel_id': 'first'
        }).reset_index()
        
        mpa_stats['duration_hours'] = (
            (mpa_stats[('base_date_time', 'max')] - mpa_stats[('base_date_time', 'min')])
            .dt.total_seconds() / 3600
        )
        
        return mpa_stats
```

**Livrables** :
- Classe ProtectedAreaAnalyzer : `protected_areas.py`
- Table : `mpa_passages`
- Carte passages : `maps/mpa_traffic.html`
- Rapport : `reports/mpa_compliance.pdf`

---

## 📊 Livrables Phase 10

### Modèles & Scripts
```
environmental/
├── fuel_model.py
├── co2_calculator.py
├── spatial_emissions.py
├── vessel_ranking.py
├── energy_efficiency.py
├── imo_compliance.py
├── protected_areas.py
└── emission_forecasting.py
```

### Tables PostgreSQL
```sql
fuel_consumption_estimates
co2_emissions_by_vessel
co2_emissions_by_segment
spatial_emissions_grid
vessel_efficiency_scores
mpa_passages
emission_hotspots
improvement_opportunities
```

### Rapports & Dashboards
```
reports/
├── fleet_emissions_report.pdf
├── top_emitters_ranking.pdf
├── fuel_savings_potential.pdf
├── imo_compliance_report.pdf
├── emission_hotspots.pdf
└── mpa_compliance.pdf

dashboards/
├── emissions_monitoring.html
├── emission_rankings.html
├── cii_ratings.html
└── environmental_impact.html
```

---

## ✅ Critères Validation Phase 10

1. ✅ **Modèles émissions**
   - Fuel consumption estimé
   - CO2 calculé par navire
   - Validation avec données réelles

2. ✅ **Analyses spatiales**
   - Heatmaps émissions
   - Hotspots identifiés
   - Zones protégées surveillées

3. ✅ **Indicateurs IMO**
   - EEOI calculé
   - CII ratings attribués
   - Conformité évaluée

4. ✅ **Optimisation**
   - Opportunités identifiées
   - Économies quantifiées
   - Recommandations fournies

5. ✅ **Rapports**
   - Dashboards déployés
   - Rapports automatisés
   - Alertes configurées

---

**Fin SPECS_PHASE_10.md**
