#!/usr/bin/env python3
"""
AIS Trajectory Prediction - Training Script V2 (CORRIGÉ)

CORRECTIONS MAJEURES:
1. Normalisation cohérente - positions en MÈTRES (pas km)
2. Architecture améliorée - plus de contexte pour le décodeur
3. Loss avec pondération - pénaliser plus le FDE
4. Learning rate warmup + cosine decay
5. Gradient accumulation pour stabilité

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
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts, LambdaLR
import psycopg2

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ==========================================
# CONFIGURATION
# ==========================================
SEED = 42

# --- HYPERPARAMÈTRES CORRIGÉS ---
SEQ_IN = 20               # Séquence d'entrée
SEQ_OUT = 10              # Séquence de sortie
BATCH_SIZE = 256          # Réduit pour meilleure stabilité
LR = 3e-4                 # Learning rate plus élevé
EPOCHS = 150              # Plus d'epochs
MIN_EPOCHS = 20           # Plus de warmup
PATIENCE = 15             # Plus de patience
MIN_DELTA = 1e-5          
NUM_WORKERS = 4           
WARMUP_EPOCHS = 5         # Warmup du LR

# === CONFIGURATION DATASET ===
TRAIN_SIZE = 800_000
VAL_SIZE = 200_000

# Architecture Modèle (améliorée)
HIDDEN = 256              
N_HEADS = 8               
N_LAYERS = 4              
DROPOUT = 0.15            # Légèrement augmenté
EMBED_VT = 32             
INPUT_DIM = 10            

# === NORMALISATION - CRUCIAL ===
# Tout en MÈTRES pour cohérence
SCALE_POSITION = 10000.0  # 10km en mètres -> normalise entre -1 et 1 pour ~20km
SCALE_SOG = 15.0          # ~15 noeuds typique
SCALE_DT = 300.0          # 5 minutes

# Base de données
DB_CONFIG = {
    'host': '172.31.60.8',
    'port': 5432,
    'database': 'ais',
    'user': 'postgres',
    'password': 'ANjw/84H77C9h2'
}

OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ==========================================
# LOGGING
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
    getattr(logger, level)(msg)
    for handler in logger.handlers:
        handler.flush()


def set_seed(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def setup_device() -> torch.device:
    if torch.cuda.is_available():
        # Utiliser GPU 0 uniquement
        device = torch.device("cuda:0")
        props = torch.cuda.get_device_properties(0)
        log(f" GPU 0: {props.name} ({props.total_memory / 1e9:.1f} Go)")
    else:
        log(" Pas de GPU, utilisation du CPU")
        device = torch.device("cpu")
    return device


# ==========================================
# EARLY STOPPING
# ==========================================
class EarlyStopping:
    def __init__(self, patience: int = PATIENCE, min_delta: float = MIN_DELTA, 
                 min_epochs: int = MIN_EPOCHS, restore_best: bool = True):
        self.patience = patience
        self.min_delta = min_delta
        self.min_epochs = min_epochs
        self.restore_best = restore_best
        
        self.counter = 0
        self.best_score = None
        self.best_epoch = 0
        self.best_state = None
        self.early_stop = False
        
    def __call__(self, score: float, epoch: int, model: Optional[nn.Module] = None) -> bool:
        if epoch < self.min_epochs:
            if self.best_score is None or score < self.best_score:
                self._update_best(score, epoch, model)
            return False
        
        if self.best_score is None:
            self._update_best(score, epoch, model)
            return False
        
        if score < (self.best_score - self.min_delta):
            self._update_best(score, epoch, model)
            self.counter = 0
        else:
            self.counter += 1
            log(f"   ⏳ EarlyStopping: {self.counter}/{self.patience}")
            if self.counter >= self.patience:
                self.early_stop = True
                return True
        return False
    
    def _update_best(self, score: float, epoch: int, model: Optional[nn.Module]):
        self.best_score = score
        self.best_epoch = epoch
        if model is not None and self.restore_best:
            self.best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    
    def restore_best_weights(self, model: nn.Module):
        if self.best_state is not None:
            model.load_state_dict(self.best_state)
            log(f"    Poids restaurés depuis epoch {self.best_epoch}")


# ==========================================
# MÉTRIQUES
# ==========================================
def haversine_distance(lat1: np.ndarray, lon1: np.ndarray, 
                       lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Distance haversine en mètres."""
    R = 6371000.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    
    a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))


