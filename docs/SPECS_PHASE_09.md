# Spécifications Techniques - Phase 9 : Deep Learning - Trajectoires

> **Objectif** : Implémenter modèles deep learning pour analyse et prédiction de trajectoires maritimes
> **Durée estimée** : 4-6 semaines
> **Priorité** : ⭐⭐⭐ HAUTE (Intelligence artificielle avancée)

---

## 📋 Vue d'ensemble

Cette phase implémente des architectures deep learning sophistiquées pour l'analyse séquentielle de trajectoires : LSTM pour la mémoire temporelle, CNN pour l'extraction de patterns, Transformers pour l'attention contextuelle. Focus sur prédiction de trajectoires, classification de comportements et génération de séquences.

**Prérequis** :
- Phase 8 complétée (ML Niveau 1)
- GPU recommandé (CUDA 11.x+)
- TensorFlow 2.13+ ou PyTorch 2.0+
- Données séquentielles préparées
- Features engineerées disponibles

**Objectifs** :
- Prédiction trajectoires futures (next positions)
- Classification comportements complexes
- Détection anomalies séquentielles
- Génération trajectoires réalistes
- Modèles state-of-the-art performances
- Explicabilité prédictions (attention)

**Technologies Deep Learning** :
- **TensorFlow/Keras 2.13+** ou **PyTorch 2.0+**
- **LSTM, GRU** : réseaux récurrents
- **CNN 1D/2D** : extraction features
- **Transformers** : attention mechanisms
- **Attention layers** : focus contextuel
- **Mixed Precision Training** : optimisation GPU
- **TensorBoard/Weights & Biases** : monitoring

**Infrastructure** :
- **GPU** : NVIDIA RTX/Tesla (8GB+ VRAM)
- **Batch processing** : DataLoader optimisés
- **Checkpointing** : sauvegarde progressive
- **Early stopping** : éviter overfitting
- **Learning rate scheduling** : convergence

---

## 9.1 Préparation Données Séquentielles

### 9.1.1 Extraction séquences temporelles par MMSI

**Objectif** : Construire dataset séquences trajectoires pour training

**Fonctionnalités** :
- Extraction trajectoires complètes par navire
- Segmentation voyages (port-to-port)
- Création sliding windows temporelles
- Gestion trajectoires variables longueur
- Indexation efficace séquences

**Technologies** :
- **Pandas** : manipulation dataframes
- **NumPy** : arrays séquences
- **SQL** : extraction optimisée
- **Dask** : parallélisation si gros volumes
- **HDF5/Parquet** : stockage efficace

**Extraction SQL** :
```sql
-- Trajectoires par navire ordonnées temporellement
SELECT 
    vessel_id,
    mmsi,
    base_date_time,
    latitude,
    longitude,
    sog,
    cog,
    heading,
    vessel_status_id,
    vessel_type_id,
    LAG(base_date_time) OVER (PARTITION BY vessel_id ORDER BY base_date_time) as prev_time,
    LAG(latitude) OVER (PARTITION BY vessel_id ORDER BY base_date_time) as prev_lat,
    LAG(longitude) OVER (PARTITION BY vessel_id ORDER BY base_date_time) as prev_lon
FROM position_vessel
WHERE is_valid = true
  AND base_date_time >= '2024-01-01'
ORDER BY vessel_id, base_date_time;
```

**Segmentation voyages** :
- Critère split : gap temporel > 4h
- Critère split : entrée/sortie port
- Critère split : changement statut majeur
- Minimum longueur : 10 positions
- Maximum longueur : 1000 positions (truncate)

**Features par position** :
1. **Spatiales** :
   - Latitude (normalized)
   - Longitude (normalized)
   - Distance depuis origine
   - Direction depuis origine
   
2. **Cinématiques** :
   - SOG (vitesse)
   - COG (cap)
   - Heading
   - Accélération (delta SOG)
   - Rate of turn (delta COG)
   
3. **Temporelles** :
   - Timestamp (Unix epoch normalized)
   - Hour of day (cyclique)
   - Day of week (cyclique)
   - Time delta depuis position précédente
   
4. **Contextuelles** :
   - Vessel type (embedding)
   - Status (embedding)
   - Distance côte
   - Distance port

**Structure séquence** :
```python
sequence = {
    'vessel_id': int,
    'mmsi': int,
    'sequence_id': str,  # vessel_id_voyage_num
    'length': int,       # nombre positions
    'timestamps': np.array([T]),
    'positions': np.array([T, 2]),  # lat, lon
    'features': np.array([T, F]),   # F features
    'labels': np.array([T]),        # pour supervised
    'metadata': dict                # type, dates, etc.
}
```

**Sliding windows** :
- Window size : 50-100 positions
- Stride : 10-25 positions (overlap)
- Prédiction horizon : 1-10 positions futures
- Contexte passé : window size positions

**Stockage** :
```python
# HDF5 pour grandes données
import h5py

with h5py.File('sequences_train.h5', 'w') as f:
    f.create_dataset('positions', data=positions_array, compression='gzip')
    f.create_dataset('features', data=features_array, compression='gzip')
    f.create_dataset('labels', data=labels_array, compression='gzip')
    f.create_dataset('metadata', data=metadata_array)
```

**Livrables** :
- Script extraction : `extract_sequences.py`
- Dataset train/val/test : HDF5 files
- Table : `trajectory_sequences`
- Statistiques dataset : notebook
- Index séquences : JSON manifest

---

### 9.1.2 Normalisation features (MinMaxScaler, StandardScaler)

**Objectif** : Preprocessing features pour convergence optimale

**Fonctionnalités** :
- Normalisation features numériques
- Encodage features catégorielles
- Features cycliques (heure, cap)
- Gestion valeurs manquantes
- Persistence scalers pour inference

**Technologies** :
- **scikit-learn** : StandardScaler, MinMaxScaler, RobustScaler
- **joblib** : sauvegarde scalers
- **NumPy** : transformations custom
- **Pipeline** : chaîne preprocessing

**Stratégies normalisation** :

**1. Features spatiales (lat/lon)**
```python
# MinMaxScaler [0, 1] ou [-1, 1]
from sklearn.preprocessing import MinMaxScaler

scaler_spatial = MinMaxScaler(feature_range=(-1, 1))
positions_norm = scaler_spatial.fit_transform(positions)
```

**2. Features vitesse/distance**
```python
# StandardScaler (mean=0, std=1)
from sklearn.preprocessing import StandardScaler

scaler_speed = StandardScaler()
sog_norm = scaler_speed.fit_transform(sog.reshape(-1, 1))
```

**3. Features cycliques (COG, heure)**
```python
# Encodage sin/cos pour cyclicité
import numpy as np

def cyclical_encoding(values, max_val):
    """Encode cyclical features as sin/cos"""
    values_rad = 2 * np.pi * values / max_val
    sin_val = np.sin(values_rad)
    cos_val = np.cos(values_rad)
    return sin_val, cos_val

# COG (0-360°)
cog_sin, cog_cos = cyclical_encoding(cog, 360)

# Hour of day (0-23)
hour_sin, hour_cos = cyclical_encoding(hour, 24)

# Day of week (0-6)
dow_sin, dow_cos = cyclical_encoding(day_of_week, 7)
```

