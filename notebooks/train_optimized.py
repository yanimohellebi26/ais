#!/usr/bin/env python3
"""
Script d'entraînement AIS Optimisé
Supporte chargement local (CSV) et distant (DB).
Intègre des features avancées (Delta Time, Accélération, ROT).
"""

import os
import sys
import time
import random
import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURATION
# ==========================================
SEED = 42
SEQ_IN = 20
SEQ_OUT = 10
BATCH_SIZE = 64  # Adapté pour CPU/GPU standard
EPOCHS = 20
LR = 0.001
HIDDEN_DIM = 256
N_HEADS = 8
N_LAYERS = 4
DROPOUT = 0.1
EMBED_VT = 32

# Features: x, y, sog, cog, dt, accel, rot
INPUT_DIM = 7 

# Chemins
OUTPUT_DIR = Path("output_optimized")
OUTPUT_DIR.mkdir(exist_ok=True)
DATA_DIR = Path("dataset")
CSV_PATH = DATA_DIR / "AIS_temp.csv"

# DB Config (si disponible)
DB_CONFIG = {
    "host": "172.31.60.8",
    "port": 5432,
    "database": "ais",
    "user": "postgres",
    "password": "ANjw/84H77C9h2"
}

# ==========================================
# UTILITAIRES
# ==========================================
def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def haversine_np(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dl / 2.0) ** 2
    return 2.0 * R * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))

# ==========================================
# CHARGEMENT DES DONNÉES
# ==========================================
def load_data():
    """Charge les données depuis la DB ou CSV."""
    # Essai DB
    try:
        import psycopg2
        logger.info("Tentative de connexion à la DB...")
        conn = psycopg2.connect(**DB_CONFIG, connect_timeout=3)
        query = """
        SELECT 
            v.mmsi,
            ST_X(pv.geom::geometry) as lon,
            ST_Y(pv.geom::geometry) as lat,
            pv.sog,
            pv.cog,
            EXTRACT(EPOCH FROM pv.base_date_time) as timestamp,
            COALESCE(v.vessel_type_id, 0) as vessel_type
        FROM position_vessel pv
        JOIN vessel v ON pv.vessel_id = v.id
        WHERE pv.sog IS NOT NULL 
          AND pv.cog IS NOT NULL
        ORDER BY v.mmsi, pv.base_date_time
        LIMIT 100000
        """
        df = pd.read_sql(query, conn)
        conn.close()
        logger.info(f"Données chargées depuis DB: {len(df)} lignes")
        return df
    except Exception as e:
        logger.warning(f"Connexion DB échouée: {e}")
    
    # Essai CSV
    if CSV_PATH.exists():
        logger.info(f"Chargement depuis CSV: {CSV_PATH}")
        df = pd.read_csv(CSV_PATH)
        # Mapping colonnes CSV -> Standard
        # CSV: MMSI,BaseDateTime,LAT,LON,SOG,COG,VesselType
        df = df.rename(columns={
            'MMSI': 'mmsi',
            'LAT': 'lat',
            'LON': 'lon',
            'SOG': 'sog',
            'COG': 'cog',
            'VesselType': 'vessel_type'
        })
        # Conversion timestamp
        df['timestamp'] = pd.to_datetime(df['BaseDateTime']).astype(int) / 10**9
        logger.info(f"Données chargées depuis CSV: {len(df)} lignes")
        return df
    
    logger.error("Aucune source de données disponible.")
    return None

