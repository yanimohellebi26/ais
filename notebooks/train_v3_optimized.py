#!/usr/bin/env python3
"""
AIS Trajectory Prediction - Version Optimisée pour données pré-processées

Ce script utilise les trajectoires pré-segmentées de la table trajectory_segment
pour un entraînement optimal avec:
- Données propres et régulières
- Filtrage par qualité
- Features pré-calculées
- Normalisation cohérente
"""

import os
import sys
import math
import random
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import psycopg2
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
from torch.optim.lr_scheduler import OneCycleLR
from tqdm import tqdm

# ============================================================
# CONFIGURATION
# ============================================================

# Device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Database
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '172.31.60.8'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'ais'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'music861!')
}

# Hyperparamètres
CONFIG = {
    # Séquences
    'seq_in': 20,
    'seq_out': 10,
    
    # Architecture
    'hidden_dim': 256,
    'n_heads': 8,
    'n_layers': 4,
    'dropout': 0.1,
    'embed_vtype': 32,
    
    # Features d'entrée
    'input_dim': 10,  # lat, lon, sog, sin_cog, cos_cog, sin_head, cos_head, delta_t, accel, turn
    
    # Normalisation (IMPORTANT)
    'scale_position': 10000,  # metres
    'scale_sog': 30,          # knots
    'scale_dt': 300,          # secondes
    
    # Training
    'batch_size': 128,
    'epochs': 150,
    'lr': 1e-3,
    'weight_decay': 1e-5,
    'patience': 15,
    
    # Data
    'min_quality': 0.5,
    'train_ratio': 0.8,
    'num_workers': 4,
    
    # Output
    'output_dir': Path('output'),
    'model_name': 'trajectory_model_v3.pth',
}

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Reproductibilité
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)


# ============================================================
# DATASET
# ============================================================