**4. Features catégorielles**
```python
# One-hot encoding (small cardinality)
from sklearn.preprocessing import OneHotEncoder

encoder_status = OneHotEncoder(sparse=False, handle_unknown='ignore')
status_encoded = encoder_status.fit_transform(status.reshape(-1, 1))

# Label encoding + embedding (large cardinality)
from sklearn.preprocessing import LabelEncoder

encoder_type = LabelEncoder()
vessel_type_encoded = encoder_type.fit_transform(vessel_type)
# Puis embedding layer dans modèle
```

**5. RobustScaler pour outliers**
```python
# Plus robuste aux outliers (utilise médiane et IQR)
from sklearn.preprocessing import RobustScaler

scaler_robust = RobustScaler()
features_norm = scaler_robust.fit_transform(features)
```

**Pipeline complet** :
```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# Définir colonnes par type
numeric_features = ['sog', 'distance', 'acceleration']
spatial_features = ['latitude', 'longitude']
cyclical_features = ['cog', 'hour', 'day_of_week']
categorical_features = ['vessel_type_id', 'vessel_status_id']

# Transformers
numeric_transformer = StandardScaler()
spatial_transformer = MinMaxScaler(feature_range=(-1, 1))
categorical_transformer = OneHotEncoder(handle_unknown='ignore')

# ColumnTransformer
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('spatial', spatial_transformer, spatial_features),
        ('cat', categorical_transformer, categorical_features)
    ],
    remainder='passthrough'  # garder autres colonnes
)
```

**Gestion valeurs manquantes** :
```python
from sklearn.impute import SimpleImputer

# Imputation médiane pour numériques
imputer = SimpleImputer(strategy='median')
features_imputed = imputer.fit_transform(features)

# Ou forward fill pour séries temporelles
features_filled = features.fillna(method='ffill')
```

**Sauvegarde scalers** :
```python
import joblib

# Sauvegarder pour inference
joblib.dump(scaler_spatial, 'scalers/scaler_spatial.pkl')
joblib.dump(scaler_speed, 'scalers/scaler_speed.pkl')
joblib.dump(encoder_type, 'scalers/encoder_vessel_type.pkl')

# Charger
scaler_spatial = joblib.load('scalers/scaler_spatial.pkl')
```

**Validation normalisation** :
```python
# Vérifier distribution après normalisation
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 4))
plt.subplot(1, 3, 1)
plt.hist(features_original, bins=50)
plt.title('Original')
plt.subplot(1, 3, 2)
plt.hist(features_normalized, bins=50)
plt.title('Normalized')
plt.subplot(1, 3, 3)
plt.hist(features_normalized, bins=50, cumulative=True, density=True)
plt.title('CDF')
plt.show()
```

**Livrables** :
- Scalers sauvegardés : `scalers/`
- Pipeline preprocessing : `preprocessing.py`
- Tests unitaires : `test_preprocessing.py`
- Documentation transformations : `docs/normalization.md`
- Notebook validation : `notebooks/preprocessing_validation.ipynb`

---

### 9.1.3 Padding/truncation séquences longueur fixe

**Objectif** : Uniformiser longueur séquences pour batch training

**Fonctionnalités** :
- Padding séquences courtes (zero/mask padding)
- Truncation séquences longues
- Création masques attention
- Gestion longueurs variables (packing)
- Optimisation mémoire batches

**Technologies** :
- **TensorFlow** : `tf.keras.preprocessing.sequence.pad_sequences`
- **PyTorch** : `torch.nn.utils.rnn.pad_sequence`
- **Masking layers** : ignorance padding
- **Attention masks** : Transformers

**Stratégies padding** :

**1. Zero Padding**
```python
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Sequences de longueurs variables
sequences = [
    [[1.2, 3.4], [5.6, 7.8], [9.0, 1.1]],           # longueur 3
    [[2.3, 4.5], [6.7, 8.9]],                       # longueur 2
    [[3.4, 5.6], [7.8, 9.0], [1.2, 3.4], [5.6, 7.8]]  # longueur 4
]

# Padding à longueur max
max_length = 100
padded = pad_sequences(
    sequences,
    maxlen=max_length,
    dtype='float32',
    padding='post',    # 'post' ou 'pre'
    truncating='post', # 'post' ou 'pre'
    value=0.0          # valeur padding
)
# Shape: (n_sequences, max_length, n_features)
```

**2. Mask Padding**
```python
# Créer masque pour positions valides
def create_padding_mask(sequences, pad_value=0.0):
    """Créer masque booléen (True = valide, False = padding)"""
    mask = np.any(sequences != pad_value, axis=-1)
    return mask.astype(np.float32)

padding_mask = create_padding_mask(padded)
# Shape: (n_sequences, max_length)
```

**3. Masking Layer (TensorFlow)**
```python
from tensorflow.keras.layers import Masking

# Layer masking automatique
masking_layer = Masking(mask_value=0.0)

# Dans modèle
model = tf.keras.Sequential([
    Masking(mask_value=0.0, input_shape=(max_length, n_features)),
    LSTM(128, return_sequences=True),
    LSTM(64),
    Dense(output_dim)
])
```

**4. PyTorch Packing**
```python
import torch
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

# Sequences + lengths
sequences = [torch.tensor(seq) for seq in sequences_list]
lengths = torch.tensor([len(seq) for seq in sequences_list])

# Padding
padded_sequences = torch.nn.utils.rnn.pad_sequence(
    sequences, 
    batch_first=True,
    padding_value=0.0
)

# Packing (optimisation LSTM)
packed = pack_padded_sequence(
    padded_sequences,
    lengths,
    batch_first=True,
    enforce_sorted=False
)

# LSTM avec packed
lstm = torch.nn.LSTM(input_size, hidden_size, batch_first=True)
output_packed, (h_n, c_n) = lstm(packed)

# Unpack
output, output_lengths = pad_packed_sequence(output_packed, batch_first=True)
```

**Truncation séquences longues** :

**Stratégie 1 : Truncate head/tail**
```python
def truncate_sequence(sequence, max_len, mode='post'):
    """Truncate à max_len positions"""
    if len(sequence) <= max_len:
        return sequence
    
    if mode == 'post':
        return sequence[:max_len]  # Garder début
    elif mode == 'pre':
        return sequence[-max_len:]  # Garder fin
    elif mode == 'center':
        start = (len(sequence) - max_len) // 2
        return sequence[start:start+max_len]
```

**Stratégie 2 : Sampling uniforme**
```python
def subsample_sequence(sequence, target_len):
    """Sample uniformément pour réduire longueur"""
    if len(sequence) <= target_len:
        return sequence
    
    indices = np.linspace(0, len(sequence)-1, target_len, dtype=int)
    return sequence[indices]
```

**Stratégie 3 : Sliding windows**
```python
def create_sliding_windows(sequence, window_size, stride):
    """Découper séquence longue en windows"""
    windows = []
    for i in range(0, len(sequence) - window_size + 1, stride):
        window = sequence[i:i+window_size]
        windows.append(window)
    return windows
```