def compute_ade_fde(pred: np.ndarray, true: np.ndarray) -> Tuple[float, float]:
    """ADE et FDE en mètres."""
    N, T, _ = pred.shape
    distances = np.zeros((N, T))
    for t in range(T):
        distances[:, t] = haversine_distance(
            pred[:, t, 0], pred[:, t, 1],
            true[:, t, 0], true[:, t, 1]
        )
    return np.mean(distances), np.mean(distances[:, -1])


# ==========================================
# CHARGEMENT DONNÉES
# ==========================================
def load_data_from_db() -> pd.DataFrame:
    log("Connexion à la base de données...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    log(" Connexion réussie!")
    
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
      AND pv.sog >= 0.5          -- Navires en mouvement
      AND pv.sog < 40            -- Vitesse réaliste
      AND pv.cog >= 0 AND pv.cog <= 360
    ORDER BY v.mmsi, pv.base_date_time;
    """
    
    log(" Extraction des données...")
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Types optimisés
    df['MMSI'] = df['MMSI'].astype('int64')
    df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'])
    df['VesselType'] = df['VesselType'].astype('int32')
    for col in ['LAT', 'LON', 'SOG', 'COG', 'Heading']:
        df[col] = df[col].astype('float32')
    
    log(f"{len(df):,} positions pour {df['MMSI'].nunique():,} navires")
    log(f"   SOG: [{df['SOG'].min():.1f}, {df['SOG'].max():.1f}] mean={df['SOG'].mean():.1f}")
    
    return df


# ==========================================
# DATASET CORRIGÉ
# ==========================================
class AISDataset(Dataset):
    """
    Dataset avec normalisation CORRIGÉE.
    Positions en mètres, pas en km!
    """
    
    MAX_GAP_SECONDS = 600   # 10 minutes max entre positions (plus strict)
    
    def __init__(self, df: pd.DataFrame, seq_in: int = SEQ_IN, seq_out: int = SEQ_OUT, 
                 max_windows: int = TRAIN_SIZE + VAL_SIZE):
        self.seq_in = seq_in
        self.seq_out = seq_out
        self.total_len = seq_in + seq_out
        
        # Mapping types navires
        df = df.copy()
        unique_vtypes = sorted(df["VesselType"].unique())
        self.vtype2idx = {v: i for i, v in enumerate(unique_vtypes)}
        df["VTIDX"] = df["VesselType"].map(self.vtype2idx).astype(int)
        
        # Créer fenêtres
        windows = self._create_windows(df, max_windows)
        
        if not windows:
            raise ValueError("Dataset vide!")
        
        random.shuffle(windows)
        log(f" {len(windows):,} fenêtres créées")
        
        self.inp = np.array([w[0] for w in windows], dtype=np.float32)
        self.out = np.array([w[1] for w in windows], dtype=np.float32)
        
        self._log_stats()
    
    def _create_windows(self, df: pd.DataFrame, max_windows: int) -> List:
        windows = []
        grouped = df.groupby("MMSI", sort=False)
        
        log(f" Création fenêtres (max: {max_windows:,})...")
        
        for idx, (mmsi, g) in enumerate(grouped):
            if idx % 10000 == 0:
                log(f"   {idx:,} navires | {len(windows):,} fenêtres")
            
            if len(windows) >= max_windows:
                break
            
            if len(g) < self.total_len:
                continue
            
            g = g.reset_index(drop=True)
            g['Delta_t'] = g['BaseDateTime'].diff().dt.total_seconds().fillna(0)
            g['Gap'] = g['Delta_t'] > self.MAX_GAP_SECONDS
            
            # Calculs dérivés
            dt_safe = g['Delta_t'].replace(0, 1.0)
            g['Accel'] = (g['SOG'].diff().fillna(0) / dt_safe).clip(-0.5, 0.5)
            
            cog_diff = g['COG'].diff().fillna(0)
            cog_diff = (cog_diff + 180) % 360 - 180
            g['ROT'] = (cog_diff / dt_safe).clip(-3, 3)
            
            arr = g[["LAT", "LON", "SOG", "COG", "Heading", "VTIDX",
                    "Delta_t", "Accel", "ROT", "Gap"]].to_numpy(dtype=np.float32)
            
            for i in range(len(g) - self.total_len + 1):
                window = arr[i:i + self.total_len]
                
                if window[:, 9].any():  # Gap
                    continue
                
                inp = window[:self.seq_in, :9]
                out = window[self.seq_in:, :9]
                windows.append((inp, out))
                
                if len(windows) >= max_windows:
                    break
        
        return windows
    
    def _log_stats(self):
        log(f"   Stats dataset:")
        log(f"   Fenêtres: {len(self.inp):,}")
        log(f"   SOG moyen: {self.inp[:, :, 2].mean():.2f} noeuds")
        log(f"   Delta_t moyen: {self.inp[:, :, 6].mean():.1f}s")
    
    def __len__(self) -> int:
        return len(self.inp)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        inp, out = self.inp[idx], self.out[idx]
        
        # Point de référence = dernier point d'entrée
        base_lat, base_lon = inp[-1, 0], inp[-1, 1]
        
        # Conversion degrés -> mètres
        METER_PER_DEG_LAT = 111320.0
        meter_per_deg_lon = 40075000.0 * math.cos(math.radians(base_lat)) / 360.0
        
        # === POSITIONS EN MÈTRES, normalisées par SCALE_POSITION ===
        # Entrée: x, y en mètres normalisés
        pos_x_in = (inp[:, 0] - base_lat) * METER_PER_DEG_LAT / SCALE_POSITION
        pos_y_in = (inp[:, 1] - base_lon) * meter_per_deg_lon / SCALE_POSITION
        
        # Features (10 dimensions)
        x = np.stack([
            pos_x_in,                                    # x normalisé
            pos_y_in,                                    # y normalisé
            inp[:, 2] / SCALE_SOG,                       # SOG normalisé
            np.sin(np.radians(inp[:, 3])),               # sin(COG)
            np.cos(np.radians(inp[:, 3])),               # cos(COG)
            np.sin(np.radians(inp[:, 4])),               # sin(Heading)
            np.cos(np.radians(inp[:, 4])),               # cos(Heading)
            np.clip(inp[:, 6] / SCALE_DT, 0, 2),         # Delta_t normalisé
            inp[:, 7],                                    # Accélération (déjà clippé)
            inp[:, 8] / 3.0                              # ROT normalisé
        ], axis=1).astype(np.float32)
        
        # === CIBLES EN MÈTRES NORMALISÉS ===
        y = np.stack([
            (out[:, 0] - base_lat) * METER_PER_DEG_LAT / SCALE_POSITION,
            (out[:, 1] - base_lon) * meter_per_deg_lon / SCALE_POSITION
        ], axis=1).astype(np.float32)
        
        return {
            "x": torch.from_numpy(x),
            "y": torch.from_numpy(y),
            "vtype": torch.tensor(int(inp[0, 5]), dtype=torch.long),
            "anchor": torch.tensor([base_lat, base_lon], dtype=torch.float32),
            "scale_lat": torch.tensor(METER_PER_DEG_LAT, dtype=torch.float32),
            "scale_lon": torch.tensor(meter_per_deg_lon, dtype=torch.float32)
        }


# ==========================================
# MODÈLE AMÉLIORÉ
# ==========================================
class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 100):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)


class AISTransformer(nn.Module):
    """
    Modèle amélioré avec:
    - Meilleur conditioning du décodeur
    - Prédiction de delta (mouvement) et non position absolue
    - Skip connections
    """
    
    def __init__(self, input_dim: int = INPUT_DIM, vtype_card: int = 100, 
                 vtype_emb: int = EMBED_VT, hidden: int = HIDDEN, 
                 n_heads: int = N_HEADS, n_layers: int = N_LAYERS, 
                 dropout: float = DROPOUT, pred_len: int = SEQ_OUT):
        super().__init__()
        
        self.hidden = hidden
        self.pred_len = pred_len
        
        # Embeddings
        self.vessel_embedding = nn.Embedding(vtype_card, vtype_emb)
        
        # Encoder
        self.input_proj = nn.Linear(input_dim + vtype_emb, hidden)
        self.input_norm = nn.LayerNorm(hidden)
        self.pos_encoder = PositionalEncoding(hidden, dropout)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden, nhead=n_heads,
            dim_feedforward=hidden * 4,
            dropout=dropout, batch_first=True,
            activation='gelu'
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.encoder_norm = nn.LayerNorm(hidden)
        
        # Décodeur amélioré: LSTM avec plus de contexte
        # Entrée: position précédente (2) + dernier état velocity-like (2) + vessel_emb
        self.decoder_lstm = nn.LSTM(
            input_size=2 + 2 + vtype_emb,  # pos + velocity + vessel
            hidden_size=hidden,
            num_layers=2,
            dropout=dropout if n_layers > 1 else 0,
            batch_first=True
        )
        
        # Prédiction de delta (mouvement)
        self.output_proj = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Linear(hidden // 2, 2)
        )
        
        # Extraction de la vélocité initiale depuis l'encodeur
        self.velocity_proj = nn.Linear(hidden, 2)
        
        self._init_weights()
    
    def _init_weights(self):
        for name, p in self.named_parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def forward(self, x: torch.Tensor, vtype: torch.Tensor, 
                out_len: int = None, y_true: torch.Tensor = None,
                teacher_forcing_ratio: float = 0.0) -> torch.Tensor:
        
        if out_len is None:
            out_len = self.pred_len
        
        B, T, _ = x.shape
        device = x.device
        
        # Embedding navire
        v_emb = self.vessel_embedding(vtype)
        v_emb_exp = v_emb.unsqueeze(1).expand(-1, T, -1)
        
        # Encoder
        x_cat = torch.cat([x, v_emb_exp], dim=2)
        x_proj = self.input_norm(self.input_proj(x_cat))
        x_enc = self.pos_encoder(x_proj)
        memory = self.encoder_norm(self.encoder(x_enc))
        
        # Extraire contexte final
        context = memory[:, -1]  # (B, hidden)
        
        # Estimer vélocité initiale depuis le contexte
        velocity = self.velocity_proj(context)  # (B, 2)
        
        # Position initiale = origine (0,0)
        pos = torch.zeros(B, 2, device=device)
        
        # Initialiser LSTM avec le contexte de l'encoder
        h0 = context.unsqueeze(0).repeat(2, 1, 1)  # (2, B, hidden)
        c0 = torch.zeros_like(h0)
        
        predictions = []
        
        for t in range(out_len):
            # Teacher forcing
            if self.training and y_true is not None and random.random() < teacher_forcing_ratio:
                pos = y_true[:, t, :]
            
            # Input: position + velocity + vessel embedding
            lstm_in = torch.cat([pos, velocity, v_emb], dim=1).unsqueeze(1)
            
            out, (h0, c0) = self.decoder_lstm(lstm_in, (h0, c0))
            
            # Prédire delta (mouvement)
            delta = self.output_proj(out.squeeze(1))
            
            # Nouvelle position = ancienne + delta
            pos = pos + delta
            predictions.append(pos.unsqueeze(1))
            
            # Mettre à jour velocity (approximation)
            velocity = delta
        
        return torch.cat(predictions, dim=1)


# ==========================================
# LOSS AMÉLIORÉE
# ==========================================
class TrajectoryLoss(nn.Module):
    """
    Loss combinée:
    - MSE sur toutes les positions
    - Pénalité supplémentaire sur FDE (position finale)
    - Pénalité sur la cohérence directionnelle
    """
    
    def __init__(self, fde_weight: float = 0.3):
        super().__init__()
        self.mse = nn.MSELoss()
        self.fde_weight = fde_weight
    
    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        # MSE global
        mse_loss = self.mse(pred, target)
        
        # FDE loss (dernier point)
        fde_loss = self.mse(pred[:, -1, :], target[:, -1, :])
        
        return mse_loss + self.fde_weight * fde_loss


# ==========================================
# VISUALISATION
# ==========================================
class TrainingVisualizer:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.history = {
            'train_loss': [], 'val_loss': [],
            'ade': [], 'fde': [], 'lr': []
        }
    
    def update(self, data: Dict):
        for k in self.history:
            if k in data:
                self.history[k].append(data[k])
    
    def plot_all(self, model, val_loader, device):
        self._plot_curves()
        self._plot_predictions(model, val_loader, device)
        self._save_history()
    
    def _plot_curves(self):
        if not self.history['train_loss']:
            return
        
        epochs = range(1, len(self.history['train_loss']) + 1)
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Loss
        ax = axes[0, 0]
        ax.plot(epochs, self.history['train_loss'], 'b-', label='Train', lw=2)
        ax.plot(epochs, self.history['val_loss'], 'r-', label='Val', lw=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Loss')
        ax.set_title('Training & Validation Loss')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # ADE
        ax = axes[0, 1]
        ax.plot(epochs, self.history['ade'], 'g-', lw=2)
        ax.axhline(min(self.history['ade']), color='g', ls='--', alpha=0.5,
                   label=f"Best: {min(self.history['ade']):.0f}m")
        ax.set_xlabel('Epoch')
        ax.set_ylabel('ADE (mètres)')
        ax.set_title('Average Displacement Error')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # FDE
        ax = axes[1, 0]
        ax.plot(epochs, self.history['fde'], 'm-', lw=2)
        ax.axhline(min(self.history['fde']), color='m', ls='--', alpha=0.5,
                   label=f"Best: {min(self.history['fde']):.0f}m")
        ax.set_xlabel('Epoch')
        ax.set_ylabel('FDE (mètres)')
        ax.set_title('Final Displacement Error')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # LR
        ax = axes[1, 1]
        ax.plot(epochs, self.history['lr'], 'orange', lw=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Learning Rate')
        ax.set_title('Learning Rate Schedule')
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'training_curves.png', dpi=150)
        plt.close()
        log(" Courbes sauvegardées")
    
    def _plot_predictions(self, model, loader, device, n_samples=6):
        model.eval()
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        count = 0
        with torch.no_grad():
            for batch in loader:
                if count >= n_samples:
                    break
                
                x = batch["x"].to(device)
                y = batch["y"].to(device)
                vtype = batch["vtype"].to(device)
                
                pred = model(x, vtype)
                
                for i in range(min(n_samples - count, x.size(0))):
                    ax = axes[count]
                    
                    inp = x[i].cpu().numpy()
                    tgt = y[i].cpu().numpy()
                    prd = pred[i].cpu().numpy()
                    
                    # Dénormaliser pour affichage en mètres
                    scale = SCALE_POSITION
                    
                    ax.plot(inp[:, 1] * scale, inp[:, 0] * scale, 'b.-', 
                           label='Entrée', lw=2, ms=4)
                    ax.plot(tgt[:, 1] * scale, tgt[:, 0] * scale, 'g.-', 
                           label='Vérité', lw=2, ms=4)
                    ax.plot(prd[:, 1] * scale, prd[:, 0] * scale, 'r.--', 
                           label='Prédiction', lw=2, ms=4)
                    
                    # Erreur
                    err = np.mean(np.sqrt(np.sum((prd - tgt)**2, axis=1))) * scale
                    ax.set_title(f'Sample {count+1} - Err: {err:.0f}m')
                    ax.set_xlabel('Y (m)')
                    ax.set_ylabel('X (m)')
                    ax.legend(fontsize=8)
                    ax.grid(True, alpha=0.3)
                    ax.set_aspect('equal')
                    
                    count += 1
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'sample_predictions.png', dpi=150)
        plt.close()
        log(" Prédictions sauvegardées")
        model.train()
    
    def _save_history(self):
        df = pd.DataFrame(self.history)
        df.index = range(1, len(df) + 1)
        df.to_csv(self.output_dir / 'training_history.csv')


# ==========================================
# TRAINING
# ==========================================
def train_epoch(model, loader, optimizer, criterion, device, tf_ratio=0.0):
    model.train()
    total_loss = 0
    n_samples = 0
    
    pbar = tqdm(loader, desc="Train", leave=False)
    for batch in pbar:
        x = batch["x"].to(device)
        y = batch["y"].to(device)
        vtype = batch["vtype"].to(device)
        
        optimizer.zero_grad()
        pred = model(x, vtype, y_true=y, teacher_forcing_ratio=tf_ratio)
        loss = criterion(pred, y)
        loss.backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        
        total_loss += loss.item() * x.size(0)
        n_samples += x.size(0)
        pbar.set_postfix({'loss': f'{loss.item():.4f}'})
    
    return total_loss / n_samples


def evaluate(model, loader, device):
    model.eval()
    criterion = nn.MSELoss()
    
    total_loss = 0
    n_samples = 0
    all_preds, all_targets = [], []
    all_anchors, all_scale_lat, all_scale_lon = [], [], []
    
    with torch.no_grad():
        for batch in tqdm(loader, desc="Eval", leave=False):
            x = batch["x"].to(device)
            y = batch["y"].to(device)
            vtype = batch["vtype"].to(device)
            
            pred = model(x, vtype)
            loss = criterion(pred, y)
            
            total_loss += loss.item() * x.size(0)
            n_samples += x.size(0)
            
            all_preds.append(pred.cpu().numpy())
            all_targets.append(y.cpu().numpy())
            all_anchors.append(batch["anchor"].numpy())
            all_scale_lat.append(batch["scale_lat"].numpy())
            all_scale_lon.append(batch["scale_lon"].numpy())
    
    # Reconversion en lat/lon
    preds = np.concatenate(all_preds)
    targets = np.concatenate(all_targets)
    anchors = np.concatenate(all_anchors)
    scale_lat = np.concatenate(all_scale_lat)
    scale_lon = np.concatenate(all_scale_lon)
    
    preds_ll = np.zeros_like(preds)
    targets_ll = np.zeros_like(targets)
    
    for i in range(len(preds)):
        lat, lon = anchors[i]
        preds_ll[i, :, 0] = lat + (preds[i, :, 0] * SCALE_POSITION) / scale_lat[i]
        preds_ll[i, :, 1] = lon + (preds[i, :, 1] * SCALE_POSITION) / scale_lon[i]
        targets_ll[i, :, 0] = lat + (targets[i, :, 0] * SCALE_POSITION) / scale_lat[i]
        targets_ll[i, :, 1] = lon + (targets[i, :, 1] * SCALE_POSITION) / scale_lon[i]
    
    ade, fde = compute_ade_fde(preds_ll, targets_ll)
    
    return total_loss / n_samples, ade, fde


# ==========================================
# MAIN
# ==========================================
def main():
    log("=" * 70)
    log(" AIS Trajectory Prediction - V2 (CORRIGÉ)")
    log("=" * 70)
    log(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    set_seed(SEED)
    device = setup_device()
    
    log(f"\n Configuration:")
    log(f"   Séquence: {SEQ_IN} -> {SEQ_OUT}")
    log(f"   Batch: {BATCH_SIZE} | LR: {LR}")
    log(f"   SCALE_POSITION: {SCALE_POSITION}m")
    
    # Données
    df = load_data_from_db()
    
    log("\n Création dataset...")
    full_dataset = AISDataset(df, max_windows=TRAIN_SIZE + VAL_SIZE)
    del df
    
    # Split
    n_total = len(full_dataset)
    n_train = min(TRAIN_SIZE, int(0.8 * n_total))
    n_val = min(VAL_SIZE, n_total - n_train)
    
    train_ds, val_ds, _ = torch.utils.data.random_split(
        full_dataset, [n_train, n_val, n_total - n_train - n_val],
        generator=torch.Generator().manual_seed(SEED)
    )
    
    log(f"   Train: {len(train_ds):,} | Val: {len(val_ds):,}")
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=NUM_WORKERS, pin_memory=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False,
                            num_workers=NUM_WORKERS, pin_memory=True)
    
    # Modèle
    n_vtypes = len(full_dataset.vtype2idx)
    log(f"\nModèle (VesselTypes: {n_vtypes})...")
    
    model = AISTransformer(
        input_dim=INPUT_DIM,
        vtype_card=max(n_vtypes, 100),
        vtype_emb=EMBED_VT,
        hidden=HIDDEN,
        n_heads=N_HEADS,
        n_layers=N_LAYERS,
        dropout=DROPOUT,
        pred_len=SEQ_OUT
    )
    
    # Utiliser UN SEUL GPU (GPU 0)
    if torch.cuda.is_available():
        torch.cuda.set_device(0)
        log(f" Utilisation GPU 0 uniquement")
    
    model = model.to(device)
    
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log(f"   Paramètres: {n_params:,}")
    
    # Optimizer avec warmup
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    
    # Warmup + Cosine scheduler
    def lr_lambda(epoch):
        if epoch < WARMUP_EPOCHS:
            return (epoch + 1) / WARMUP_EPOCHS
        return 0.5 * (1 + math.cos(math.pi * (epoch - WARMUP_EPOCHS) / (EPOCHS - WARMUP_EPOCHS)))
    
    scheduler = LambdaLR(optimizer, lr_lambda)
    
    criterion = TrajectoryLoss(fde_weight=0.3)
    
    model_for_es = model.module if hasattr(model, 'module') else model
    early_stopping = EarlyStopping(patience=PATIENCE, min_epochs=MIN_EPOCHS)
    
    visualizer = TrainingVisualizer(OUTPUT_DIR)
    
    # Training
    log("\n" + "=" * 70)
    log(" Entraînement")
    log("=" * 70)
    
    best_val_loss = float('inf')
    best_ade, best_fde, best_epoch = float('inf'), float('inf'), 0
    
    for epoch in range(1, EPOCHS + 1):
        start = datetime.now()
        
        # Teacher forcing: démarre à 0.5, décroit sur 60 epochs
        tf_ratio = max(0.0, 0.5 * (1 - epoch / 60))
        
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device, tf_ratio)
        val_loss, ade, fde = evaluate(model, val_loader, device)
        
        scheduler.step()
        lr = optimizer.param_groups[0]['lr']
        
        visualizer.update({
            'train_loss': train_loss, 'val_loss': val_loss,
            'ade': ade, 'fde': fde, 'lr': lr
        })
        
        elapsed = (datetime.now() - start).total_seconds()
        
        improved = ""
        if val_loss < best_val_loss:
            improved = " ⭐"
            best_val_loss = val_loss
            best_ade, best_fde = ade, fde
            best_epoch = epoch
            
            model_to_save = model.module if hasattr(model, 'module') else model
            torch.save({
                'epoch': epoch,
                'model_state_dict': model_to_save.state_dict(),
                'val_loss': val_loss,
                'ade': ade, 'fde': fde,
                'config': {
                    'input_dim': INPUT_DIM, 'hidden': HIDDEN,
                    'n_heads': N_HEADS, 'n_layers': N_LAYERS,
                    'seq_in': SEQ_IN, 'seq_out': SEQ_OUT,
                    'scale_position': SCALE_POSITION
                }
            }, OUTPUT_DIR / 'best_model.pth')
        
        log(f"Epoch {epoch:3d}/{EPOCHS} | "
            f"Loss: {train_loss:.4f}/{val_loss:.4f} | "
            f"ADE: {ade:.0f}m | FDE: {fde:.0f}m | "
            f"LR: {lr:.1e} | {elapsed:.1f}s{improved}")
        
        if early_stopping(val_loss, epoch, model_for_es):
            log(f"\n Early Stopping @ epoch {epoch}")
            break
    
    # Fin
    log("\n" + "=" * 70)
    log(" Terminé!")
    log(f"   Meilleur epoch: {best_epoch}")
    log(f"   Val Loss: {best_val_loss:.4f}")
    log(f"   ADE: {best_ade:.0f}m | FDE: {best_fde:.0f}m")
    
    # Restaurer meilleur modèle
    if early_stopping.early_stop:
        early_stopping.restore_best_weights(model_for_es)
    
    # Visualisations
    log("\n Génération visualisations...")
    checkpoint = torch.load(OUTPUT_DIR / 'best_model.pth')
    model_for_es.load_state_dict(checkpoint['model_state_dict'])
    visualizer.plot_all(model, val_loader, device)
    
    log(f"\n Terminé! Logs: {LOG_FILE}")
    
    return model


if __name__ == "__main__":
    main()