def preprocess_data(df):
    """Prépare les fenêtres et features."""
    logger.info("Préparation des données...")
    windows = []
    vessel_types = []
    
    grouped = df.groupby('mmsi')
    total_len = SEQ_IN + SEQ_OUT
    
    for mmsi, group in grouped:
        if len(group) < total_len:
            continue
            
        group = group.sort_values('timestamp')
        
        # Calcul Delta Time
        timestamps = group['timestamp'].values
        dt = np.diff(timestamps, prepend=timestamps[0])
        
        # Coordonnées relatives (en mètres)
        lat_ref = group['lat'].iloc[0]
        lon_ref = group['lon'].iloc[0]
        
        METER_PER_DEG_LAT = 111320.0
        meter_per_deg_lon = 40075000.0 * np.cos(np.radians(lat_ref)) / 360.0
        
        x = (group['lon'].values - lon_ref) * meter_per_deg_lon
        y = (group['lat'].values - lat_ref) * METER_PER_DEG_LAT
        
        sog = group['sog'].values
        cog = group['cog'].values
        
        # Calcul Accélération et ROT
        # Éviter division par zéro
        dt_safe = np.where(dt == 0, 1.0, dt)
        accel = np.diff(sog, prepend=sog[0]) / dt_safe
        
        # ROT (différence angulaire minimale)
        cog_diff = np.diff(cog, prepend=cog[0])
        cog_diff = (cog_diff + 180) % 360 - 180
        rot = cog_diff / dt_safe
        
        # Normalisation basique (Z-score ou MinMax pourrait être mieux, ici simple scaling)
        # SOG ~ 0-50, COG ~ 0-360
        sog_norm = sog / 30.0
        cog_norm = cog / 360.0
        dt_norm = np.clip(dt, 0, 300) / 300.0
        accel_norm = np.clip(accel, -1, 1)
        rot_norm = np.clip(rot, -5, 5) / 5.0
        
        # Stack features: x, y, sog, cog, dt, accel, rot
        # x, y restent en mètres pour la prédiction (ou on pourrait normaliser)
        # Pour le Transformer, il vaut mieux normaliser x, y aussi si possible, 
        # mais ici on garde l'échelle relative pour la loss MSE en mètres.
        # On va normaliser x et y par rapport à la fenêtre dans le Dataset __getitem__
        
        data = np.column_stack([x, y, sog_norm, cog_norm, dt_norm, accel_norm, rot_norm])
        vtype = group['vessel_type'].iloc[0]
        
        # Création fenêtres glissantes
        for i in range(len(data) - total_len + 1):
            window = data[i:i+total_len]
            # Vérifier continuité temporelle (pas de trou > 10 min)
            window_dt = dt[i:i+total_len]
            if np.any(window_dt > 600): # 10 minutes
                continue
                
            windows.append(window)
            vessel_types.append(vtype)
            
    return np.array(windows), np.array(vessel_types)

# ==========================================
# DATASET
# ==========================================
class AISDataset(Dataset):
    def __init__(self, windows, vessel_types):
        self.windows = torch.FloatTensor(windows)
        self.vessel_types = torch.LongTensor(vessel_types)
        
    def __len__(self):
        return len(self.windows)
    
    def __getitem__(self, idx):
        # Window: [SEQ_IN + SEQ_OUT, FEATURES]
        window = self.windows[idx]
        
        # Normalisation relative de la position pour l'entrée
        # On prend la dernière position connue (t=SEQ_IN-1) comme origine (0,0)
        origin_x = window[SEQ_IN-1, 0]
        origin_y = window[SEQ_IN-1, 1]
        
        # Copie pour ne pas modifier l'original
        x_seq = window.clone()
        x_seq[:, 0] -= origin_x
        x_seq[:, 1] -= origin_y
        
        # Input: [SEQ_IN, FEATURES]
        src = x_seq[:SEQ_IN]
        
        # Target: [SEQ_OUT, 2] (x, y relatifs)
        tgt = x_seq[SEQ_IN:, :2]
        
        vtype = self.vessel_types[idx]
        
        return src, vtype, tgt

# ==========================================
# MODÈLE
# ==========================================
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

class AIS_Transformer(nn.Module):
    def __init__(self, input_dim=INPUT_DIM, hidden_dim=HIDDEN_DIM, n_heads=N_HEADS, 
                 n_layers=N_LAYERS, dropout=DROPOUT, n_vessel_types=100):
        super().__init__()
        
        # Embedding Type Navire
        self.vessel_embedding = nn.Embedding(n_vessel_types, EMBED_VT)
        
        # Projection entrée -> Hidden
        self.input_proj = nn.Linear(input_dim, hidden_dim - EMBED_VT)
        
        self.pos_encoder = PositionalEncoding(hidden_dim, dropout)
        
        encoder_layers = nn.TransformerEncoderLayer(hidden_dim, n_heads, hidden_dim*4, dropout)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, n_layers)
        
        # Décodeur pour prédiction
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, SEQ_OUT * 2) # Prédiction x, y pour SEQ_OUT pas de temps
        )
        
    def forward(self, src, vtype):
        # src: [Batch, Seq, Feat]
        # vtype: [Batch]
        
        # Projection
        x = self.input_proj(src) # [Batch, Seq, Hidden-Emb]
        
        # Ajout embedding navire (concaténé ou additionné, ici concaténé pour chaque pas de temps)
        v_emb = self.vessel_embedding(vtype).unsqueeze(1).repeat(1, src.size(1), 1) # [Batch, Seq, Emb]
        x = torch.cat([x, v_emb], dim=2) # [Batch, Seq, Hidden]
        
        # Transformer attend [Seq, Batch, Hidden]
        x = x.permute(1, 0, 2)
        x = self.pos_encoder(x)
        output = self.transformer_encoder(x)
        
        # On prend la dernière sortie pour prédire la suite
        # Ou on pourrait utiliser un TransformerDecoder
        # Ici approche simple: encodage de la séquence -> prédiction directe de la trajectoire future
        last_output = output[-1] # [Batch, Hidden]
        
        prediction = self.decoder(last_output) # [Batch, SEQ_OUT * 2]
        prediction = prediction.view(-1, SEQ_OUT, 2) # [Batch, SEQ_OUT, 2]
        
        return prediction