class TrajectoryDataset(Dataset):
    """Dataset utilisant les trajectoires pré-processées."""
    
    def __init__(self, config: dict = None):
        self.config = config or CONFIG
        self.samples = []
        self.vtype2idx = {}
        self.idx2vtype = {}
        
        self._load_data()
    
    def _load_data(self):
        """Charge les données depuis la base."""
        logger.info("Chargement des données depuis trajectory_segment...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Récupérer les segments valides
        segments_query = """
            SELECT ts.id, ts.vessel_type_id, ts.num_points, ts.quality_score
            FROM trajectory_segment ts
            WHERE ts.is_valid_for_training = TRUE
              AND ts.quality_score >= %s
              AND ts.num_points >= %s
            ORDER BY ts.quality_score DESC
        """
        
        min_points = self.config['seq_in'] + self.config['seq_out']
        segments_df = pd.read_sql(
            segments_query, conn, 
            params=(self.config['min_quality'], min_points)
        )
        
        logger.info(f"✅ {len(segments_df)} segments valides trouvés")
        
        if segments_df.empty:
            raise ValueError("Aucun segment valide trouvé! Exécutez d'abord prepare_trajectories.py")
        
        # Mapper les types de navires
        vtypes = segments_df['vessel_type_id'].dropna().unique()
        self.vtype2idx = {int(v): i for i, v in enumerate(sorted(vtypes))}
        self.vtype2idx[0] = len(self.vtype2idx)  # Type inconnu
        self.idx2vtype = {i: v for v, i in self.vtype2idx.items()}
        
        # Charger les points pour chaque segment
        logger.info("Chargement des points de trajectoire...")
        
        for _, seg in tqdm(segments_df.iterrows(), total=len(segments_df), desc="Segments"):
            segment_id = seg['id']
            vtype = int(seg['vessel_type_id']) if pd.notna(seg['vessel_type_id']) else 0
            
            # Récupérer les points
            points_query = """
                SELECT lat, lon, sog, cog, heading, delta_t, acceleration, turn_rate
                FROM trajectory_point
                WHERE segment_id = %s
                ORDER BY point_index
            """
            points_df = pd.read_sql(points_query, conn, params=(segment_id,))
            
            if len(points_df) < min_points:
                continue
            
            # Créer des fenêtres glissantes
            self._create_windows(points_df.values, vtype)
        
        conn.close()
        logger.info(f"✅ {len(self.samples)} échantillons d'entraînement créés")
    
    def _create_windows(self, points: np.ndarray, vtype: int):
        """Crée des fenêtres d'entraînement à partir d'un segment."""
        seq_in = self.config['seq_in']
        seq_out = self.config['seq_out']
        total_len = seq_in + seq_out
        
        # Colonnes: lat, lon, sog, cog, heading, delta_t, acceleration, turn_rate
        num_windows = len(points) - total_len + 1
        
        for start in range(0, num_windows, 5):  # Stride de 5 pour éviter trop de redondance
            window = points[start:start + total_len]
            
            # Point d'ancrage (dernier de l'entrée)
            anchor_lat = window[seq_in - 1, 0]
            anchor_lon = window[seq_in - 1, 1]
            
            # Facteurs de conversion
            METER_PER_DEG_LAT = 111320.0
            meter_per_deg_lon = 40075000.0 * math.cos(math.radians(anchor_lat)) / 360.0
            
            # Entrée: positions relatives + features
            inp = window[:seq_in]
            x = np.stack([
                (inp[:, 0] - anchor_lat) * METER_PER_DEG_LAT / self.config['scale_position'],
                (inp[:, 1] - anchor_lon) * meter_per_deg_lon / self.config['scale_position'],
                inp[:, 2] / self.config['scale_sog'],  # SOG
                np.sin(np.radians(inp[:, 3])),  # sin(COG)
                np.cos(np.radians(inp[:, 3])),  # cos(COG)
                np.sin(np.radians(inp[:, 4])),  # sin(Heading)
                np.cos(np.radians(inp[:, 4])),  # cos(Heading)
                np.clip(inp[:, 5] / self.config['scale_dt'], 0, 2),  # delta_t
                inp[:, 6],  # acceleration (déjà normalisée)
                inp[:, 7] / 3.0,  # turn_rate
            ], axis=1).astype(np.float32)
            
            # Sortie: positions relatives
            out = window[seq_in:]
            y = np.stack([
                (out[:, 0] - anchor_lat) * METER_PER_DEG_LAT / self.config['scale_position'],
                (out[:, 1] - anchor_lon) * meter_per_deg_lon / self.config['scale_position'],
            ], axis=1).astype(np.float32)
            
            self.samples.append({
                'x': x,
                'y': y,
                'vtype': self.vtype2idx.get(vtype, self.vtype2idx[0]),
                'anchor': np.array([anchor_lat, anchor_lon], dtype=np.float32),
                'scales': np.array([METER_PER_DEG_LAT, meter_per_deg_lon], dtype=np.float32),
            })
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        s = self.samples[idx]
        return {
            'x': torch.from_numpy(s['x']),
            'y': torch.from_numpy(s['y']),
            'vtype': torch.tensor(s['vtype'], dtype=torch.long),
            'anchor': torch.from_numpy(s['anchor']),
            'scales': torch.from_numpy(s['scales']),
        }


# ============================================================
# MODÈLE
# ============================================================

class PositionalEncoding(nn.Module):
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
        # x: (B, T, D)
        x = x + self.pe[:x.size(1)].transpose(0, 1)
        return self.dropout(x)


class TrajectoryTransformer(nn.Module):
    """Transformer encoder + LSTM decoder pour prédiction de trajectoire."""
    
    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or CONFIG
        
        input_dim = self.config['input_dim']
        hidden = self.config['hidden_dim']
        embed_vt = self.config['embed_vtype']
        n_heads = self.config['n_heads']
        n_layers = self.config['n_layers']
        dropout = self.config['dropout']
        
        # Embedding type de navire
        self.vtype_embed = nn.Embedding(100, embed_vt)  # 100 types max
        
        # Projection entrée
        self.input_proj = nn.Linear(input_dim + embed_vt, hidden)
        
        # Encodeur Transformer
        self.pos_encoder = PositionalEncoding(hidden, dropout)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden,
            nhead=n_heads,
            dim_feedforward=hidden * 4,
            dropout=dropout,
            batch_first=True,
            activation='gelu'
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        
        # Décodeur LSTM
        self.decoder = nn.LSTMCell(2 + embed_vt, hidden)
        
        # Tête de sortie
        self.output_head = nn.Sequential(
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden // 2, 2)
        )
        
        self._init_weights()
    
    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def forward(self, x: torch.Tensor, vtype: torch.Tensor, 
                out_len: int = None, y_true: torch.Tensor = None,
                teacher_forcing_ratio: float = 0.0) -> torch.Tensor:
        """
        Args:
            x: (B, T_in, input_dim) - séquence d'entrée
            vtype: (B,) - type de navire
            out_len: longueur de sortie (défaut: seq_out)
            y_true: (B, T_out, 2) - cibles pour teacher forcing
            teacher_forcing_ratio: probabilité d'utiliser y_true
        
        Returns:
            (B, T_out, 2) - positions prédites
        """
        if out_len is None:
            out_len = self.config['seq_out']
        
        B, T, _ = x.shape
        
        # Embedding type
        v_emb = self.vtype_embed(vtype)  # (B, embed_vt)
        v_emb_expanded = v_emb.unsqueeze(1).expand(-1, T, -1)
        
        # Concaténer entrée + embedding
        x_cat = torch.cat([x, v_emb_expanded], dim=-1)
        
        # Encoder
        h_enc = self.input_proj(x_cat)
        h_enc = self.pos_encoder(h_enc)
        memory = self.encoder(h_enc)
        
        # Initialiser décodeur avec le dernier état
        h = memory[:, -1].contiguous()
        c = torch.zeros_like(h)
        
        # Décodage auto-régressif
        prev_pos = torch.zeros(B, 2, device=x.device)
        outputs = []
        
        for t in range(out_len):
            # Teacher forcing
            if y_true is not None and random.random() < teacher_forcing_ratio:
                dec_input = y_true[:, t]
            else:
                dec_input = prev_pos
            
            # LSTM step
            lstm_input = torch.cat([dec_input, v_emb], dim=-1)
            h, c = self.decoder(lstm_input, (h, c))
            
            # Prédiction
            delta = self.output_head(h)
            outputs.append(delta.unsqueeze(1))
            
            # Mise à jour position précédente (cumulative)
            prev_pos = prev_pos + delta
        
        return torch.cat(outputs, dim=1)


# ============================================================
# LOSS FUNCTION
# ============================================================

class TrajectoryLoss(nn.Module):
    """Loss combinée: MSE + poids sur la FDE."""
    
    def __init__(self, fde_weight: float = 2.0):
        super().__init__()
        self.fde_weight = fde_weight
    
    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        # MSE sur tous les points
        mse = torch.mean((pred - target) ** 2)
        
        # MSE pondéré sur le dernier point (FDE)
        fde_mse = torch.mean((pred[:, -1] - target[:, -1]) ** 2)
        
        return mse + self.fde_weight * fde_mse


# ============================================================
# MÉTRIQUES
# ============================================================

def haversine_distance_np(lat1, lon1, lat2, lon2):
    """Distance haversine en mètres."""
    R = 6371000.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1-a))