**Attention masks pour Transformers** :
```python
def create_attention_mask(padded_sequences, pad_value=0.0):
    """Masque attention (1=valide, 0=padding)"""
    # Détection padding
    mask = np.any(padded_sequences != pad_value, axis=-1)
    return mask.astype(np.int32)

def create_causal_mask(seq_length):
    """Masque causal (prévenir voir futur)"""
    mask = np.tril(np.ones((seq_length, seq_length)))
    return mask

# Combinaison masques
attention_mask = create_attention_mask(sequences)
causal_mask = create_causal_mask(max_length)

# Masque final (broadcasting)
final_mask = attention_mask[:, None, :] * causal_mask[None, :, :]
```

**Gestion mémoire** :
```python
# Batch size adaptatif selon longueur séquences
def adaptive_batch_size(seq_length, base_batch_size=32, max_length=100):
    """Réduire batch_size pour longues séquences"""
    ratio = max_length / seq_length
    return max(1, int(base_batch_size * ratio))

# DataLoader avec batches variables
from torch.utils.data import DataLoader

def collate_fn_variable_length(batch):
    """Collate function pour longueurs variables"""
    sequences, labels = zip(*batch)
    
    # Padding dynamique au max du batch
    max_len_batch = max(len(seq) for seq in sequences)
    padded = pad_sequences(sequences, maxlen=max_len_batch)
    
    return torch.tensor(padded), torch.tensor(labels)

dataloader = DataLoader(
    dataset,
    batch_size=32,
    collate_fn=collate_fn_variable_length,
    shuffle=True
)
```

**Livrables** :
- Fonctions padding/truncation : `sequence_utils.py`
- Tests longueurs variables : `test_sequences.py`
- Benchmark mémoire : `notebooks/memory_optimization.ipynb`
- Documentation stratégies : `docs/sequence_preprocessing.md`

---

### 9.1.4 Train/validation/test split temporel

**Objectif** : Split chronologique éviter data leakage

**Fonctionnalités** :
- Split temporel strict (no shuffle)
- Ratio 80/10/10 ou 70/15/15
- Validation croisée temporelle (TimeSeriesSplit)
- Gap entre splits (éviter contamination)
- Stratification par type navire (optionnel)

**Technologies** :
- **scikit-learn** : TimeSeriesSplit
- **Pandas** : manipulation dates
- **NumPy** : indexation arrays

**Split temporel simple** :
```python
import pandas as pd
import numpy as np

def temporal_split(df, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    """Split temporel strict sans shuffle"""
    assert train_ratio + val_ratio + test_ratio == 1.0
    
    # Trier par date
    df_sorted = df.sort_values('base_date_time')
    
    n = len(df_sorted)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    
    train = df_sorted.iloc[:train_end]
    val = df_sorted.iloc[train_end:val_end]
    test = df_sorted.iloc[val_end:]
    
    return train, val, test

# Utilisation
train_df, val_df, test_df = temporal_split(
    trajectories_df,
    train_ratio=0.8,
    val_ratio=0.1,
    test_ratio=0.1
)

print(f"Train: {train_df['base_date_time'].min()} to {train_df['base_date_time'].max()}")
print(f"Val:   {val_df['base_date_time'].min()} to {val_df['base_date_time'].max()}")
print(f"Test:  {test_df['base_date_time'].min()} to {test_df['base_date_time'].max()}")
```

**Split avec gap temporel** :
```python
def temporal_split_with_gap(df, train_ratio=0.8, val_ratio=0.1, gap_days=7):
    """Split avec gap pour éviter contamination"""
    df_sorted = df.sort_values('base_date_time')
    
    # Dates split
    date_min = df_sorted['base_date_time'].min()
    date_max = df_sorted['base_date_time'].max()
    total_days = (date_max - date_min).days
    
    train_days = int(total_days * train_ratio)
    val_days = int(total_days * val_ratio)
    
    # Frontières avec gaps
    train_end = date_min + pd.Timedelta(days=train_days)
    gap1_end = train_end + pd.Timedelta(days=gap_days)
    val_end = gap1_end + pd.Timedelta(days=val_days)
    gap2_end = val_end + pd.Timedelta(days=gap_days)
    
    # Split
    train = df_sorted[df_sorted['base_date_time'] < train_end]
    val = df_sorted[
        (df_sorted['base_date_time'] >= gap1_end) & 
        (df_sorted['base_date_time'] < val_end)
    ]
    test = df_sorted[df_sorted['base_date_time'] >= gap2_end]
    
    return train, val, test
```

**TimeSeriesSplit (validation croisée)** :
```python
from sklearn.model_selection import TimeSeriesSplit

# 5 folds temporels
tscv = TimeSeriesSplit(n_splits=5, gap=0)

for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
    print(f"Fold {fold}:")
    print(f"  Train: {train_idx.min()}-{train_idx.max()}")
    print(f"  Val:   {val_idx.min()}-{val_idx.max()}")
    
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
    
    # Train model pour ce fold
    model = train_model(X_train, y_train)
    score = evaluate_model(model, X_val, y_val)
    print(f"  Score: {score}")
```

**Stratification par type navire** :
```python
def stratified_temporal_split(df, train_ratio=0.8, vessel_col='vessel_type_id'):
    """Split temporel avec distribution types préservée"""
    train_list, val_list, test_list = [], [], []
    
    # Split par type
    for vessel_type in df[vessel_col].unique():
        df_type = df[df[vessel_col] == vessel_type]
        train, val, test = temporal_split(df_type, train_ratio)
        train_list.append(train)
        val_list.append(val)
        test_list.append(test)
    
    # Concaténer
    train_final = pd.concat(train_list).sort_values('base_date_time')
    val_final = pd.concat(val_list).sort_values('base_date_time')
    test_final = pd.concat(test_list).sort_values('base_date_time')
    
    return train_final, val_final, test_final
```

**Split par navire (éviter leakage)** :
```python
def vessel_aware_split(df, train_ratio=0.8, vessel_col='vessel_id'):
    """Split pour que navires soient soit train soit val/test (pas les deux)"""
    vessels = df[vessel_col].unique()
    np.random.shuffle(vessels)
    
    n_vessels = len(vessels)
    train_vessels = vessels[:int(n_vessels * train_ratio)]
    val_vessels = vessels[int(n_vessels * train_ratio):int(n_vessels * 0.9)]
    test_vessels = vessels[int(n_vessels * 0.9):]
    
    train = df[df[vessel_col].isin(train_vessels)]
    val = df[df[vessel_col].isin(val_vessels)]
    test = df[df[vessel_col].isin(test_vessels)]
    
    return train, val, test
```

