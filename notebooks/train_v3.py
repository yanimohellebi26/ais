#!/usr/bin/env python3
"""
AIS Trajectory Prediction - V3 (Données pré-processées)

Utilise les tables trajectory_segment / trajectory_point
pour un entraînement optimal avec données propres.

Usage sur serveur eco:
    python train_v3.py --epochs 150 --batch-size 256
"""

import os
import sys
import math
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import psycopg2
from tqdm import tqdm

import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from torch.optim.lr_scheduler import LambdaLR

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42

# Hyperparamètres
SEQ_IN = 20
SEQ_OUT = 10
BATCH_SIZE = 256
LR = 3e-4
EPOCHS = 150
MIN_EPOCHS = 20
PATIENCE = 15
WARMUP_EPOCHS = 5
NUM_WORKERS = 4

# Architecture
HIDDEN = 256
N_HEADS = 8
N_LAYERS = 4
DROPOUT = 0.15
EMBED_VT = 32
INPUT_DIM = 10

# Normalisation
SCALE_POSITION = 10000.0  # mètres
SCALE_SOG = 15.0          # noeuds
SCALE_DT = 300.0          # secondes

# Database
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '172.31.60.8'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'ais'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'ANjw/84H77C9h2')
}

OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Logging
LOG_FILE = OUTPUT_DIR / f"train_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def log(msg, level="info"):
    getattr(logger, level)(msg)

def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ============================================================
# DATASET (depuis tables pré-processées)
# ============================================================

class PreparedTrajectoryDataset(Dataset):
    """Dataset utilisant trajectory_segment/trajectory_point."""
    
    def __init__(self, min_quality: float = 0.3, max_samples: int = None):
        self.seq_in = SEQ_IN
        self.seq_out = SEQ_OUT
        self.samples = []
        self.vtype2idx = {}
        
        self._load_from_db(min_quality, max_samples)
    
    def _load_from_db(self, min_quality: float, max_samples: int):
        log("📊 Chargement depuis trajectory_segment...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Récupérer segments valides
        query = """
            SELECT id, vessel_type_id, num_points, quality_score
            FROM trajectory_segment
            WHERE is_valid = TRUE
              AND quality_score >= %s
              AND num_points >= %s
            ORDER BY quality_score DESC
        """
        min_pts = self.seq_in + self.seq_out
        segments = pd.read_sql(query, conn, params=(min_quality, min_pts))
        
        log(f"   {len(segments)} segments valides")
        
        if segments.empty:
            raise ValueError("Aucun segment! Exécutez prepare_trajectories.py")
        
        # Mapper types navires
        vtypes = segments['vessel_type_id'].dropna().unique()
        self.vtype2idx = {int(v): i for i, v in enumerate(sorted(vtypes))}
        self.vtype2idx[0] = len(self.vtype2idx)
        
        # Charger points par segment
        total_windows = 0
        for _, seg in tqdm(segments.iterrows(), total=len(segments), desc="Segments"):
            if max_samples and total_windows >= max_samples:
                break
            
            pts = pd.read_sql("""
                SELECT lat, lon, sog, cog, heading, delta_t, accel, turn_rate
                FROM trajectory_point
                WHERE segment_id = %s
                ORDER BY point_idx
            """, conn, params=(seg['id'],))
            
            if len(pts) < min_pts:
                continue
            
            vtype = int(seg['vessel_type_id']) if pd.notna(seg['vessel_type_id']) else 0
            n_windows = self._create_windows(pts.values, vtype)
            total_windows += n_windows
        
        conn.close()
        log(f"✅ {len(self.samples):,} échantillons créés")
    
    def _create_windows(self, points: np.ndarray, vtype: int) -> int:
        """Crée fenêtres d'entraînement depuis un segment."""
        total_len = self.seq_in + self.seq_out
        n_windows = len(points) - total_len + 1
        created = 0
        
        # Stride de 5 pour éviter trop de redondance
        for start in range(0, n_windows, 5):
            window = points[start:start + total_len]
            
            # Point d'ancrage
            anchor_lat = window[self.seq_in - 1, 0]
            anchor_lon = window[self.seq_in - 1, 1]
            
            # Conversion
            METER_PER_DEG_LAT = 111320.0
            meter_per_deg_lon = 40075000.0 * math.cos(math.radians(anchor_lat)) / 360.0
            
            # Entrée
            inp = window[:self.seq_in]
            x = np.stack([
                (inp[:, 0] - anchor_lat) * METER_PER_DEG_LAT / SCALE_POSITION,
                (inp[:, 1] - anchor_lon) * meter_per_deg_lon / SCALE_POSITION,
                inp[:, 2] / SCALE_SOG,
                np.sin(np.radians(inp[:, 3])),
                np.cos(np.radians(inp[:, 3])),
                np.sin(np.radians(inp[:, 4])),
                np.cos(np.radians(inp[:, 4])),
                np.clip(inp[:, 5] / SCALE_DT, 0, 2),
                inp[:, 6],  # accel
                inp[:, 7] / 3.0,  # turn_rate
            ], axis=1).astype(np.float32)
            
            # Sortie
            out = window[self.seq_in:]
            y = np.stack([
                (out[:, 0] - anchor_lat) * METER_PER_DEG_LAT / SCALE_POSITION,
                (out[:, 1] - anchor_lon) * meter_per_deg_lon / SCALE_POSITION,
            ], axis=1).astype(np.float32)
            
            self.samples.append({
                'x': x, 'y': y,
                'vtype': self.vtype2idx.get(vtype, 0),
                'anchor': np.array([anchor_lat, anchor_lon], dtype=np.float32),
                'scale_lat': METER_PER_DEG_LAT,
                'scale_lon': meter_per_deg_lon,
            })
            created += 1
        
        return created
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        s = self.samples[idx]
        return {
            'x': torch.from_numpy(s['x']),
            'y': torch.from_numpy(s['y']),
            'vtype': torch.tensor(s['vtype'], dtype=torch.long),
            'anchor': torch.from_numpy(s['anchor']),
            'scale_lat': torch.tensor(s['scale_lat'], dtype=torch.float32),
            'scale_lon': torch.tensor(s['scale_lon'], dtype=torch.float32),
        }


# ============================================================
# MODÈLE
# ============================================================

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=100):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))
    
    def forward(self, x):
        return self.dropout(x + self.pe[:, :x.size(1)])