def compute_metrics(pred: np.ndarray, target: np.ndarray, 
                    anchors: np.ndarray, scale_position: float) -> Dict[str, float]:
    """
    Calcule ADE et FDE en mètres.
    
    Args:
        pred, target: (N, T, 2) - positions normalisées
        anchors: (N, 2) - points d'ancrage [lat, lon]
        scale_position: facteur de normalisation
    """
    N, T, _ = pred.shape
    
    ade_sum = 0.0
    fde_sum = 0.0
    
    for i in range(N):
        anchor_lat, anchor_lon = anchors[i]
        meter_per_deg_lon = 40075000.0 * math.cos(math.radians(anchor_lat)) / 360.0
        
        # Convertir en lat/lon
        pred_lat = anchor_lat + (pred[i, :, 0] * scale_position) / 111320.0
        pred_lon = anchor_lon + (pred[i, :, 1] * scale_position) / meter_per_deg_lon
        
        true_lat = anchor_lat + (target[i, :, 0] * scale_position) / 111320.0
        true_lon = anchor_lon + (target[i, :, 1] * scale_position) / meter_per_deg_lon
        
        # Distances pour chaque point
        distances = haversine_distance_np(pred_lat, pred_lon, true_lat, true_lon)
        
        ade_sum += np.mean(distances)
        fde_sum += distances[-1]
    
    return {
        'ade': ade_sum / N,
        'fde': fde_sum / N
    }


# ============================================================
# ENTRAÎNEMENT
# ============================================================

def train_epoch(model, loader, optimizer, loss_fn, epoch, max_epochs):
    """Une époque d'entraînement."""
    model.train()
    total_loss = 0.0
    
    # Teacher forcing décroissant
    tf_ratio = max(0.0, 1.0 - epoch / (max_epochs * 0.5))
    
    pbar = tqdm(loader, desc=f"Train {epoch}", leave=False)
    for batch in pbar:
        x = batch['x'].to(DEVICE)
        y = batch['y'].to(DEVICE)
        vtype = batch['vtype'].to(DEVICE)
        
        optimizer.zero_grad()
        pred = model(x, vtype, y_true=y, teacher_forcing_ratio=tf_ratio)
        loss = loss_fn(pred, y)
        
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        total_loss += loss.item() * x.size(0)
        pbar.set_postfix({'loss': f'{loss.item():.4f}'})
    
    return total_loss / len(loader.dataset)