**Sauvegarde splits** :
```python
# Sauvegarder indices pour reproductibilité
train_indices = train_df.index.tolist()
val_indices = val_df.index.tolist()
test_indices = test_df.index.tolist()

split_info = {
    'train': {
        'indices': train_indices,
        'date_min': str(train_df['base_date_time'].min()),
        'date_max': str(train_df['base_date_time'].max()),
        'n_samples': len(train_df)
    },
    'val': {
        'indices': val_indices,
        'date_min': str(val_df['base_date_time'].min()),
        'date_max': str(val_df['base_date_time'].max()),
        'n_samples': len(val_df)
    },
    'test': {
        'indices': test_indices,
        'date_min': str(test_df['base_date_time'].min()),
        'date_max': str(test_df['base_date_time'].max()),
        'n_samples': len(test_df)
    }
}

import json
with open('data_splits.json', 'w') as f:
    json.dump(split_info, f, indent=2)
```

**Validation split** :
```python
def validate_temporal_split(train, val, test):
    """Valider pas d'overlap temporel"""
    train_max = train['base_date_time'].max()
    val_min = val['base_date_time'].min()
    val_max = val['base_date_time'].max()
    test_min = test['base_date_time'].min()
    
    assert train_max < val_min, "Train/Val overlap!"
    assert val_max < test_min, "Val/Test overlap!"
    
    print("✓ Split temporel valide (pas d'overlap)")
    print(f"  Train: {train_max}")
    print(f"  Val:   {val_min} - {val_max}")
    print(f"  Test:  {test_min}")
```

**Livrables** :
- Script split : `create_data_splits.py`
- Splits sauvegardés : `data_splits.json`
- Validation split : `validate_splits.py`
- Documentation : `docs/data_splitting.md`
- Notebook analyse : `notebooks/data_split_analysis.ipynb`

---

### 9.1.5 Data augmentation (rotation, translation)

**Objectif** : Augmenter données training + robustesse modèle

**Fonctionnalités** :
- Augmentation géométrique (rotation, translation)
- Augmentation temporelle (time warping, resampling)
- Ajout bruit contrôlé
- Génération trajectoires synthétiques
- Préservation cohérence physique

**Technologies** :
- **NumPy** : transformations géométriques
- **tsaug** : time series augmentation
- **Albumentations** : si représentations images

**Augmentation spatiale** :

**1. Rotation trajectoires**
```python
import numpy as np

def rotate_trajectory(lat, lon, angle_deg):
    """Rotation trajectoire autour centroïde"""
    # Centroïde
    lat_center = np.mean(lat)
    lon_center = np.mean(lon)
    
    # Centrer
    lat_c = lat - lat_center
    lon_c = lon - lon_center
    
    # Rotation
    angle_rad = np.deg2rad(angle_deg)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    lat_rot = lat_c * cos_a - lon_c * sin_a
    lon_rot = lat_c * sin_a + lon_c * cos_a
    
    # Recentrer
    lat_new = lat_rot + lat_center
    lon_new = lon_rot + lon_center
    
    return lat_new, lon_new

# Augmentation random rotation
def augment_rotation(trajectory, max_angle=30):
    """Rotation aléatoire ±max_angle degrés"""
    angle = np.random.uniform(-max_angle, max_angle)
    lat_rot, lon_rot = rotate_trajectory(
        trajectory['latitude'],
        trajectory['longitude'],
        angle
    )
    trajectory_aug = trajectory.copy()
    trajectory_aug['latitude'] = lat_rot
    trajectory_aug['longitude'] = lon_rot
    return trajectory_aug
```

**2. Translation trajectoires**
```python
def translate_trajectory(lat, lon, delta_lat, delta_lon):
    """Translation trajectoire"""
    return lat + delta_lat, lon + delta_lon

def augment_translation(trajectory, max_delta_deg=0.1):
    """Translation aléatoire"""
    delta_lat = np.random.uniform(-max_delta_deg, max_delta_deg)
    delta_lon = np.random.uniform(-max_delta_deg, max_delta_deg)
    
    trajectory_aug = trajectory.copy()
    trajectory_aug['latitude'] += delta_lat
    trajectory_aug['longitude'] += delta_lon
    return trajectory_aug
```

**3. Scaling (zoom)**
```python
def scale_trajectory(lat, lon, scale_factor):
    """Scaling trajectoire autour centroïde"""
    lat_center = np.mean(lat)
    lon_center = np.mean(lon)
    
    lat_scaled = (lat - lat_center) * scale_factor + lat_center
    lon_scaled = (lon - lon_center) * scale_factor + lon_center
    
    return lat_scaled, lon_scaled

def augment_scaling(trajectory, min_scale=0.9, max_scale=1.1):
    """Scaling aléatoire"""
    scale = np.random.uniform(min_scale, max_scale)
    lat_scaled, lon_scaled = scale_trajectory(
        trajectory['latitude'],
        trajectory['longitude'],
        scale
    )
    trajectory_aug = trajectory.copy()
    trajectory_aug['latitude'] = lat_scaled
    trajectory_aug['longitude'] = lon_scaled
    return trajectory_aug
```

**Augmentation temporelle** :

**1. Time warping**
```python
def time_warp(sequence, sigma=0.2):
    """Warping temporel (distorsion vitesse)"""
    seq_len = len(sequence)
    
    # Sampling points
    warp_points = np.linspace(0, seq_len-1, num=5)
    warp_offsets = np.random.normal(0, sigma * seq_len, size=len(warp_points))
    warp_offsets[0] = 0  # Fix start
    warp_offsets[-1] = 0  # Fix end
    
    # Interpolation warping
    from scipy.interpolate import CubicSpline
    cs = CubicSpline(warp_points, warp_points + warp_offsets)
    
    # New indices
    indices_warped = cs(np.arange(seq_len))
    indices_warped = np.clip(indices_warped, 0, seq_len-1)
    
    # Resample
    from scipy.interpolate import interp1d
    interpolator = interp1d(
        np.arange(seq_len),
        sequence,
        axis=0,
        kind='linear',
        fill_value='extrapolate'
    )
    sequence_warped = interpolator(indices_warped)
    
    return sequence_warped
```

**2. Jittering (ajout bruit)**
```python
def jitter(sequence, sigma=0.03):
    """Ajout bruit gaussien"""
    noise = np.random.normal(0, sigma, sequence.shape)
    return sequence + noise
```

**3. Scaling vitesse**
```python
def speed_scaling(sog, scale_factor):
    """Scaling vitesse"""
    return sog * scale_factor

def augment_speed_variation(trajectory, min_scale=0.9, max_scale=1.1):
    """Variation vitesse aléatoire"""
    scale = np.random.uniform(min_scale, max_scale)
    trajectory_aug = trajectory.copy()
    trajectory_aug['sog'] *= scale
    return trajectory_aug
```

**4. Cropping + padding**
```python
def random_crop(sequence, min_len=0.7, max_len=1.0):
    """Crop aléatoire séquence"""
    seq_len = len(sequence)
    crop_len = int(np.random.uniform(min_len, max_len) * seq_len)
    start = np.random.randint(0, seq_len - crop_len + 1)
    return sequence[start:start+crop_len]
```

