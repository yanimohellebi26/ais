#!/usr/bin/env python3
"""
AIS Trajectory Prediction - Training Script pour serveur distant (2x L40S)

Utilise les données de la base PostgreSQL distante.
Optimisé pour Multi-GPU avec DataParallel.
Inclut: Early Stopping amélioré, Visualisations, Métriques complètes

Auteur: Projet AIS
Date: Décembre 2025
"""

import os
import sys
import math
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
import pandas as pd
from tqdm import tqdm

import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from torch.optim.lr_scheduler import ReduceLROnPlateau
import psycopg2

import matplotlib
matplotlib.use('Agg')  # Pour serveur sans écran
import matplotlib.pyplot as plt

# ==========================================
# CONFIGURATION
# ==========================================
SEED = 42

# --- HYPERPARAMÈTRES ---
SEQ_IN = 20               # Séquence d'entrée (20 positions)
SEQ_OUT = 10              # Séquence de sortie (10 positions à prédire)
BATCH_SIZE = 512          # Gros batch pour exploiter les GPUs
LR = 1e-4                 # Learning rate initial (réduit pour stabilité)
EPOCHS = 100              # Max epochs
MIN_EPOCHS = 10           # Minimum d'epochs avant early stopping
PATIENCE = 10             # Patience pour early stopping
MIN_DELTA = 1e-4          # Amélioration minimale requise
NUM_WORKERS = 4           

# === CONFIGURATION DATASET ===
TRAIN_SIZE = 800_000      # 800K pour entraînement
VAL_SIZE = 200_000        # 200K pour validation

# Architecture Modèle
HIDDEN = 256              
N_HEADS = 8               
N_LAYERS = 4              
DROPOUT = 0.1            
EMBED_VT = 32             
INPUT_DIM = 10            # x, y, sog, sin_cog, cos_cog, sin_hdg, cos_hdg, dt, accel, rot

# Base de données
DB_CONFIG = {
    'host': '172.31.60.8',
    'port': 5432,
    'database': 'ais',
    'user': 'postgres',
    'password': 'ANjw/84H77C9h2'
}

# Chemins de sortie
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ==========================================
# LOGGING CONFIGURATION
# ==========================================
LOG_FILE = OUTPUT_DIR / f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def log(msg: str, level: str = "info"):
    """Log message avec flush immédiat."""
    getattr(logger, level)(msg)
    for handler in logger.handlers:
        handler.flush()