@torch.no_grad()
def evaluate(model, loader, loss_fn, config):
    """Évaluation sur un loader."""
    model.eval()
    total_loss = 0.0
    
    all_preds, all_targets, all_anchors = [], [], []
    
    for batch in loader:
        x = batch['x'].to(DEVICE)
        y = batch['y'].to(DEVICE)
        vtype = batch['vtype'].to(DEVICE)
        
        pred = model(x, vtype)
        loss = loss_fn(pred, y)
        total_loss += loss.item() * x.size(0)
        
        all_preds.append(pred.cpu().numpy())
        all_targets.append(y.cpu().numpy())
        all_anchors.append(batch['anchor'].numpy())
    
    preds = np.concatenate(all_preds, axis=0)
    targets = np.concatenate(all_targets, axis=0)
    anchors = np.concatenate(all_anchors, axis=0)
    
    metrics = compute_metrics(preds, targets, anchors, config['scale_position'])
    metrics['loss'] = total_loss / len(loader.dataset)
    
    return metrics


def train(config: dict = None):
    """Pipeline d'entraînement complet."""
    config = config or CONFIG
    config['output_dir'].mkdir(exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("🚀 ENTRAÎNEMENT MODÈLE TRAJECTOIRE V3")
    logger.info("=" * 60)
    logger.info(f"Device: {DEVICE}")
    
    # Dataset
    logger.info("\n📊 Chargement des données...")
    dataset = TrajectoryDataset(config)
    
    # Split train/val
    n = len(dataset)
    train_size = int(n * config['train_ratio'])
    val_size = n - train_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])
    
    logger.info(f"Train: {train_size}, Val: {val_size}")
    
    train_loader = DataLoader(
        train_ds, 
        batch_size=config['batch_size'], 
        shuffle=True,
        num_workers=config['num_workers'],
        pin_memory=True
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=config['batch_size'],
        shuffle=False,
        num_workers=config['num_workers'],
        pin_memory=True
    )
    
    # Modèle
    logger.info("\n🏗️ Création du modèle...")
    model = TrajectoryTransformer(config).to(DEVICE)
    num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Paramètres: {num_params:,}")
    
    # Optimizer et scheduler
    optimizer = torch.optim.AdamW(
        model.parameters(), 
        lr=config['lr'],
        weight_decay=config['weight_decay']
    )
    
    scheduler = OneCycleLR(
        optimizer,
        max_lr=config['lr'],
        epochs=config['epochs'],
        steps_per_epoch=len(train_loader),
        pct_start=0.1,
        anneal_strategy='cos'
    )
    
    loss_fn = TrajectoryLoss(fde_weight=2.0)
    
    # Training loop
    logger.info("\n🎯 Début de l'entraînement...")
    best_fde = float('inf')
    patience_counter = 0
    history = []
    
    for epoch in range(1, config['epochs'] + 1):
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, loss_fn, epoch, config['epochs'])
        scheduler.step()
        
        # Eval
        val_metrics = evaluate(model, val_loader, loss_fn, config)
        
        history.append({
            'epoch': epoch,
            'train_loss': train_loss,
            'val_loss': val_metrics['loss'],
            'ade': val_metrics['ade'],
            'fde': val_metrics['fde'],
            'lr': optimizer.param_groups[0]['lr']
        })
        
        # Log
        logger.info(
            f"Ep {epoch:03d} | "
            f"Loss: {train_loss:.4f}/{val_metrics['loss']:.4f} | "
            f"ADE: {val_metrics['ade']:.0f}m | "
            f"FDE: {val_metrics['fde']:.0f}m | "
            f"LR: {optimizer.param_groups[0]['lr']:.2e}"
        )
        
        # Best model
        if val_metrics['fde'] < best_fde:
            best_fde = val_metrics['fde']
            patience_counter = 0
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'config': config,
                'metrics': val_metrics,
                'vtype2idx': dataset.vtype2idx,
            }, config['output_dir'] / config['model_name'])
            logger.info(f"  ✅ Meilleur modèle sauvegardé (FDE: {best_fde:.0f}m)")
        else:
            patience_counter += 1
            if patience_counter >= config['patience']:
                logger.info(f"\n⏹️ Early stopping à l'époque {epoch}")
                break
    
    # Résultats finaux
    logger.info("\n" + "=" * 60)
    logger.info("📊 RÉSULTATS FINAUX")
    logger.info("=" * 60)
    logger.info(f"Meilleur FDE: {best_fde:.0f}m")
    logger.info(f"Modèle sauvegardé: {config['output_dir'] / config['model_name']}")
    
    return model, history


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Entraînement modèle trajectoire AIS")
    parser.add_argument('--epochs', type=int, default=150, help="Nombre d'époques")
    parser.add_argument('--batch-size', type=int, default=128, help="Taille de batch")
    parser.add_argument('--lr', type=float, default=1e-3, help="Learning rate")
    parser.add_argument('--patience', type=int, default=15, help="Patience early stopping")
    args = parser.parse_args()
    
    CONFIG['epochs'] = args.epochs
    CONFIG['batch_size'] = args.batch_size
    CONFIG['lr'] = args.lr
    CONFIG['patience'] = args.patience
    
    train(CONFIG)