**Pipeline augmentation** :
```python
class TrajectoryAugmentor:
    """Pipeline augmentation trajectoires"""
    
    def __init__(self, 
                 rotation_prob=0.5,
                 translation_prob=0.5,
                 scaling_prob=0.3,
                 jitter_prob=0.4,
                 time_warp_prob=0.3):
        self.rotation_prob = rotation_prob
        self.translation_prob = translation_prob
        self.scaling_prob = scaling_prob
        self.jitter_prob = jitter_prob
        self.time_warp_prob = time_warp_prob
    
    def augment(self, trajectory):
        """Appliquer augmentations aléatoires"""
        traj_aug = trajectory.copy()
        
        # Rotation
        if np.random.random() < self.rotation_prob:
            traj_aug = augment_rotation(traj_aug, max_angle=30)
        
        # Translation
        if np.random.random() < self.translation_prob:
            traj_aug = augment_translation(traj_aug, max_delta_deg=0.1)
        
        # Scaling
        if np.random.random() < self.scaling_prob:
            traj_aug = augment_scaling(traj_aug)
        
        # Jitter features
        if np.random.random() < self.jitter_prob:
            traj_aug['features'] = jitter(traj_aug['features'], sigma=0.03)
        
        # Time warping
        if np.random.random() < self.time_warp_prob:
            traj_aug['positions'] = time_warp(traj_aug['positions'])
        
        return traj_aug

# Utilisation
augmentor = TrajectoryAugmentor()

# Dans DataLoader
def get_augmented_batch(batch):
    return [augmentor.augment(traj) for traj in batch]
```

**Validation physique** :
```python
def validate_augmentation(trajectory_original, trajectory_augmented):
    """Valider cohérence physique après augmentation"""
    
    # Vitesse max réaliste
    sog_max = trajectory_augmented['sog'].max()
    assert sog_max < 50, f"Vitesse irréaliste: {sog_max} knots"
    
    # Accélération réaliste
    delta_sog = np.diff(trajectory_augmented['sog'])
    acc_max = np.abs(delta_sog).max()
    assert acc_max < 5, f"Accélération irréaliste: {acc_max} knots/step"
    
    # Positions valides
    lat = trajectory_augmented['latitude']
    lon = trajectory_augmented['longitude']
    assert np.all((-90 <= lat) & (lat <= 90)), "Latitude invalide"
    assert np.all((-180 <= lon) & (lon <= 180)), "Longitude invalide"
    
    print("✓ Augmentation valide")
```

**Livrables** :
- Classe augmentation : `augmentation.py`
- Tests validation : `test_augmentation.py`
- Visualisations : `notebooks/augmentation_examples.ipynb`
- Documentation : `docs/data_augmentation.md`

---

## 9.2 Modèles LSTM (Long Short-Term Memory)

### 9.2.1 LSTM simple pour prédiction next position

**Objectif** : Modèle baseline LSTM prédiction position suivante

**Fonctionnalités** :
- Architecture LSTM 1-2 couches
- Input : séquence N positions passées
- Output : position suivante (lat, lon)
- Loss : MSE ou Haversine distance
- Métriques : distance error (km)

**Technologies** :
- **TensorFlow/Keras** ou **PyTorch**
- **LSTM layers** : mémoire long terme
- **Dense layers** : output
- **Adam optimizer**
- **Learning rate scheduling**

**Architecture TensorFlow/Keras** :
```python
import tensorflow as tf
from tensorflow.keras import layers, models

def build_lstm_model(
    sequence_length=50,
    n_features=10,
    lstm_units=128,
    dropout=0.2,
    output_dim=2  # lat, lon
):
    """LSTM simple pour prédiction next position"""
    
    model = models.Sequential([
        # Input
        layers.Input(shape=(sequence_length, n_features)),
        
        # LSTM layer
        layers.LSTM(
            lstm_units,
            return_sequences=False,  # Seulement dernier hidden state
            dropout=dropout,
            recurrent_dropout=dropout
        ),
        
        # Dense layers
        layers.Dense(64, activation='relu'),
        layers.Dropout(dropout),
        layers.Dense(32, activation='relu'),
        
        # Output (lat, lon)
        layers.Dense(output_dim, activation='linear')
    ])
    
    return model

# Build model
model = build_lstm_model(
    sequence_length=50,
    n_features=10,
    lstm_units=128,
    dropout=0.2
)

model.summary()
```

**Architecture PyTorch** :
```python
import torch
import torch.nn as nn

class SimpleLSTM(nn.Module):
    def __init__(self, input_size=10, hidden_size=128, num_layers=1, output_size=2, dropout=0.2):
        super(SimpleLSTM, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM
        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Dense layers
        self.fc1 = nn.Linear(hidden_size, 64)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, output_size)
    
    def forward(self, x):
        # LSTM
        # x shape: (batch, seq_len, input_size)
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Prendre dernier hidden state
        # h_n shape: (num_layers, batch, hidden_size)
        last_hidden = h_n[-1]  # (batch, hidden_size)
        
        # Dense layers
        out = self.fc1(last_hidden)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.relu(out)
        out = self.fc3(out)
        
        return out

# Instantiate
model = SimpleLSTM(
    input_size=10,
    hidden_size=128,
    num_layers=1,
    output_size=2,
    dropout=0.2
)
```

**Préparation données** :
```python
def create_sequences_next_position(data, sequence_length=50):
    """Créer (X, y) pour prédiction next position"""
    X, y = [], []
    
    for i in range(len(data) - sequence_length):
        # Input: sequence_length positions passées
        X.append(data[i:i+sequence_length])
        
        # Target: next position (lat, lon)
        y.append(data[i+sequence_length, [0, 1]])  # indices lat, lon
    
    return np.array(X), np.array(y)

# Utilisation
X_train, y_train = create_sequences_next_position(
    train_data_normalized,
    sequence_length=50
)
print(f"X_train shape: {X_train.shape}")  # (n_samples, 50, n_features)
print(f"y_train shape: {y_train.shape}")  # (n_samples, 2)
```

**Compilation & Training (Keras)** :
```python
# Compilation
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss='mse',
    metrics=['mae']
)

# Callbacks
callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=1e-7
    ),
    tf.keras.callbacks.ModelCheckpoint(
        'models/lstm_next_position.h5',
        monitor='val_loss',
        save_best_only=True
    )
]

# Training
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=100,
    batch_size=64,
    callbacks=callbacks,
    verbose=1
)
```

**Training Loop (PyTorch)** :
```python
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Dataset
train_dataset = TensorDataset(
    torch.FloatTensor(X_train),
    torch.FloatTensor(y_train)
)
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)

# Model, loss, optimizer
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = SimpleLSTM().to(device)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop
num_epochs = 100
for epoch in range(num_epochs):
    model.train()
    train_loss = 0
    
    for batch_X, batch_y in train_loader:
        batch_X = batch_X.to(device)
        batch_y = batch_y.to(device)
        
        # Forward
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        
        # Backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        train_loss += loss.item()
    
    # Validation
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for batch_X, batch_y in val_loader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            val_loss += loss.item()
    
    print(f"Epoch {epoch+1}/{num_epochs} - Train Loss: {train_loss/len(train_loader):.4f}, Val Loss: {val_loss/len(val_loader):.4f}")
```