class AISTransformerV3(nn.Module):
    def __init__(self, input_dim=INPUT_DIM, vtype_card=100, vtype_emb=EMBED_VT,
                 hidden=HIDDEN, n_heads=N_HEADS, n_layers=N_LAYERS, 
                 dropout=DROPOUT, pred_len=SEQ_OUT):
        super().__init__()
        
        self.hidden = hidden
        self.pred_len = pred_len
        
        self.vessel_emb = nn.Embedding(vtype_card, vtype_emb)
        self.input_proj = nn.Linear(input_dim + vtype_emb, hidden)
        self.input_norm = nn.LayerNorm(hidden)
        self.pos_enc = PositionalEncoding(hidden, dropout)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden, nhead=n_heads,
            dim_feedforward=hidden * 4,
            dropout=dropout, batch_first=True, activation='gelu'
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.encoder_norm = nn.LayerNorm(hidden)
        
        # Décodeur LSTM
        self.decoder = nn.LSTM(
            input_size=2 + 2 + vtype_emb,
            hidden_size=hidden,
            num_layers=2,
            dropout=dropout,
            batch_first=True
        )
        
        self.velocity_proj = nn.Linear(hidden, 2)
        self.output_proj = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, 2)
        )
        
        self._init_weights()
    
    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def forward(self, x, vtype, out_len=None, y_true=None, tf_ratio=0.0):
        if out_len is None:
            out_len = self.pred_len
        
        B, T, _ = x.shape
        device = x.device
        
        v_emb = self.vessel_emb(vtype)
        v_emb_exp = v_emb.unsqueeze(1).expand(-1, T, -1)
        
        x_cat = torch.cat([x, v_emb_exp], dim=2)
        x_proj = self.input_norm(self.input_proj(x_cat))
        x_enc = self.pos_enc(x_proj)
        memory = self.encoder_norm(self.encoder(x_enc))
        
        context = memory[:, -1]
        velocity = self.velocity_proj(context)
        pos = torch.zeros(B, 2, device=device)
        
        h0 = context.unsqueeze(0).repeat(2, 1, 1)
        c0 = torch.zeros_like(h0)
        
        preds = []
        for t in range(out_len):
            if self.training and y_true is not None and random.random() < tf_ratio:
                pos = y_true[:, t]
            
            lstm_in = torch.cat([pos, velocity, v_emb], dim=1).unsqueeze(1)
            out, (h0, c0) = self.decoder(lstm_in, (h0, c0))
            
            delta = self.output_proj(out.squeeze(1))
            pos = pos + delta
            preds.append(pos.unsqueeze(1))
            velocity = delta
        
        return torch.cat(preds, dim=1)