# ==========================================
# REPRODUCTIBILITÉ
# ==========================================
def set_seed(seed: int = SEED):
    """Configure la reproductibilité."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


# ==========================================
# SETUP DEVICE
# ==========================================
def setup_device() -> torch.device:
    """Configure le device pour GPU/CPU."""
    if torch.cuda.is_available():
        n_gpus = torch.cuda.device_count()
        log(f"🚀 {n_gpus} GPU(s) détecté(s):")
        for i in range(n_gpus):
            props = torch.cuda.get_device_properties(i)
            log(f"   GPU {i}: {props.name} ({props.total_memory / 1e9:.1f} Go)")
        device = torch.device("cuda")
    else:
        log("⚠️ Pas de GPU, utilisation du CPU")
        device = torch.device("cpu")
    return device


# ==========================================
# EARLY STOPPING AMÉLIORÉ
# ==========================================
class EarlyStopping:
    """
    Early stopping amélioré avec plusieurs critères.
    
    Features:
    - Période de grâce (min_epochs)
    - Delta minimum pour considérer une amélioration
    - Sauvegarde du meilleur état
    - Support pour monitoring de plusieurs métriques
    """
    
    def __init__(self, patience: int = PATIENCE, min_delta: float = MIN_DELTA, 
                 min_epochs: int = MIN_EPOCHS, mode: str = 'min', 
                 restore_best: bool = True):
        """
        Args:
            patience: Nombre d'epochs sans amélioration avant arrêt
            min_delta: Amélioration minimale requise
            min_epochs: Minimum d'epochs avant de commencer le early stopping
            mode: 'min' pour loss, 'max' pour accuracy
            restore_best: Restaurer les meilleurs poids à la fin
        """
        self.patience = patience
        self.min_delta = min_delta
        self.min_epochs = min_epochs
        self.mode = mode
        self.restore_best = restore_best
        
        self.counter = 0
        self.best_score = None
        self.best_epoch = 0
        self.best_state = None
        self.early_stop = False
        self.history = []
        
    def __call__(self, score: float, epoch: int, model: Optional[nn.Module] = None) -> bool:
        """
        Vérifie si on doit arrêter l'entraînement.
        
        Args:
            score: Métrique à monitorer (loss ou accuracy)
            epoch: Numéro de l'epoch actuel
            model: Modèle pour sauvegarder les poids
            
        Returns:
            True si on doit arrêter l'entraînement
        """
        self.history.append(score)
        
        # Période de grâce
        if epoch < self.min_epochs:
            if self.best_score is None or self._is_improvement(score):
                self._update_best(score, epoch, model)
            return False
        
        # Premier score après période de grâce
        if self.best_score is None:
            self._update_best(score, epoch, model)
            return False
        
        # Vérifier amélioration
        if self._is_improvement(score):
            self._update_best(score, epoch, model)
            self.counter = 0
        else:
            self.counter += 1
            log(f"   ⏳ EarlyStopping: {self.counter}/{self.patience} "
                f"(best: {self.best_score:.4f} @ epoch {self.best_epoch})")
            
            if self.counter >= self.patience:
                self.early_stop = True
                return True
        
        return False
    
    def _is_improvement(self, score: float) -> bool:
        """Vérifie si le score s'est amélioré significativement."""
        if self.mode == 'min':
            return score < (self.best_score - self.min_delta)
        return score > (self.best_score + self.min_delta)
    
    def _update_best(self, score: float, epoch: int, model: Optional[nn.Module]):
        """Met à jour le meilleur score et sauvegarde l'état du modèle."""
        self.best_score = score
        self.best_epoch = epoch
        if model is not None and self.restore_best:
            self.best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    
    def restore_best_weights(self, model: nn.Module):
        """Restaure les meilleurs poids du modèle."""
        if self.best_state is not None:
            model.load_state_dict(self.best_state)
            log(f"   ✅ Poids restaurés depuis epoch {self.best_epoch}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de l'early stopping."""
        return {
            'stopped_early': self.early_stop,
            'best_epoch': self.best_epoch,
            'best_score': self.best_score,
            'patience_used': self.counter,
            'total_epochs': len(self.history)
        }


# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================
def haversine_distance(lat1: np.ndarray, lon1: np.ndarray, 
                       lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """
    Calcule la distance haversine en mètres.
    
    Args:
        lat1, lon1: Coordonnées du premier point (degrés)
        lat2, lon2: Coordonnées du second point (degrés)
    
    Returns:
        Distance en mètres
    """
    R = 6371000.0  # Rayon de la Terre en mètres
    
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    
    return R * c


def compute_ade_fde(pred: np.ndarray, true: np.ndarray) -> Tuple[float, float]:
    """
    Calcule ADE et FDE en mètres.
    
    ADE: Average Displacement Error - erreur moyenne sur toute la trajectoire
    FDE: Final Displacement Error - erreur au point final
    
    Args:
        pred: Prédictions (N, T, 2) - lat, lon en degrés
        true: Vérité terrain (N, T, 2) - lat, lon en degrés
    
    Returns:
        (ADE, FDE) en mètres
    """
    N, T, _ = pred.shape
    
    # Calculer toutes les distances point par point
    distances = np.zeros((N, T))
    for t in range(T):
        distances[:, t] = haversine_distance(
            pred[:, t, 0], pred[:, t, 1],
            true[:, t, 0], true[:, t, 1]
        )
    
    ade = np.mean(distances)  # Moyenne sur tous les points et échantillons
    fde = np.mean(distances[:, -1])  # Moyenne seulement sur le dernier point
    
    return ade, fde


def compute_metrics_per_horizon(pred: np.ndarray, true: np.ndarray) -> List[Dict]:
    """
    Calcule les métriques par horizon de prédiction.
    
    Args:
        pred: Prédictions (N, T, 2)
        true: Vérité terrain (N, T, 2)
    
    Returns:
        Liste de dict avec erreurs par timestep
    """
    N, T, _ = pred.shape
    errors = []
    
    for t in range(T):
        dist = haversine_distance(
            pred[:, t, 0], pred[:, t, 1],
            true[:, t, 0], true[:, t, 1]
        )
        errors.append({
            'timestep': t + 1,
            'mean_error': np.mean(dist),
            'std_error': np.std(dist),
            'median_error': np.median(dist),
            'p90_error': np.percentile(dist, 90)
        })
    
    return errors


# ==========================================
# CHARGEMENT DES DONNÉES
# ==========================================
def load_data_from_db() -> pd.DataFrame:
    """Charge les données AIS depuis la base PostgreSQL."""
    log("📊 Connexion à la base de données PostgreSQL...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        log("✅ Connexion réussie!")
        
        # Requête optimisée avec filtres de qualité
        query = """
        SELECT 
            v.mmsi AS "MMSI",
            pv.base_date_time AS "BaseDateTime",
            ST_Y(pv.geom::geometry) AS "LAT",
            ST_X(pv.geom::geometry) AS "LON",
            pv.sog AS "SOG",
            pv.cog AS "COG",
            COALESCE(pv.heading, pv.cog) AS "Heading",
            COALESCE(v.vessel_type_id, 0) AS "VesselType"
        FROM position_vessel pv
        JOIN vessel v ON pv.vessel_id = v.id
        WHERE pv.sog IS NOT NULL 
          AND pv.cog IS NOT NULL
          AND pv.geom IS NOT NULL
          AND pv.sog >= 0.1          -- Exclure navires immobiles
          AND pv.sog < 50            -- Vitesse réaliste (noeuds)
          AND pv.cog >= 0 AND pv.cog <= 360
          AND ST_Y(pv.geom::geometry) BETWEEN -90 AND 90
          AND ST_X(pv.geom::geometry) BETWEEN -180 AND 180
        ORDER BY v.mmsi, pv.base_date_time;
        """
        
        log("📥 Extraction des données (peut prendre plusieurs minutes)...")
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Optimisation mémoire
        df['MMSI'] = df['MMSI'].astype('int64')
        df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'])
        df['VesselType'] = df['VesselType'].astype('int32')
        df['LAT'] = df['LAT'].astype('float32')
        df['LON'] = df['LON'].astype('float32')
        df['SOG'] = df['SOG'].astype('float32')
        df['COG'] = df['COG'].astype('float32')
        df['Heading'] = df['Heading'].astype('float32')
        
        n_vessels = df['MMSI'].nunique()
        log(f"✅ {len(df):,} positions chargées pour {n_vessels:,} navires")
        
        # Stats rapides
        log(f"   SOG: min={df['SOG'].min():.1f}, max={df['SOG'].max():.1f}, mean={df['SOG'].mean():.1f}")
        log(f"   LAT: [{df['LAT'].min():.2f}, {df['LAT'].max():.2f}]")
        log(f"   LON: [{df['LON'].min():.2f}, {df['LON'].max():.2f}]")
        
        return df
        
    except Exception as e:
        log(f"❌ Erreur de connexion: {e}", "error")
        raise


# ==========================================
# DATASET
# ==========================================
class AISDataset(Dataset):
    """
    Dataset pour trajectoires AIS.
    
    Features d'entrée (10):
    - x, y: position relative en km
    - sog: vitesse normalisée
    - sin_cog, cos_cog: direction du mouvement
    - sin_hdg, cos_hdg: direction du navire
    - dt: intervalle temporel normalisé
    - accel: accélération
    - rot: rate of turn
    """
    
    # Constantes de normalisation
    SCALE_POSITION = 1000.0  # Convertit mètres en km
    SCALE_SOG = 30.0         # Vitesse max ~30 noeuds
    SCALE_DT = 600.0         # 10 minutes
    MAX_GAP_SECONDS = 1800   # Gap max de 30 minutes entre positions
    
    def __init__(self, df: pd.DataFrame, seq_in: int = SEQ_IN, seq_out: int = SEQ_OUT, 
                 max_windows: int = TRAIN_SIZE + VAL_SIZE):
        self.seq_in = seq_in
        self.seq_out = seq_out
        self.total_len = seq_in + seq_out
        
        # Mapping des types de navires
        df = df.copy()
        if df["VesselType"].dtype == object:
            df["VesselType"] = pd.to_numeric(df["VesselType"], errors="coerce").fillna(0).astype(int)
        
        unique_vtypes = sorted(df["VesselType"].unique())
        self.vtype2idx = {v: i for i, v in enumerate(unique_vtypes)}
        self.idx2vtype = {i: v for v, i in self.vtype2idx.items()}
        df["VTIDX"] = df["VesselType"].map(self.vtype2idx).astype(int)
        
        # Création des fenêtres
        windows = self._create_windows(df, max_windows)
        
        if not windows:
            raise ValueError("Dataset vide après fenêtrage! Vérifiez les données.")
        
        # Mélanger et stocker
        random.shuffle(windows)
        log(f"✅ {len(windows):,} fenêtres créées")
        
        self.inp = np.array([w[0] for w in windows], dtype=np.float32)
        self.out = np.array([w[1] for w in windows], dtype=np.float32)
        
        # Stats du dataset
        self._log_stats()
    
    def _create_windows(self, df: pd.DataFrame, max_windows: int) -> List:
        """Crée les fenêtres glissantes avec contrôle de qualité."""
        windows = []
        grouped = df.groupby("MMSI", sort=False)
        n_groups = len(grouped)
        
        log(f"🔄 Création des fenêtres (max: {max_windows:,})...")
        
        skipped_short = 0
        skipped_gap = 0
        
        for idx, (mmsi, g) in enumerate(grouped):
            if idx % 10000 == 0:
                log(f"   Progression: {idx:,}/{n_groups:,} navires | {len(windows):,} fenêtres")
            
            if len(windows) >= max_windows:
                log(f"   ✅ Limite de {max_windows:,} fenêtres atteinte")
                break
            
            if len(g) < self.total_len:
                skipped_short += 1
                continue
            
            g = g.reset_index(drop=True)
            
            # Calcul des features temporelles
            g['Delta_t'] = g['BaseDateTime'].diff().dt.total_seconds().fillna(0)
            
            # Marquer les gaps trop grands
            g['Gap'] = g['Delta_t'] > self.MAX_GAP_SECONDS
            
            # Calcul accélération et ROT
            dt_safe = g['Delta_t'].replace(0, 1.0)
            g['Accel'] = g['SOG'].diff().fillna(0) / dt_safe
            
            # Rate of Turn (gestion du wrap-around 0-360)
            cog_diff = g['COG'].diff().fillna(0)
            cog_diff = (cog_diff + 180) % 360 - 180
            g['ROT'] = cog_diff / dt_safe
            
            # Clip les valeurs aberrantes
            g['Accel'] = g['Accel'].clip(-1, 1)
            g['ROT'] = g['ROT'].clip(-5, 5)
            
            arr = g[["LAT", "LON", "SOG", "COG", "Heading", "VTIDX", 
                    "Delta_t", "Accel", "ROT", "Gap"]].to_numpy(dtype=np.float32)
            
            # Créer les fenêtres en évitant les gaps
            max_start = len(g) - self.total_len + 1
            for i in range(max_start):
                window = arr[i:i + self.total_len]
                
                # Ignorer si gap dans la fenêtre
                if window[:, 9].any():  # Colonne Gap
                    skipped_gap += 1
                    continue
                
                inp = window[:self.seq_in, :9]  # Sans la colonne Gap
                out = window[self.seq_in:, :9]
                windows.append((inp, out))
                
                if len(windows) >= max_windows:
                    break
        
        log(f"   Navires trop courts: {skipped_short:,}")
        log(f"   Fenêtres avec gaps: {skipped_gap:,}")
        
        return windows
    
    def _log_stats(self):
        """Log des statistiques du dataset."""
        log(f"📊 Stats du dataset:")
        log(f"   Fenêtres: {len(self.inp):,}")
        log(f"   SOG moyen: {self.inp[:, :, 2].mean():.2f} noeuds")
        log(f"   Delta_t moyen: {self.inp[:, :, 6].mean():.1f}s")
    
    def __len__(self) -> int:
        return len(self.inp)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        inp, out = self.inp[idx], self.out[idx]
        
        # Point de référence (dernier point de l'entrée)
        base_lat, base_lon = inp[-1, 0], inp[-1, 1]
        
        # Conversion degrés -> mètres
        METER_PER_DEG_LAT = 111320.0
        meter_per_deg_lon = 40075000.0 * math.cos(math.radians(base_lat)) / 360.0
        
        # Features d'entrée normalisées (10 dimensions)
        x = np.stack([
            (inp[:, 0] - base_lat) * METER_PER_DEG_LAT / self.SCALE_POSITION,  # x en km
            (inp[:, 1] - base_lon) * meter_per_deg_lon / self.SCALE_POSITION,   # y en km
            inp[:, 2] / self.SCALE_SOG,                                          # SOG normalisé
            np.sin(np.radians(inp[:, 3])),                                       # sin(COG)
            np.cos(np.radians(inp[:, 3])),                                       # cos(COG)
            np.sin(np.radians(inp[:, 4])),                                       # sin(Heading)
            np.cos(np.radians(inp[:, 4])),                                       # cos(Heading)
            np.clip(inp[:, 6] / self.SCALE_DT, 0, 1),                           # Delta_t normalisé
            inp[:, 7] * 2.0,                                                     # Accélération
            inp[:, 8] * 0.5                                                      # ROT
        ], axis=1).astype(np.float32)
        
        # Cible: positions futures en km (relatives au point de référence)
        y = np.stack([
            (out[:, 0] - base_lat) * METER_PER_DEG_LAT / self.SCALE_POSITION,
            (out[:, 1] - base_lon) * meter_per_deg_lon / self.SCALE_POSITION
        ], axis=1).astype(np.float32)
        
        # Clip pour éviter les valeurs extrêmes
        x = np.clip(x, -100, 100)
        y = np.clip(y, -50, 50)
        
        return {
            "x": torch.from_numpy(x),
            "y": torch.from_numpy(y),
            "vtype": torch.tensor(int(inp[0, 5]), dtype=torch.long),
            "anchor": torch.tensor([base_lat, base_lon], dtype=torch.float32),
            "scale_lat": torch.tensor(METER_PER_DEG_LAT, dtype=torch.float32),
            "scale_lon": torch.tensor(meter_per_deg_lon, dtype=torch.float32)
        }


# ==========================================
# MODÈLE
# ==========================================
class PositionalEncoding(nn.Module):
    """Encodage positionnel sinusoïdal pour Transformer."""
    
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch, seq_len, d_model)
        x = x + self.pe[:x.size(1), :].transpose(0, 1)
        return self.dropout(x)


class AISTransformer(nn.Module):
    """
    Modèle Transformer pour prédiction de trajectoires AIS.
    
    Architecture:
    - Embedding du type de navire
    - Encoder Transformer avec attention multi-têtes
    - Decoder LSTM autorégressif
    - MLP de sortie
    """
    
    def __init__(self, input_dim: int = INPUT_DIM, vtype_card: int = 100, 
                 vtype_emb: int = EMBED_VT, hidden: int = HIDDEN, 
                 n_heads: int = N_HEADS, n_layers: int = N_LAYERS, 
                 dropout: float = DROPOUT, pred_len: int = SEQ_OUT):
        super().__init__()
        
        self.hidden = hidden
        self.pred_len = pred_len
        self.vtype_emb_dim = vtype_emb
        
        # Embedding type de navire
        self.vessel_embedding = nn.Embedding(vtype_card, vtype_emb)
        
        # Projection d'entrée
        self.input_proj = nn.Linear(input_dim + vtype_emb, hidden)
        self.input_norm = nn.LayerNorm(hidden)
        
        # Encodage positionnel
        self.pos_encoder = PositionalEncoding(hidden, dropout)
        
        # Encoder Transformer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden,
            nhead=n_heads,
            dim_feedforward=hidden * 4,
            dropout=dropout,
            batch_first=True,
            activation='gelu'
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.encoder_norm = nn.LayerNorm(hidden)
        
        # Decoder LSTM pour génération autorégressive
        self.decoder_cell = nn.LSTMCell(2 + vtype_emb, hidden)
        
        # Projection de sortie avec skip connection
        self.output_proj = nn.Sequential(
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Dropout(dropout / 2),
            nn.Linear(hidden // 2, 2)
        )
        
        # Initialisation des poids
        self._init_weights()
    
    def _init_weights(self):
        """Initialisation des poids Xavier/Glorot."""
        for name, p in self.named_parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
            elif 'bias' in name:
                nn.init.zeros_(p)
    
    def forward(self, x: torch.Tensor, vtype: torch.Tensor, 
                out_len: int = None, y_true: torch.Tensor = None,
                teacher_forcing_ratio: float = 0.0) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Séquence d'entrée (B, T, input_dim)
            vtype: Type de navire (B,)
            out_len: Longueur de sortie (défaut: pred_len)
            y_true: Vérité terrain pour teacher forcing (B, out_len, 2)
            teacher_forcing_ratio: Ratio de teacher forcing [0, 1]
        
        Returns:
            Prédictions (B, out_len, 2) - positions relatives en km
        """
        if out_len is None:
            out_len = self.pred_len
        
        B, T, _ = x.shape
        device = x.device
        
        # Embedding du type de navire
        v_emb = self.vessel_embedding(vtype)  # (B, vtype_emb)
        v_emb_expanded = v_emb.unsqueeze(1).expand(-1, T, -1)  # (B, T, vtype_emb)
        
        # Concaténation et projection
        x_cat = torch.cat([x, v_emb_expanded], dim=2)
        x_proj = self.input_norm(self.input_proj(x_cat))
        
        # Encodage avec Transformer
        x_enc = self.pos_encoder(x_proj)
        memory = self.encoder(x_enc)
        memory = self.encoder_norm(memory)
        
        # Décodage autorégressif avec LSTM
        h = memory[:, -1].contiguous()  # Dernier état encodé comme état initial
        c = torch.zeros_like(h)
        
        # Position initiale (0, 0 car relative au point de référence)
        prev_pos = torch.zeros(B, 2, device=device)
        
        predictions = []
        for t in range(out_len):
            # Teacher forcing: utiliser la vraie position avec probabilité tf_ratio
            if self.training and y_true is not None and random.random() < teacher_forcing_ratio:
                decoder_input = y_true[:, t, :]
            else:
                decoder_input = prev_pos
            
            # LSTM step
            lstm_input = torch.cat([decoder_input, v_emb], dim=1)
            h, c = self.decoder_cell(lstm_input, (h, c))
            
            # Prédiction de la position
            delta = self.output_proj(h)
            predictions.append(delta.unsqueeze(1))
            
            # Mise à jour pour le prochain pas
            prev_pos = delta
        
        return torch.cat(predictions, dim=1)


# ==========================================
# VISUALISATION
# ==========================================
class TrainingVisualizer:
    """Gestion des visualisations d'entraînement."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.history = {
            'train_loss': [], 'val_loss': [],
            'ade': [], 'fde': [],
            'lr': []
        }
    
    def update(self, epoch_data: Dict[str, float]):
        """Met à jour l'historique."""
        for key in self.history:
            if key in epoch_data:
                self.history[key].append(epoch_data[key])
    
    def plot_training_curves(self):
        """Génère les courbes d'entraînement."""
        if not self.history['train_loss']:
            return
            
        epochs = range(1, len(self.history['train_loss']) + 1)
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Loss
        ax = axes[0, 0]
        ax.plot(epochs, self.history['train_loss'], 'b-', label='Train Loss', linewidth=2)
        ax.plot(epochs, self.history['val_loss'], 'r-', label='Val Loss', linewidth=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Loss (MSE)')
        ax.set_title('Training & Validation Loss')
        ax.legend()
        ax.grid(True, alpha=0.3)
        if min(self.history['val_loss']) > 0:
            ax.set_yscale('log')
        
        # ADE
        ax = axes[0, 1]
        ax.plot(epochs, self.history['ade'], 'g-', linewidth=2)
        ax.axhline(y=min(self.history['ade']), color='g', linestyle='--', alpha=0.5,
                   label=f'Best: {min(self.history["ade"]):.0f}m')
        ax.set_xlabel('Epoch')
        ax.set_ylabel('ADE (mètres)')
        ax.set_title('Average Displacement Error')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # FDE
        ax = axes[1, 0]
        ax.plot(epochs, self.history['fde'], 'm-', linewidth=2)
        ax.axhline(y=min(self.history['fde']), color='m', linestyle='--', alpha=0.5,
                   label=f'Best: {min(self.history["fde"]):.0f}m')
        ax.set_xlabel('Epoch')
        ax.set_ylabel('FDE (mètres)')
        ax.set_title('Final Displacement Error')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Learning Rate
        ax = axes[1, 1]
        ax.plot(epochs, self.history['lr'], 'orange', linewidth=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Learning Rate')
        ax.set_title('Learning Rate Schedule')
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'training_curves.png', dpi=150, bbox_inches='tight')
        plt.close()
        log("📊 Courbes sauvegardées: training_curves.png")
    
    def plot_predictions(self, model: nn.Module, val_loader: DataLoader, 
                         device: torch.device, n_samples: int = 6):
        """Visualise des prédictions exemples."""
        model.eval()
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        sample_count = 0
        
        with torch.no_grad():
            for batch in val_loader:
                if sample_count >= n_samples:
                    break
                
                x = batch["x"].to(device)
                y = batch["y"].to(device)
                vtype = batch["vtype"].to(device)
                
                pred = model(x, vtype)
                
                batch_size = min(n_samples - sample_count, x.size(0))
                for i in range(batch_size):
                    ax = axes[sample_count]
                    
                    # Entrée (x, y en km)
                    inp = x[i].cpu().numpy()
                    ax.plot(inp[:, 1], inp[:, 0], 'b.-', label='Entrée', 
                           linewidth=2, markersize=6)
                    
                    # Vérité terrain
                    tgt = y[i].cpu().numpy()
                    ax.plot(tgt[:, 1], tgt[:, 0], 'g.-', label='Vérité', 
                           linewidth=2, markersize=6)
                    
                    # Prédiction
                    prd = pred[i].cpu().numpy()
                    ax.plot(prd[:, 1], prd[:, 0], 'r.--', label='Prédiction', 
                           linewidth=2, markersize=6)
                    
                    # Connexion entre fin d'entrée et début sortie
                    ax.plot([inp[-1, 1], tgt[0, 1]], [inp[-1, 0], tgt[0, 0]], 
                           'g--', alpha=0.5, linewidth=1)
                    ax.plot([inp[-1, 1], prd[0, 1]], [inp[-1, 0], prd[0, 0]], 
                           'r--', alpha=0.5, linewidth=1)
                    
                    # Calcul erreur pour ce sample
                    sample_error = np.mean(np.sqrt(np.sum((prd - tgt)**2, axis=1))) * 1000  # en mètres
                    
                    ax.set_xlabel('X (km)')
                    ax.set_ylabel('Y (km)')
                    ax.set_title(f'Sample {sample_count + 1} - Err: {sample_error:.0f}m')
                    ax.legend(fontsize=8, loc='best')
                    ax.grid(True, alpha=0.3)
                    ax.set_aspect('equal')
                    
                    sample_count += 1
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'sample_predictions.png', dpi=150, bbox_inches='tight')
        plt.close()
        log("📊 Prédictions sauvegardées: sample_predictions.png")
        model.train()
    
    def plot_error_distribution(self, errors_per_horizon: List[Dict]):
        """Visualise la distribution des erreurs par horizon."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        timesteps = [e['timestep'] for e in errors_per_horizon]
        means = [e['mean_error'] for e in errors_per_horizon]
        stds = [e['std_error'] for e in errors_per_horizon]
        p90s = [e['p90_error'] for e in errors_per_horizon]
        
        ax.plot(timesteps, means, 'b-o', label='Mean Error', linewidth=2)
        ax.fill_between(timesteps, 
                        [m - s for m, s in zip(means, stds)],
                        [m + s for m, s in zip(means, stds)],
                        alpha=0.3, color='blue')
        ax.plot(timesteps, p90s, 'r--', label='90th Percentile', linewidth=2)
        
        ax.set_xlabel('Prediction Horizon (timestep)')
        ax.set_ylabel('Error (meters)')
        ax.set_title('Prediction Error by Horizon')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'error_by_horizon.png', dpi=150, bbox_inches='tight')
        plt.close()
        log("📊 Distribution des erreurs sauvegardée: error_by_horizon.png")
    
    def save_history(self):
        """Sauvegarde l'historique en CSV."""
        df = pd.DataFrame(self.history)
        df.index = range(1, len(df) + 1)
        df.index.name = 'epoch'
        df.to_csv(self.output_dir / 'training_history.csv')
        log("📊 Historique sauvegardé: training_history.csv")


# ==========================================
# ENTRAÎNEMENT
# ==========================================
def train_epoch(model: nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer,
                device: torch.device, teacher_forcing_ratio: float = 0.0) -> Tuple[float, float]:
    """
    Entraîne un epoch.
    
    Returns:
        (loss moyenne, gradient norm moyen)
    """
    model.train()
    total_loss = 0
    total_grad_norm = 0
    n_samples = 0
    n_batches = 0
    
    criterion = nn.MSELoss()
    
    pbar = tqdm(loader, desc="Train", leave=False)
    for batch in pbar:
        x = batch["x"].to(device)
        y = batch["y"].to(device)
        vtype = batch["vtype"].to(device)
        
        optimizer.zero_grad()
        
        pred = model(x, vtype, out_len=y.size(1), y_true=y, 
                    teacher_forcing_ratio=teacher_forcing_ratio)
        
        loss = criterion(pred, y)
        loss.backward()
        
        # Gradient clipping et calcul de la norme
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        
        batch_size = x.size(0)
        total_loss += loss.item() * batch_size
        total_grad_norm += grad_norm.item()
        n_samples += batch_size
        n_batches += 1
        
        # Mise à jour de la barre de progression
        pbar.set_postfix({'loss': f'{loss.item():.4f}'})
    
    return total_loss / n_samples, total_grad_norm / n_batches


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device, 
             compute_full_metrics: bool = False) -> Tuple[float, float, float, Optional[List]]:
    """
    Évalue le modèle.
    
    Returns:
        (loss, ADE, FDE, errors_per_horizon si compute_full_metrics)
    """
    model.eval()
    criterion = nn.MSELoss()
    
    total_loss = 0
    n_samples = 0
    
    all_preds = []
    all_targets = []
    all_anchors = []
    all_scale_lat = []
    all_scale_lon = []
    
    with torch.no_grad():
        for batch in tqdm(loader, desc="Eval", leave=False):
            x = batch["x"].to(device)
            y = batch["y"].to(device)
            vtype = batch["vtype"].to(device)
            
            pred = model(x, vtype, out_len=y.size(1))
            
            loss = criterion(pred, y)
            total_loss += loss.item() * x.size(0)
            n_samples += x.size(0)
            
            all_preds.append(pred.cpu().numpy())
            all_targets.append(y.cpu().numpy())
            all_anchors.append(batch["anchor"].numpy())
            all_scale_lat.append(batch["scale_lat"].numpy())
            all_scale_lon.append(batch["scale_lon"].numpy())
    
    avg_loss = total_loss / n_samples
    
    # Reconvertir en lat/lon pour calculer ADE/FDE
    preds = np.concatenate(all_preds, axis=0)
    targets = np.concatenate(all_targets, axis=0)
    anchors = np.concatenate(all_anchors, axis=0)
    scale_lat = np.concatenate(all_scale_lat, axis=0)
    scale_lon = np.concatenate(all_scale_lon, axis=0)
    
    # Reconversion km -> degrés
    preds_ll = np.zeros_like(preds)
    targets_ll = np.zeros_like(targets)
    
    SCALE = AISDataset.SCALE_POSITION
    
    for i in range(len(preds)):
        lat, lon = anchors[i]
        
        # Prédictions: km -> degrés
        preds_ll[i, :, 0] = lat + (preds[i, :, 0] * SCALE) / scale_lat[i]
        preds_ll[i, :, 1] = lon + (preds[i, :, 1] * SCALE) / scale_lon[i]
        
        # Cibles: km -> degrés
        targets_ll[i, :, 0] = lat + (targets[i, :, 0] * SCALE) / scale_lat[i]
        targets_ll[i, :, 1] = lon + (targets[i, :, 1] * SCALE) / scale_lon[i]
    
    ade, fde = compute_ade_fde(preds_ll, targets_ll)
    
    errors_per_horizon = None
    if compute_full_metrics:
        errors_per_horizon = compute_metrics_per_horizon(preds_ll, targets_ll)
    
    return avg_loss, ade, fde, errors_per_horizon


# ==========================================
# MAIN
# ==========================================
def main():
    """Fonction principale d'entraînement."""
    log("=" * 70)
    log("🚢 AIS Trajectory Prediction - Training Script")
    log("=" * 70)
    log(f"📅 Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📝 Logs: {LOG_FILE}")
    
    # Setup
    set_seed(SEED)
    device = setup_device()
    
    log(f"\n📋 Configuration:")
    log(f"   Séquence: {SEQ_IN} entrée -> {SEQ_OUT} sortie")
    log(f"   Dataset: Train={TRAIN_SIZE:,} | Val={VAL_SIZE:,}")
    log(f"   Batch: {BATCH_SIZE} | LR: {LR}")
    log(f"   Epochs: max {EPOCHS} | Patience: {PATIENCE} | Min epochs: {MIN_EPOCHS}")
    log(f"   Architecture: Hidden={HIDDEN} | Heads={N_HEADS} | Layers={N_LAYERS}")
    
    # Charger les données
    df = load_data_from_db()
    
    # Créer le dataset
    log("\n📦 Création du dataset...")
    full_dataset = AISDataset(df, max_windows=TRAIN_SIZE + VAL_SIZE)
    del df  # Libérer la mémoire
    
    # Split train/val
    n_total = len(full_dataset)
    n_train = min(TRAIN_SIZE, int(0.8 * n_total))
    n_val = min(VAL_SIZE, n_total - n_train)
    n_unused = n_total - n_train - n_val
    
    train_dataset, val_dataset, _ = torch.utils.data.random_split(
        full_dataset, [n_train, n_val, n_unused],
        generator=torch.Generator().manual_seed(SEED)
    )
    
    log(f"   Train: {len(train_dataset):,} | Val: {len(val_dataset):,}")
    
    # DataLoaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=BATCH_SIZE, 
        shuffle=True,
        num_workers=NUM_WORKERS, 
        pin_memory=True,
        drop_last=True
    )
    val_loader = DataLoader(
        val_dataset, 
        batch_size=BATCH_SIZE, 
        shuffle=False,
        num_workers=NUM_WORKERS, 
        pin_memory=True
    )
    
    # Modèle
    n_vessel_types = len(full_dataset.vtype2idx)
    log(f"\n🏗️ Création du modèle (VesselTypes: {n_vessel_types})...")
    
    model = AISTransformer(
        input_dim=INPUT_DIM,
        vtype_card=max(n_vessel_types, 100),
        vtype_emb=EMBED_VT,
        hidden=HIDDEN,
        n_heads=N_HEADS,
        n_layers=N_LAYERS,
        dropout=DROPOUT,
        pred_len=SEQ_OUT
    )
    
    # Multi-GPU si disponible
    if torch.cuda.device_count() > 1:
        log(f"🔥 Utilisation de DataParallel sur {torch.cuda.device_count()} GPUs")
        model = nn.DataParallel(model)
    
    model = model.to(device)
    
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log(f"   Paramètres: {n_params:,}")
    
    # Optimiseur et scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    scheduler = ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3, 
        min_lr=1e-7, verbose=False
    )
    
    # Early stopping avec sauvegarde des meilleurs poids
    model_for_es = model.module if hasattr(model, 'module') else model
    early_stopping = EarlyStopping(
        patience=PATIENCE, 
        min_delta=MIN_DELTA, 
        min_epochs=MIN_EPOCHS,
        restore_best=True
    )
    
    # Visualisation
    visualizer = TrainingVisualizer(OUTPUT_DIR)
    
    # Entraînement
    log("\n" + "=" * 70)
    log("🚀 Début de l'entraînement")
    log("=" * 70)
    
    best_val_loss = float('inf')
    best_ade = float('inf')
    best_fde = float('inf')
    best_epoch = 0
    
    training_start = datetime.now()
    
    for epoch in range(1, EPOCHS + 1):
        epoch_start = datetime.now()
        
        # Teacher forcing décroissant progressif
        # Commence à 0.5 et décroit jusqu'à 0 sur 40 epochs
        tf_ratio = max(0.0, 0.5 * (1 - epoch / 40))
        
        # Train
        train_loss, grad_norm = train_epoch(
            model, train_loader, optimizer, device, tf_ratio
        )
        
        # Validation
        val_loss, ade, fde, _ = evaluate(model, val_loader, device)
        
        # Update scheduler basé sur val_loss
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]['lr']
        
        # Update visualizer
        visualizer.update({
            'train_loss': train_loss,
            'val_loss': val_loss,
            'ade': ade,
            'fde': fde,
            'lr': current_lr
        })
        
        epoch_time = (datetime.now() - epoch_start).total_seconds()
        
        # Log
        improved = ""
        if val_loss < best_val_loss:
            improved = " ⭐"
            best_val_loss = val_loss
            best_ade = ade
            best_fde = fde
            best_epoch = epoch
            
            # Sauvegarder le meilleur modèle
            model_to_save = model.module if hasattr(model, 'module') else model
            torch.save({
                'epoch': epoch,
                'model_state_dict': model_to_save.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'val_loss': val_loss,
                'ade': ade,
                'fde': fde,
                'vtype2idx': full_dataset.vtype2idx,
                'config': {
                    'input_dim': INPUT_DIM,
                    'hidden': HIDDEN,
                    'n_heads': N_HEADS,
                    'n_layers': N_LAYERS,
                    'seq_in': SEQ_IN,
                    'seq_out': SEQ_OUT,
                    'vtype_card': max(n_vessel_types, 100),
                    'vtype_emb': EMBED_VT,
                    'dropout': DROPOUT
                }
            }, OUTPUT_DIR / 'best_model.pth')
        
        log(f"Epoch {epoch:3d}/{EPOCHS} | "
            f"Loss: {train_loss:.4f}/{val_loss:.4f} | "
            f"ADE: {ade:.0f}m | FDE: {fde:.0f}m | "
            f"LR: {current_lr:.1e} | "
            f"GradNorm: {grad_norm:.2f} | "
            f"{epoch_time:.1f}s{improved}")
        
        # Early stopping (basé sur val_loss)
        if early_stopping(val_loss, epoch, model_for_es):
            log(f"\n🛑 Early Stopping déclenché à l'epoch {epoch}")
            summary = early_stopping.get_summary()
            log(f"   Meilleur: epoch {summary['best_epoch']}, loss={summary['best_score']:.4f}")
            break
    
    # Fin de l'entraînement
    training_time = (datetime.now() - training_start).total_seconds() / 60
    
    log("\n" + "=" * 70)
    log("✅ Entraînement terminé!")
    log("=" * 70)
    log(f"   Durée totale: {training_time:.1f} minutes")
    log(f"   Epochs effectués: {epoch}")
    log(f"   Meilleur epoch: {best_epoch}")
    log(f"   Meilleur Val Loss: {best_val_loss:.4f}")
    log(f"   Meilleur ADE: {best_ade:.0f}m")
    log(f"   Meilleur FDE: {best_fde:.0f}m")
    log(f"   Modèle: {OUTPUT_DIR / 'best_model.pth'}")
    
    # Restaurer les meilleurs poids si early stopping
    if early_stopping.early_stop and early_stopping.restore_best:
        early_stopping.restore_best_weights(model_for_es)
    
    # Charger le meilleur modèle pour l'évaluation finale
    checkpoint = torch.load(OUTPUT_DIR / 'best_model.pth')
    model_to_load = model.module if hasattr(model, 'module') else model
    model_to_load.load_state_dict(checkpoint['model_state_dict'])
    
    # Évaluation finale avec métriques complètes
    log("\n📊 Évaluation finale avec métriques détaillées...")
    final_loss, final_ade, final_fde, errors_per_horizon = evaluate(
        model, val_loader, device, compute_full_metrics=True
    )
    
    log(f"   Final Val Loss: {final_loss:.4f}")
    log(f"   Final ADE: {final_ade:.0f}m")
    log(f"   Final FDE: {final_fde:.0f}m")
    
    if errors_per_horizon:
        log("   Erreur par horizon:")
        for e in errors_per_horizon:
            log(f"     t+{e['timestep']}: {e['mean_error']:.0f}m (±{e['std_error']:.0f}m)")
    
    # Visualisations finales
    log("\n📊 Génération des visualisations...")
    visualizer.plot_training_curves()
    visualizer.save_history()
    visualizer.plot_predictions(model, val_loader, device)
    
    if errors_per_horizon:
        visualizer.plot_error_distribution(errors_per_horizon)
    
    log("\n📁 Fichiers générés:")
    for f in sorted(OUTPUT_DIR.glob('*')):
        size = f.stat().st_size / 1024  # KB
        log(f"   - {f.name} ({size:.1f} KB)")
    
    log(f"\n🎉 Entraînement complété avec succès!")
    log(f"📝 Logs complets: {LOG_FILE}")
    
    return model, visualizer.history


if __name__ == "__main__":
    main()