**Evaluation** :
```python
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Prédictions
y_pred = model.predict(X_test)

# Dénormaliser
y_test_denorm = scaler_spatial.inverse_transform(y_test)
y_pred_denorm = scaler_spatial.inverse_transform(y_pred)

# Métriques
mse = mean_squared_error(y_test_denorm, y_pred_denorm)
mae = mean_absolute_error(y_test_denorm, y_pred_denorm)

print(f"MSE: {mse:.6f}")
print(f"MAE: {mae:.6f}")

# Distance haversine
def haversine_distance(lat1, lon1, lat2, lon2):
    """Distance en km"""
    from math import radians, cos, sin, asin, sqrt
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km

distances_km = [
    haversine_distance(
        y_test_denorm[i, 0], y_test_denorm[i, 1],
        y_pred_denorm[i, 0], y_pred_denorm[i, 1]
    )
    for i in range(len(y_test_denorm))
]

print(f"Mean distance error: {np.mean(distances_km):.2f} km")
print(f"Median distance error: {np.median(distances_km):.2f} km")
print(f"95th percentile: {np.percentile(distances_km, 95):.2f} km")
```

**Visualisation** :
```python
import matplotlib.pyplot as plt

# Courbes loss
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Val Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.title('Training History')

# Distribution erreurs
plt.subplot(1, 2, 2)
plt.hist(distances_km, bins=50, edgecolor='black')
plt.xlabel('Distance Error (km)')
plt.ylabel('Frequency')
plt.title('Prediction Error Distribution')
plt.tight_layout()
plt.show()
```

**Livrables** :
- Modèle LSTM : `models/lstm_next_position.h5`
- Script training : `train_lstm.py`
- Evaluation metrics : `results/lstm_metrics.json`
- Visualisations : `plots/lstm_training.png`
- Notebook analyse : `notebooks/lstm_next_position_analysis.ipynb`

---

### 9.2.2 LSTM bidirectionnel pour analyse trajectoires

**Objectif** : LSTM bidirectionnel pour contexte passé + futur

**Fonctionnalités** :
- Forward + backward LSTM
- Meilleure compréhension patterns séquences
- Classification comportements
- Détection anomalies contextuelles
- Feature extraction trajectoires

**Architecture** :
```python
def build_bidirectional_lstm(
    sequence_length=50,
    n_features=10,
    lstm_units=128,
    n_classes=5  # Classification comportements
):
    """Bidirectional LSTM pour classification"""
    
    model = models.Sequential([
        layers.Input(shape=(sequence_length, n_features)),
        
        # Bidirectional LSTM
        layers.Bidirectional(
            layers.LSTM(lstm_units, return_sequences=False, dropout=0.2),
            merge_mode='concat'  # Concat forward + backward
        ),
        
        # Dense layers
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.2),
        
        # Output (classification)
        layers.Dense(n_classes, activation='softmax')
    ])
    
    return model
```

**PyTorch version** :
```python
class BidirectionalLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, n_classes, dropout=0.2):
        super(BidirectionalLSTM, self).__init__()
        
        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        # hidden_size * 2 car bidirectionnel
        self.fc1 = nn.Linear(hidden_size * 2, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, n_classes)
        self.dropout = nn.Dropout(dropout)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Concatenate last hidden states forward + backward
        # h_n shape: (num_layers * 2, batch, hidden_size)
        h_forward = h_n[-2]  # avant-dernière layer (forward)
        h_backward = h_n[-1]  # dernière layer (backward)
        h_concat = torch.cat([h_forward, h_backward], dim=1)
        
        out = self.fc1(h_concat)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.relu(out)
        out = self.fc3(out)
        
        return out
```

**Applications** :
- Classification comportements (fishing, cargo, passenger)
- Détection patterns navigation
- Anomaly detection contextualisée
- Feature extraction pour downstream tasks

**Livrables** :
- Modèle BiLSTM : `models/bilstm_classifier.h5`
- Script training : `train_bilstm.py`
- Confusion matrix : `results/bilstm_confusion.png`

---

### 9.2.3 Stacked LSTM pour patterns complexes

**Objectif** : LSTM multi-couches pour hiérarchie features

**Architecture** :
```python
def build_stacked_lstm(
    sequence_length=50,
    n_features=10,
    lstm_units=[128, 64, 32],
    output_dim=2
):
    """Stacked LSTM (multiple layers)"""
    
    model = models.Sequential([
        layers.Input(shape=(sequence_length, n_features)),
        
        # Layer 1: return_sequences=True
        layers.LSTM(lstm_units[0], return_sequences=True, dropout=0.2),
        
        # Layer 2: return_sequences=True
        layers.LSTM(lstm_units[1], return_sequences=True, dropout=0.2),
        
        # Layer 3: return_sequences=False (dernier)
        layers.LSTM(lstm_units[2], return_sequences=False, dropout=0.2),
        
        # Dense output
        layers.Dense(64, activation='relu'),
        layers.Dense(output_dim)
    ])
    
    return model
```

**Avantages** :
- Hiérarchie abstractions (low → high level)
- Capture patterns long terme
- Meilleure performance tâches complexes

**Inconvénients** :
- Plus lent training
- Plus de paramètres (overfitting risk)
- Nécessite plus de données

---

### 9.2.4 LSTM avec attention pour focus zones

**Objectif** : Mécanisme attention sur positions importantes

**Architecture Attention** :
```python
class AttentionLayer(layers.Layer):
    """Attention mechanism layer"""
    
    def __init__(self, **kwargs):
        super(AttentionLayer, self).__init__(**kwargs)
    
    def build(self, input_shape):
        # Weight matrix
        self.W = self.add_weight(
            name='attention_weight',
            shape=(input_shape[-1], input_shape[-1]),
            initializer='glorot_uniform',
            trainable=True
        )
        self.b = self.add_weight(
            name='attention_bias',
            shape=(input_shape[-1],),
            initializer='zeros',
            trainable=True
        )
        super(AttentionLayer, self).build(input_shape)
    
    def call(self, x):
        # x shape: (batch, seq_len, features)
        
        # Attention scores
        e = tf.nn.tanh(tf.tensordot(x, self.W, axes=1) + self.b)
        a = tf.nn.softmax(e, axis=1)  # (batch, seq_len, features)
        
        # Weighted sum
        output = x * a
        return tf.reduce_sum(output, axis=1)  # (batch, features)

def build_lstm_attention(sequence_length, n_features, lstm_units=128):
    """LSTM with attention mechanism"""
    
    inputs = layers.Input(shape=(sequence_length, n_features))
    
    # LSTM returning sequences
    lstm_out = layers.LSTM(lstm_units, return_sequences=True)(inputs)
    
    # Attention
    attention_out = AttentionLayer()(lstm_out)
    
    # Dense
    dense1 = layers.Dense(64, activation='relu')(attention_out)
    outputs = layers.Dense(2)(dense1)
    
    model = models.Model(inputs=inputs, outputs=outputs)
    return model
```