# ============================================================
# LOSS & METRICS
# ============================================================

class TrajectoryLoss(nn.Module):
    def __init__(self, fde_weight=0.3):
        super().__init__()
        self.mse = nn.MSELoss()
        self.fde_weight = fde_weight
    
    def forward(self, pred, target):
        mse = self.mse(pred, target)
        fde = self.mse(pred[:, -1], target[:, -1])
        return mse + self.fde_weight * fde


def haversine_np(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dl/2)**2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1-a))


def compute_metrics(pred, target, anchors, scale_lat, scale_lon):
    """ADE/FDE en mètres."""
    N, T, _ = pred.shape
    ade_sum, fde_sum = 0.0, 0.0
    
    for i in range(N):
        lat, lon = anchors[i]
        
        pred_lat = lat + (pred[i, :, 0] * SCALE_POSITION) / scale_lat[i]
        pred_lon = lon + (pred[i, :, 1] * SCALE_POSITION) / scale_lon[i]
        true_lat = lat + (target[i, :, 0] * SCALE_POSITION) / scale_lat[i]
        true_lon = lon + (target[i, :, 1] * SCALE_POSITION) / scale_lon[i]
        
        dists = haversine_np(pred_lat, pred_lon, true_lat, true_lon)
        ade_sum += np.mean(dists)
        fde_sum += dists[-1]
    
    return ade_sum / N, fde_sum / N


# ============================================================
# EARLY STOPPING
# ============================================================

class EarlyStopping:
    def __init__(self, patience=PATIENCE, min_epochs=MIN_EPOCHS):
        self.patience = patience
        self.min_epochs = min_epochs
        self.counter = 0
        self.best_score = None
        self.best_epoch = 0
        self.best_state = None
    
    def __call__(self, score, epoch, model):
        if epoch < self.min_epochs:
            if self.best_score is None or score < self.best_score:
                self._update(score, epoch, model)
            return False
        
        if self.best_score is None or score < self.best_score - 1e-5:
            self._update(score, epoch, model)
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                return True
        return False
    
    def _update(self, score, epoch, model):
        self.best_score = score
        self.best_epoch = epoch
        self.best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    
    def restore(self, model):
        if self.best_state:
            model.load_state_dict(self.best_state)


# ============================================================
# TRAINING
# ============================================================

def train_epoch(model, loader, optimizer, criterion, device, tf_ratio=0.0):
    model.train()
    total_loss, n = 0, 0
    
    for batch in tqdm(loader, desc="Train", leave=False):
        x = batch['x'].to(device)
        y = batch['y'].to(device)
        vtype = batch['vtype'].to(device)
        
        optimizer.zero_grad()
        pred = model(x, vtype, y_true=y, tf_ratio=tf_ratio)
        loss = criterion(pred, y)
        loss.backward()
        
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        
        total_loss += loss.item() * x.size(0)
        n += x.size(0)
    
    return total_loss / n


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    total_loss, n = 0, 0
    all_pred, all_target, all_anchor = [], [], []
    all_scale_lat, all_scale_lon = [], []
    
    criterion = nn.MSELoss()
    
    for batch in tqdm(loader, desc="Eval", leave=False):
        x = batch['x'].to(device)
        y = batch['y'].to(device)
        vtype = batch['vtype'].to(device)
        
        pred = model(x, vtype)
        loss = criterion(pred, y)
        
        total_loss += loss.item() * x.size(0)
        n += x.size(0)
        
        all_pred.append(pred.cpu().numpy())
        all_target.append(y.cpu().numpy())
        all_anchor.append(batch['anchor'].numpy())
        all_scale_lat.append(batch['scale_lat'].numpy())
        all_scale_lon.append(batch['scale_lon'].numpy())
    
    pred = np.concatenate(all_pred)
    target = np.concatenate(all_target)
    anchors = np.concatenate(all_anchor)
    scale_lat = np.concatenate(all_scale_lat)
    scale_lon = np.concatenate(all_scale_lon)
    
    ade, fde = compute_metrics(pred, target, anchors, scale_lat, scale_lon)
    
    return total_loss / n, ade, fde