# ==========================================
# MAIN
# ==========================================
def main():
    set_seed(SEED)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Utilisation du device: {device}")
    
    # 1. Chargement
    df = load_data()
    if df is None or len(df) == 0:
        logger.error("Pas de données. Arrêt.")
        return
        
    # 2. Préparation
    windows, vessel_types = preprocess_data(df)
    if len(windows) == 0:
        logger.error("Pas assez de données pour créer des fenêtres.")
        return
        
    logger.info(f"Dataset créé: {len(windows)} fenêtres")
    
    # Split Train/Val
    indices = np.random.permutation(len(windows))
    split = int(len(windows) * 0.8)
    train_idx, val_idx = indices[:split], indices[split:]
    
    train_ds = AISDataset(windows[train_idx], vessel_types[train_idx])
    val_ds = AISDataset(windows[val_idx], vessel_types[val_idx])
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)
    
    # 3. Modèle
    n_vtypes = int(vessel_types.max()) + 1
    model = AIS_Transformer(n_vessel_types=max(n_vtypes, 100)).to(device)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    
    # 4. Entraînement
    logger.info("Début de l'entraînement...")
    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0
        for src, vtype, tgt in train_loader:
            src, vtype, tgt = src.to(device), vtype.to(device), tgt.to(device)
            
            optimizer.zero_grad()
            pred = model(src, vtype)
            loss = criterion(pred, tgt)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for src, vtype, tgt in val_loader:
                src, vtype, tgt = src.to(device), vtype.to(device), tgt.to(device)
                pred = model(src, vtype)
                val_loss += criterion(pred, tgt)
        
        logger.info(f"Epoch {epoch+1}/{EPOCHS} | Train Loss: {train_loss/len(train_loader):.4f} | Val Loss: {val_loss/len(val_loader):.4f}")
        
    # 5. Sauvegarde
    torch.save(model.state_dict(), OUTPUT_DIR / "ais_model_optimized.pth")
    logger.info(f"Modèle sauvegardé dans {OUTPUT_DIR}")
    
    # 6. Visualisation (si matplotlib disponible)
    try:
        import matplotlib.pyplot as plt
        logger.info("Génération des visualisations...")
        
        model.eval()
        with torch.no_grad():
            # Prendre un batch de validation
            src, vtype, tgt = next(iter(val_loader))
            src, vtype, tgt = src.to(device), vtype.to(device), tgt.to(device)
            pred = model(src, vtype)
            
            # Plot 4 exemples
            fig, axes = plt.subplots(2, 2, figsize=(12, 12))
            for i in range(4):
                ax = axes[i//2, i%2]
                
                # Récupérer les trajectoires (relatives -> absolues pour l'affichage, ou juste relatives)
                # On affiche en relatif (mètres depuis le dernier point connu)
                
                # Historique (src)
                # src est [SEQ_IN, FEATURES]. Les 2 premières features sont x, y
                hist_x = src[i, :, 0].cpu().numpy()
                hist_y = src[i, :, 1].cpu().numpy()
                
                # Target (tgt)
                tgt_x = tgt[i, :, 0].cpu().numpy()
                tgt_y = tgt[i, :, 1].cpu().numpy()
                
                # Prediction (pred)
                pred_x = pred[i, :, 0].cpu().numpy()
                pred_y = pred[i, :, 1].cpu().numpy()
                
                ax.plot(hist_x, hist_y, 'b.-', label='Historique')
                ax.plot(tgt_x, tgt_y, 'g.-', label='Réel')
                ax.plot(pred_x, pred_y, 'r.--', label='Prédit')
                
                ax.set_title(f"Exemple {i+1}")
                ax.legend()
                ax.grid(True)
                
            plt.tight_layout()
            plt.savefig(OUTPUT_DIR / "predictions_sample.png")
            logger.info(f"Visualisation sauvegardée: {OUTPUT_DIR / 'predictions_sample.png'}")
            
    except ImportError:
        logger.warning("Matplotlib non installé, pas de visualisation.")
    except Exception as e:
        logger.warning(f"Erreur visualisation: {e}")

if __name__ == "__main__":
    main()