**Visualisation attention weights** :
```python
# Extraire attention weights
attention_model = models.Model(
    inputs=model.input,
    outputs=model.get_layer('attention_layer').output
)

attention_weights = attention_model.predict(X_sample)

# Plot
plt.figure(figsize=(12, 4))
plt.plot(attention_weights[0])
plt.xlabel('Sequence Position')
plt.ylabel('Attention Weight')
plt.title('Attention Weights on Trajectory')
plt.show()
```

**Livrables** :
- Modèle LSTM-Attention : `models/lstm_attention.h5`
- Visualisation weights : `notebooks/attention_analysis.ipynb`

---

### 9.2.5 Encoder-Decoder LSTM pour séquence complète

**Objectif** : Seq2Seq pour prédiction trajectoire complète

**Architecture Encoder-Decoder** :
```python
def build_encoder_decoder_lstm(
    input_seq_length=50,
    output_seq_length=10,
    n_features=10,
    latent_dim=128
):
    """Encoder-Decoder LSTM pour seq2seq prediction"""
    
    # ENCODER
    encoder_inputs = layers.Input(shape=(input_seq_length, n_features))
    encoder_lstm = layers.LSTM(latent_dim, return_state=True)
    encoder_outputs, state_h, state_c = encoder_lstm(encoder_inputs)
    encoder_states = [state_h, state_c]
    
    # DECODER
    decoder_inputs = layers.Input(shape=(output_seq_length, n_features))
    decoder_lstm = layers.LSTM(latent_dim, return_sequences=True, return_state=True)
    decoder_outputs, _, _ = decoder_lstm(decoder_inputs, initial_state=encoder_states)
    
    # Dense output
    decoder_dense = layers.Dense(n_features)
    decoder_outputs = decoder_dense(decoder_outputs)
    
    # Model
    model = models.Model([encoder_inputs, decoder_inputs], decoder_outputs)
    
    return model
```

**Training seq2seq** :
```python
# Données
encoder_input = past_sequences  # (batch, 50, features)
decoder_input = future_sequences[:, :-1, :]  # (batch, 9, features) - teacher forcing
decoder_target = future_sequences[:, 1:, :]  # (batch, 9, features) - shifted

# Training
model.compile(optimizer='adam', loss='mse')
model.fit(
    [encoder_input, decoder_input],
    decoder_target,
    epochs=100,
    batch_size=64,
    validation_split=0.2
)
```

**Inference** :
```python
def predict_sequence(model, encoder_input, n_steps=10):
    """Prédire séquence future"""
    # Encoder
    encoder_model = models.Model(model.input[0], model.layers[2].output)
    state_h, state_c = encoder_model.predict(encoder_input)
    
    # Decoder
    decoder_state_input_h = layers.Input(shape=(latent_dim,))
    decoder_state_input_c = layers.Input(shape=(latent_dim,))
    decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
    
    decoder_lstm = model.layers[4]
    decoder_outputs, state_h, state_c = decoder_lstm(
        decoder_inputs,
        initial_state=decoder_states_inputs
    )
    decoder_states = [state_h, state_c]
    decoder_outputs = model.layers[5](decoder_outputs)
    
    decoder_model = models.Model(
        [decoder_inputs] + decoder_states_inputs,
        [decoder_outputs] + decoder_states
    )
    
    # Prédiction itérative
    predictions = []
    current_input = encoder_input[:, -1, :].reshape(1, 1, -1)
    states = [state_h, state_c]
    
    for _ in range(n_steps):
        output, h, c = decoder_model.predict([current_input] + states)
        predictions.append(output[0, 0, :])
        current_input = output
        states = [h, c]
    
    return np.array(predictions)
```

**Livrables** :
- Modèle Encoder-Decoder : `models/lstm_seq2seq.h5`
- Script inference : `predict_trajectory_seq2seq.py`

---

## 9.3 Modèles CNN (Convolutional Neural Networks)

### 9.3.1 CNN 1D sur séquences temporelles

**Objectif** : CNN 1D pour extraction features temporelles

**Architecture** :
```python
def build_cnn1d_model(sequence_length=50, n_features=10, n_classes=5):
    """CNN 1D pour classification comportements"""
    
    model = models.Sequential([
        layers.Input(shape=(sequence_length, n_features)),
        
        # Conv Block 1
        layers.Conv1D(filters=64, kernel_size=5, activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling1D(pool_size=2),
        layers.Dropout(0.2),
        
        # Conv Block 2
        layers.Conv1D(filters=128, kernel_size=5, activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling1D(pool_size=2),
        layers.Dropout(0.2),
        
        # Conv Block 3
        layers.Conv1D(filters=256, kernel_size=3, activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.GlobalAveragePooling1D(),
        
        # Dense
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(n_classes, activation='softmax')
    ])
    
    return model
```

**Avantages CNN vs LSTM** :
- Plus rapide training (parallélisable)
- Capture patterns locaux
- Moins de paramètres
- Bonne performance classification

**Livrables** :
- Modèle CNN1D : `models/cnn1d_classifier.h5`

---

### 9.3.2 CNN pour classification comportements

**Objectif** : Classification types navigation via CNN

**Features engineering** :
- Transformer séquence en image 2D
- Axe X : temps
- Axe Y : features
- Valeurs : normalisées

```python
# Transformer séquence en "image"
def sequence_to_image(sequence):
    """(seq_len, features) → (1, seq_len, features) comme image grayscale"""
    return sequence[np.newaxis, :, :]

# CNN 2D
def build_cnn2d_classifier(seq_len=50, n_features=10, n_classes=5):
    model = models.Sequential([
        layers.Input(shape=(1, seq_len, n_features)),
        
        layers.Conv2D(32, (1, 3), activation='relu', padding='same'),
        layers.MaxPooling2D((1, 2)),
        
        layers.Conv2D(64, (1, 3), activation='relu', padding='same'),
        layers.GlobalAveragePooling2D(),
        
        layers.Dense(128, activation='relu'),
        layers.Dense(n_classes, activation='softmax')
    ])
    return model
```

---

### 9.3.3 ResNet 1D pour patterns profonds

**Objectif** : Residual connections pour réseaux très profonds

**Architecture ResNet Block** :
```python
def residual_block(x, filters, kernel_size=3):
    """Residual block with skip connection"""
    shortcut = x
    
    # Conv path
    x = layers.Conv1D(filters, kernel_size, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    
    x = layers.Conv1D(filters, kernel_size, padding='same')(x)
    x = layers.BatchNormalization()(x)
    
    # Skip connection
    if shortcut.shape[-1] != filters:
        shortcut = layers.Conv1D(filters, 1, padding='same')(shortcut)
    
    x = layers.Add()([x, shortcut])
    x = layers.Activation('relu')(x)
    
    return x

def build_resnet1d(sequence_length=50, n_features=10, n_blocks=3):
    """ResNet 1D avec residual blocks"""
    inputs = layers.Input(shape=(sequence_length, n_features))
    
    x = layers.Conv1D(64, 7, padding='same')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    
    # Residual blocks
    for i in range(n_blocks):
        x = residual_block(x, filters=64 * (2**i))
        x = layers.MaxPooling1D(2)(x)
    
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(128, activation='relu')(x)
    outputs = layers.Dense(2)(x)
    
    model = models.Model(inputs, outputs)
    return model
```