def save_plots(history, output_dir):
    epochs = range(1, len(history['train_loss']) + 1)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    axes[0,0].plot(epochs, history['train_loss'], 'b-', label='Train')
    axes[0,0].plot(epochs, history['val_loss'], 'r-', label='Val')
    axes[0,0].set_title('Loss')
    axes[0,0].legend()
    axes[0,0].grid(True)
    
    axes[0,1].plot(epochs, history['ade'], 'g-')
    axes[0,1].axhline(min(history['ade']), color='g', ls='--', alpha=0.5)
    axes[0,1].set_title(f"ADE (best: {min(history['ade']):.0f}m)")
    axes[0,1].grid(True)
    
    axes[1,0].plot(epochs, history['fde'], 'm-')
    axes[1,0].axhline(min(history['fde']), color='m', ls='--', alpha=0.5)
    axes[1,0].set_title(f"FDE (best: {min(history['fde']):.0f}m)")
    axes[1,0].grid(True)
    
    axes[1,1].plot(epochs, history['lr'], 'orange')
    axes[1,1].set_title('Learning Rate')
    axes[1,1].set_yscale('log')
    axes[1,1].grid(True)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'training_v3.png', dpi=150)
    plt.close()


# ============================================================
# MAIN
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=EPOCHS)
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE)
    parser.add_argument('--lr', type=float, default=LR)
    parser.add_argument('--max-samples', type=int, default=None)
    parser.add_argument('--min-quality', type=float, default=0.3)
    args = parser.parse_args()
    
    log("=" * 60)
    log("🚀 AIS Trajectory V3 - Données pré-processées")
    log("=" * 60)
    
    set_seed()
    
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    if torch.cuda.is_available():
        log(f"🖥️ GPU: {torch.cuda.get_device_name(0)}")
    
    # Dataset
    dataset = PreparedTrajectoryDataset(
        min_quality=args.min_quality,
        max_samples=args.max_samples
    )
    
    # Split
    n = len(dataset)
    n_train = int(0.8 * n)
    n_val = n - n_train
    
    train_ds, val_ds = torch.utils.data.random_split(
        dataset, [n_train, n_val],
        generator=torch.Generator().manual_seed(SEED)
    )
    
    log(f"📊 Train: {n_train:,} | Val: {n_val:,}")
    
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              num_workers=NUM_WORKERS, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            num_workers=NUM_WORKERS, pin_memory=True)
    
    # Modèle
    model = AISTransformerV3(
        vtype_card=max(len(dataset.vtype2idx), 100)
    ).to(device)
    
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log(f"🏗️ Paramètres: {n_params:,}")
    
    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    
    def lr_lambda(epoch):
        if epoch < WARMUP_EPOCHS:
            return (epoch + 1) / WARMUP_EPOCHS
        return 0.5 * (1 + math.cos(math.pi * (epoch - WARMUP_EPOCHS) / (args.epochs - WARMUP_EPOCHS)))
    
    scheduler = LambdaLR(optimizer, lr_lambda)
    criterion = TrajectoryLoss(fde_weight=0.3)
    early_stop = EarlyStopping()
    
    history = {'train_loss': [], 'val_loss': [], 'ade': [], 'fde': [], 'lr': []}
    best_fde = float('inf')
    
    log("\n🎯 Entraînement...")
    for epoch in range(1, args.epochs + 1):
        tf_ratio = max(0.0, 0.5 * (1 - epoch / 60))
        
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device, tf_ratio)
        val_loss, ade, fde = evaluate(model, val_loader, device)
        
        scheduler.step()
        lr = optimizer.param_groups[0]['lr']
        
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['ade'].append(ade)
        history['fde'].append(fde)
        history['lr'].append(lr)
        
        improved = ""
        if fde < best_fde:
            best_fde = fde
            improved = " ⭐"
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'config': {'hidden': HIDDEN, 'n_heads': N_HEADS, 'n_layers': N_LAYERS,
                          'seq_in': SEQ_IN, 'seq_out': SEQ_OUT, 'scale_position': SCALE_POSITION},
                'ade': ade, 'fde': fde,
                'vtype2idx': dataset.vtype2idx,
            }, OUTPUT_DIR / 'best_model_v3.pth')
        
        log(f"Ep {epoch:3d} | Loss: {train_loss:.4f}/{val_loss:.4f} | "
            f"ADE: {ade:.0f}m | FDE: {fde:.0f}m | LR: {lr:.1e}{improved}")
        
        if early_stop(val_loss, epoch, model):
            log(f"⏹️ Early stopping @ epoch {epoch}")
            break
    
    # Fin
    log("\n" + "=" * 60)
    log("✅ TERMINÉ")
    log(f"   Best FDE: {best_fde:.0f}m")
    log(f"   Modèle: {OUTPUT_DIR / 'best_model_v3.pth'}")
    
    save_plots(history, OUTPUT_DIR)
    log(f"   Graphiques: {OUTPUT_DIR / 'training_v3.png'}")


if __name__ == "__main__":
    main()