---

### 9.3.4 CNN + LSTM hybride

**Objectif** : Combiner CNN (features locales) + LSTM (séquence)

**Architecture** :
```python
def build_cnn_lstm_hybrid(sequence_length=50, n_features=10):
    """CNN pour features extraction + LSTM pour séquence"""
    
    model = models.Sequential([
        layers.Input(shape=(sequence_length, n_features)),
        
        # CNN feature extraction
        layers.Conv1D(64, 5, activation='relu', padding='same'),
        layers.MaxPooling1D(2),
        layers.Conv1D(128, 3, activation='relu', padding='same'),
        layers.MaxPooling1D(2),
        
        # LSTM pour séquence
        layers.LSTM(128, return_sequences=False),
        
        # Dense
        layers.Dense(64, activation='relu'),
        layers.Dense(2)
    ])
    
    return model
```

**Avantages hybride** :
- CNN : extraction features locales rapide
- LSTM : modélisation dépendances temporelles
- Meilleure performance que chacun seul
- State-of-the-art séries temporelles

---

## 9.4 Transformers

### 9.4.1 Transformer pour prédiction trajectoire

**Objectif** : Architecture Transformer attention-based

**Composants** :
- Multi-head self-attention
- Positional encoding
- Feed-forward networks
- Layer normalization

**Architecture Transformer** :
```python
class TransformerBlock(layers.Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, dropout=0.1):
        super(TransformerBlock, self).__init__()
        self.att = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.ffn = models.Sequential([
            layers.Dense(ff_dim, activation='relu'),
            layers.Dense(embed_dim)
        ])
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = layers.Dropout(dropout)
        self.dropout2 = layers.Dropout(dropout)
    
    def call(self, inputs, training):
        # Multi-head attention
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        
        # Feed forward
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

def build_transformer_model(
    sequence_length=50,
    n_features=10,
    num_heads=4,
    ff_dim=128,
    num_blocks=2,
    dropout=0.1
):
    """Transformer model pour trajectoires"""
    
    inputs = layers.Input(shape=(sequence_length, n_features))
    
    # Positional encoding
    positions = tf.range(start=0, limit=sequence_length, delta=1)
    pos_embedding = layers.Embedding(input_dim=sequence_length, output_dim=n_features)(positions)
    x = inputs + pos_embedding
    
    # Transformer blocks
    for _ in range(num_blocks):
        x = TransformerBlock(n_features, num_heads, ff_dim, dropout)(x)
    
    # Global pooling + dense
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(64, activation='relu')(x)
    outputs = layers.Dense(2)(x)
    
    model = models.Model(inputs=inputs, outputs=outputs)
    return model
```

---

### 9.4.2 Multi-head attention temporelle

**Objectif** : Attention sur différentes représentations temps

```python
# Multi-head attention avec 8 heads
attention_layer = layers.MultiHeadAttention(
    num_heads=8,
    key_dim=64,
    dropout=0.1
)

# Application
attention_output = attention_layer(query, value, key)
```

**Visualisation attention** :
```python
# Extraire attention weights
attention_scores = attention_layer.attention_scores

# Plot heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(attention_scores[0], cmap='viridis')
plt.xlabel('Key Position')
plt.ylabel('Query Position')
plt.title('Attention Weights Heatmap')
plt.show()
```

---

### 9.4.3 Positional encoding pour timestamps

**Objectif** : Encoder position temporelle dans séquence

```python
def positional_encoding(length, depth):
    """Positional encoding sinusoidal"""
    depth = depth / 2
    positions = np.arange(length)[:, np.newaxis]
    depths = np.arange(depth)[np.newaxis, :] / depth
    
    angle_rates = 1 / (10000**depths)
    angle_rads = positions * angle_rates
    
    pos_encoding = np.concatenate([
        np.sin(angle_rads),
        np.cos(angle_rads)
    ], axis=-1)
    
    return tf.cast(pos_encoding, dtype=tf.float32)

# Ajouter à input
pos_enc = positional_encoding(sequence_length, embed_dim)
x = inputs + pos_enc
```

---

### 9.4.4 BERT-like pour masked trajectory prediction

**Objectif** : Pré-training self-supervised style BERT

**Masked Trajectory Modeling** :
```python
def mask_trajectory(trajectory, mask_prob=0.15):
    """Masquer positions aléatoirement"""
    mask = np.random.rand(len(trajectory)) < mask_prob
    masked_trajectory = trajectory.copy()
    masked_trajectory[mask] = 0  # ou token spécial [MASK]
    return masked_trajectory, mask

# Training objective
def masked_prediction_loss(y_true, y_pred, mask):
    """Loss seulement sur positions masquées"""
    loss = tf.keras.losses.MSE(y_true, y_pred)
    masked_loss = loss * mask
    return tf.reduce_mean(masked_loss)
```

---

## 📊 Livrables Phase 9

### Modèles Deep Learning
```
models/
├── lstm_next_position.h5
├── bilstm_classifier.h5
├── stacked_lstm.h5
├── lstm_attention.h5
├── lstm_seq2seq.h5
├── cnn1d_classifier.h5
├── cnn2d_classifier.h5
├── resnet1d.h5
├── cnn_lstm_hybrid.h5
├── transformer_trajectories.h5
└── bert_trajectories.h5
```

### Scripts
```
scripts/
├── data_preparation/
│   ├── extract_sequences.py
│   ├── normalize_features.py
│   ├── augmentation.py
│   └── create_splits.py
├── training/
│   ├── train_lstm.py
│   ├── train_cnn.py
│   ├── train_transformer.py
│   └── train_hybrid.py
├── evaluation/
│   ├── evaluate_models.py
│   ├── compare_architectures.py
│   └── visualize_predictions.py
└── inference/
    ├── predict_trajectory.py
    └── batch_inference.py
```

### Tables PostgreSQL
```sql
trajectory_sequences
model_predictions
model_performance_dl
attention_weights_storage
trajectory_embeddings
```

### Documentation
```
docs/
├── architectures.md
├── training_guide.md
├── hyperparameters_tuning.md
├── model_comparison.md
└── deployment_guide.md
```

---

## ✅ Critères de Validation Phase 9

1. ✅ **Données préparées**
   - Séquences extraites et normalisées
   - Splits train/val/test temporels
   - Augmentation implémentée

2. ✅ **Modèles LSTM**
   - LSTM simple (next position)
   - BiLSTM classifier
   - LSTM attention
   - Encoder-Decoder

3. ✅ **Modèles CNN**
   - CNN 1D classifier
   - ResNet 1D
   - CNN-LSTM hybride

4. ✅ **Transformers**
   - Transformer baseline
   - Multi-head attention
   - Positional encoding

5. ✅ **Performance**
   - Prédiction < 1km erreur moyenne
   - Classification > 85% accuracy
   - Inference < 100ms

6. ✅ **Production**
   - Modèles sauvegardés
   - API inference
   - Monitoring déployé

---

**Fin SPECS_PHASE_09.md**
