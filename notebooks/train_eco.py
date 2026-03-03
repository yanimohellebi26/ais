#!/usr/bin/env python3
"""
=============================================================================
AIS LSTM-Transformer - Script d'entrainement optimise pour serveur ECO
=============================================================================
Serveur : ym519512@eco
CPU     : 2x AMD EPYC 9254 -> 96 coeurs
RAM     : 1 TB
GPU     : 2x NVIDIA L40S (46 GB chacun)
CUDA    : 13.1 | Driver: 590.48.01
Source  : CSV local (ais_data.csv)
=============================================================================
OPTIMISATIONS vs version precedente :
  - Lecture CSV locale (plus de tunnel SSH PostgreSQL)
  - correct_speed / correct_position vectorises avec numpy (plus de boucles Python)
  - calculate_metrics vectorise par batch (plus de boucle sample par sample)
  - Batch size 16384 pour saturer les 2x L40S
=============================================================================
"""

import os
import sys
import gc
import pickle
import time
import argparse
import resource
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tqdm.auto import tqdm
from pyproj import Proj

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.amp import autocast

# -----------------------------------------------------------------------------
# ARGUMENTS CLI
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="AIS LSTM-Transformer Training on ECO")
parser.add_argument("--csv-file",    default="ais_data.csv", help="Fichier CSV d'entree")
parser.add_argument("--epochs",      default=150,           type=int)
parser.add_argument("--batch-size",  default=16384,         type=int)
parser.add_argument("--lr",          default=1e-3,          type=float)
parser.add_argument("--patience",    default=20,            type=int)
parser.add_argument("--seq-in",      default=20,            type=int)
parser.add_argument("--seq-out",     default=10,            type=int)
parser.add_argument("--hidden-dim",  default=512,           type=int)
parser.add_argument("--num-layers",  default=4,             type=int)
parser.add_argument("--num-heads",   default=8,             type=int)
parser.add_argument("--dropout",     default=0.2,           type=float)
parser.add_argument("--num-workers", default=4,             type=int)
parser.add_argument("--multi-gpu",   action="store_true",   default=True)
parser.add_argument("--limit-rows",  default=None,          type=int, help="Limiter nb lignes (debug)")
parser.add_argument("--output-dir",  default="./eco_output")
args = parser.parse_args()

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
os.makedirs(args.output_dir, exist_ok=True)

SEQ_IN      = args.seq_in
SEQ_OUT     = args.seq_out
BATCH_SIZE  = args.batch_size
EPOCHS      = args.epochs
LR          = args.lr
PATIENCE    = args.patience
RANDOM_SEED = 42

amax_knots  = 0.15
amax        = amax_knots * 0.514
proj        = Proj(proj="utm", zone=31, ellps="WGS84")

np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

# -----------------------------------------------------------------------------
# DEVICE SETUP
# -----------------------------------------------------------------------------
if torch.cuda.is_available():
    n_gpus = torch.cuda.device_count()
    DEVICE = torch.device("cuda:0")
    torch.cuda.manual_seed_all(RANDOM_SEED)
else:
    n_gpus = 0
    DEVICE = torch.device("cpu")

USE_MULTI_GPU = args.multi_gpu and n_gpus > 1

print("=" * 80)
print("  AIS LSTM-TRANSFORMER — SERVEUR ECO (OPTIMISE)")
print("=" * 80)
print(f"  Date        : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  PyTorch     : {torch.__version__}")
print(f"  CUDA dispo  : {torch.cuda.is_available()}")
if torch.cuda.is_available():
    for i in range(n_gpus):
        mem = torch.cuda.get_device_properties(i).total_memory / 1024**3
        print(f"  GPU {i}       : {torch.cuda.get_device_name(i)} ({mem:.0f} GB)")
print(f"  Multi-GPU   : {USE_MULTI_GPU} ({n_gpus} GPU)")
print(f"  Workers DL  : {args.num_workers}")
print(f"  Batch size  : {BATCH_SIZE}")
print(f"  Hidden dim  : {args.hidden_dim}")
print(f"  Epochs max  : {EPOCHS}")
print(f"  Patience    : {PATIENCE}")
print(f"  CSV         : {args.csv_file}")
print(f"  Output dir  : {args.output_dir}")
print("=" * 80)

# -----------------------------------------------------------------------------
# 1. CHARGEMENT DONNEES DEPUIS CSV
# -----------------------------------------------------------------------------
print("\n[1/8] CHARGEMENT DONNEES DEPUIS CSV")
print("-" * 60)

t0 = time.time()
print(f"  Lecture de {args.csv_file} ...")
nrows = args.limit_rows if args.limit_rows else None
df = pd.read_csv(args.csv_file, parse_dates=["BaseDateTime"], nrows=nrows)
print(f"  {len(df):,} lignes chargees en {time.time()-t0:.1f}s")
print(f"     Navires uniques : {df['MMSI'].nunique():,}")
print(f"     Periode : {df['BaseDateTime'].min()} -> {df['BaseDateTime'].max()}")

# -----------------------------------------------------------------------------
# 2. NETTOYAGE
# -----------------------------------------------------------------------------
print("\n[2/8] NETTOYAGE DES DONNEES")
print("-" * 60)

n0 = len(df)
print(f"  Points bruts : {n0:,}")

df = df.dropna(subset=['LAT', 'LON', 'SOG', 'COG'])
print(f"  Valeurs manquantes supprimees -> {len(df):,} ({len(df)/n0*100:.1f}%)")

df = df.drop_duplicates(subset=["MMSI", "BaseDateTime"])
print(f"  Doublons supprimes -> {len(df):,} ({len(df)/n0*100:.1f}%)")

df = df[df["LAT"].between(-90, 90) & df["LON"].between(-180, 180)]
print(f"  Positions invalides filtrees -> {len(df):,}")

df = df[df["SOG"].between(0.1, 30) & df["COG"].between(0, 360)]
print(f"  SOG/COG invalides filtres -> {len(df):,}")

df = df[df["VesselType"].between(20, 90)]
print(f"  Type navire filtre -> {len(df):,}")

df = df.sort_values(["MMSI", "BaseDateTime"])
df["dt"] = df.groupby("MMSI")["BaseDateTime"].diff().dt.total_seconds()
df = df[(df["dt"].isna()) | ((df["dt"] >= 1) & (df["dt"] <= 3600))]
df = df.drop(columns=["dt"])
print(f"  Intervalles filtres -> {len(df):,} ({len(df)/n0*100:.1f}% conserves)")

# -----------------------------------------------------------------------------
# 3. EXTRACTION TRAJECTOIRES
# -----------------------------------------------------------------------------
print("\n[3/8] EXTRACTION TRAJECTOIRES")
print("-" * 60)

def extract_trajectories(df, min_len=30, max_duration_hours=24, min_speed=1.0):
    trajs = []
    stats = {'short': 0, 'duration': 0, 'speed': 0, 'distance': 0}

    for mmsi, g in tqdm(df.groupby("MMSI"), desc="  Navires", ncols=80):
        g = g.sort_values("BaseDateTime").copy()
        g["dt"] = g["BaseDateTime"].diff().dt.total_seconds()
        g["traj_id"] = (g["dt"] > 600).cumsum()

        for _, t in g.groupby("traj_id"):
            if len(t) < min_len:
                stats['short'] += 1
                continue
            dur = (t["BaseDateTime"].iloc[-1] - t["BaseDateTime"].iloc[0]).total_seconds() / 3600
            if dur > max_duration_hours or dur < 0.5:
                stats['duration'] += 1
                continue
            if t["SOG"].mean() < min_speed:
                stats['speed'] += 1
                continue
            x, y = proj(t["LON"].values, t["LAT"].values)
            dist = np.sum(np.sqrt(np.diff(x)**2 + np.diff(y)**2))
            if dist < 1000:
                stats['distance'] += 1
                continue
            trajs.append(t.reset_index(drop=True))

    print(f"  Trajectoires extraites  : {len(trajs):,}")
    print(f"  Trop courtes            : {stats['short']:,}")
    print(f"  Duree invalide          : {stats['duration']:,}")
    print(f"  Vitesse trop faible     : {stats['speed']:,}")
    print(f"  Distance trop faible    : {stats['distance']:,}")
    return trajs

raw_trajs = extract_trajectories(df)
del df; gc.collect()
if not raw_trajs:
    raise ValueError("Aucune trajectoire extraite !")

# -----------------------------------------------------------------------------
# 4. CORRECTIONS PHYSIQUES VECTORISEES + REECHANTILLONNAGE
# -----------------------------------------------------------------------------
print("\n[4/8] CORRECTIONS PHYSIQUES + REECHANTILLONNAGE (VECTORISE)")
print("-" * 60)

def correct_speed_vectorized(traj):
    """Correction vitesse vectorisee — remplace la boucle Python."""
    sog = traj["SOG"].values.copy()
    t = traj["BaseDateTime"].values
    n = len(sog)
    if n < 3:
        return traj, 0

    dt_fwd = np.diff(t) / np.timedelta64(1, "s")  # dt[i] = t[i+1] - t[i]

    # dt1[i] = t[i] - t[i-1], dt2[i] = t[i+1] - t[i] pour i in [1, n-2]
    dt1 = dt_fwd[:-1]   # (n-2,)
    dt2 = dt_fwd[1:]    # (n-2,)

    valid = (dt1 > 0) & (dt2 > 0)
    indices = np.where(valid)[0] + 1  # indices dans sog (decale de 1)

    if len(indices) == 0:
        return traj, 0

    dt1_v = dt1[valid]
    dt2_v = dt2[valid]

    corr_total = 0
    for _ in range(1):  # une passe suffit par appel (on appelle 3x dehors)
        delta = np.abs(sog[indices] - sog[indices - 1])
        max_delta = amax_knots * dt1_v
        need_fix = delta > max_delta

        if not np.any(need_fix):
            break

        fix_idx = indices[need_fix]
        w1 = 1.0 / dt1_v[need_fix]
        w2 = 1.0 / dt2_v[need_fix]
        sog[fix_idx] = (w1 * sog[fix_idx - 1] + w2 * sog[fix_idx + 1]) / (w1 + w2)
        corr_total += int(np.sum(need_fix))

    traj = traj.copy()
    traj["SOG"] = sog
    return traj, corr_total


def correct_position_vectorized(traj):
    """Correction position vectorisee — remplace la boucle Python."""
    lat = traj["LAT"].values.copy()
    lon = traj["LON"].values.copy()
    sog = traj["SOG"].values
    t = traj["BaseDateTime"].values
    n = len(lat)
    if n < 3:
        return traj, 0

    x, y = proj(lon, lat)

    dt_fwd = np.diff(t) / np.timedelta64(1, "s")
    dt1 = dt_fwd[:-1]  # t[i]-t[i-1] pour i in [1..n-2]
    dt2 = dt_fwd[1:]   # t[i+1]-t[i] pour i in [1..n-2]

    valid = (dt1 > 0) & (dt2 > 0)
    indices = np.where(valid)[0] + 1

    if len(indices) == 0:
        return traj, 0

    dt1_v = dt1[valid]
    dt2_v = dt2[valid]

    v = sog[indices - 1] * 0.514
    dmax = v * dt1_v + 0.5 * amax * (dt1_v ** 2)
    dx = x[indices] - x[indices - 1]
    dy = y[indices] - y[indices - 1]
    d = np.sqrt(dx**2 + dy**2)

    need_fix = d > dmax * 1.5
    if not np.any(need_fix):
        return traj, 0

    fix_idx = indices[need_fix]
    dt1_fix = dt1_v[need_fix]
    dt2_fix = dt2_v[need_fix]
    alpha = dt1_fix / (dt1_fix + dt2_fix)

    x[fix_idx] = x[fix_idx - 1] + alpha * (x[fix_idx + 1] - x[fix_idx - 1])
    y[fix_idx] = y[fix_idx - 1] + alpha * (y[fix_idx + 1] - y[fix_idx - 1])

    lon_c, lat_c = proj(x, y, inverse=True)
    traj = traj.copy()
    traj["LAT"] = lat_c
    traj["LON"] = lon_c
    return traj, int(np.sum(need_fix))


def resample_trajectory(traj):
    for col in ["LAT", "LON", "SOG", "COG"]:
        traj[col] = pd.to_numeric(traj[col], errors='coerce')
    # Garder seulement les colonnes utiles et indexer par datetime
    t = traj[["BaseDateTime", "LAT", "LON", "SOG", "COG"]].set_index("BaseDateTime")
    traj_res = t.resample("1min").mean()  # agrège par minute (1 valeur/min)
    # Interpolation linéaire + ffill/bfill pour éliminer les NaN aux bords
    traj_res = traj_res.interpolate(method='linear').ffill().bfill()
    # Supprimer les NaN résiduels
    traj_res = traj_res.dropna(subset=["LAT", "LON", "SOG", "COG"])
    if len(traj_res) == 0:
        return traj_res.reset_index()
    x, y = proj(traj_res["LON"].values, traj_res["LAT"].values)
    dist  = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
    sog_c = dist / 60 / 0.514
    traj_res["SOG"] = np.insert(sog_c, 0, traj_res["SOG"].iloc[0])
    cog = np.unwrap(np.deg2rad(traj_res["COG"].values))
    traj_res["COG"] = np.rad2deg(cog) % 360
    return traj_res.reset_index()


processed_trajs = []
total_sc = total_pc = 0
for traj in tqdm(raw_trajs, desc="  Traitement", ncols=80):
    for _ in range(3):
        traj, s = correct_speed_vectorized(traj)
        traj, p = correct_position_vectorized(traj)
        total_sc += s
        total_pc += p
    traj_res = resample_trajectory(traj)
    if len(traj_res) >= SEQ_IN + SEQ_OUT:
        processed_trajs.append(traj_res)

del raw_trajs; gc.collect()
print(f"  Trajectoires finales     : {len(processed_trajs):,}")
print(f"  Corrections vitesse      : {total_sc:,}")
print(f"  Corrections position     : {total_pc:,}")

# -----------------------------------------------------------------------------
# 5. SPLIT TRAIN / VAL / TEST
# -----------------------------------------------------------------------------
print("\n[5/8] SPLIT TRAIN / VAL / TEST")
print("-" * 60)

train_t, temp  = train_test_split(processed_trajs, test_size=0.3,  random_state=RANDOM_SEED)
val_t,   test_t = train_test_split(temp,            test_size=0.5,  random_state=RANDOM_SEED)

n_total = len(processed_trajs)
print(f"  Train : {len(train_t):,}  ({len(train_t)/n_total*100:.1f}%)")
print(f"  Val   : {len(val_t):,}  ({len(val_t)/n_total*100:.1f}%)")
print(f"  Test  : {len(test_t):,}  ({len(test_t)/n_total*100:.1f}%)")

# -----------------------------------------------------------------------------
# 6. DATASET PYTORCH
# -----------------------------------------------------------------------------
print("\n[6/8] CREATION DATASETS PYTORCH")
print("-" * 60)

class AISTrajDataset(Dataset):
    def __init__(self, trajectories, seq_in=20, seq_out=10, scaler=None, fit_scaler=False):
        self.seq_in  = seq_in
        self.seq_out = seq_out
        X_list, Y_list = [], []
        lat0_list, lon0_list = [], []
        all_features = []

        for traj in trajectories:
            lat  = traj["LAT"].values
            lon  = traj["LON"].values
            sog  = traj["SOG"].values
            cog  = traj["COG"].values
            lat0, lon0 = float(lat[0]), float(lon[0])

            dx       = (lat - lat0) * 111320
            dy       = (lon - lon0) * 111320 * np.cos(np.deg2rad(lat0))
            sog_norm = sog / 30.0
            cog_rad  = np.deg2rad(cog)
            sin_cog  = np.sin(cog_rad)
            cos_cog  = np.cos(cog_rad)
            dt       = np.ones(len(traj)) * 60.0

            feats = np.stack([dx, dy, sog_norm, sin_cog, cos_cog, dt], axis=1)
            all_features.append(feats)

            # Ignorer si NaN dans les features
            if np.isnan(feats).any():
                continue
            for i in range(len(feats) - seq_in - seq_out + 1):
                X_list.append(feats[i:i+seq_in])
                Y_list.append(feats[i+seq_in:i+seq_in+seq_out])
                lat0_list.append(lat0)
                lon0_list.append(lon0)

        if fit_scaler:
            all_f = np.concatenate(all_features, axis=0)
            self.scaler = StandardScaler()
            self.scaler.fit(all_f[:, :2])
            print(f"  Scaler : mu={self.scaler.mean_}, sigma={self.scaler.scale_}")
        else:
            self.scaler = scaler

        del all_features

        print(f"  Conversion en numpy arrays ({len(X_list):,} samples)...")
        sys.stdout.flush()
        X_np = np.array(X_list, dtype=np.float32)
        Y_np = np.array(Y_list, dtype=np.float32)
        del X_list, Y_list

        if self.scaler:
            n = X_np.shape[0]
            X_pos = X_np[:, :, :2].reshape(-1, 2)
            X_pos = self.scaler.transform(X_pos).reshape(n, seq_in, 2).astype(np.float32)
            X_np[:, :, :2] = X_pos
            del X_pos
            Y_pos = Y_np[:, :, :2].reshape(-1, 2)
            Y_pos = self.scaler.transform(Y_pos).reshape(n, seq_out, 2).astype(np.float32)
            Y_np[:, :, :2] = Y_pos
            del Y_pos

        self.X = torch.from_numpy(X_np)
        self.Y = torch.from_numpy(Y_np)
        self.lat0 = torch.tensor(lat0_list, dtype=torch.float64)
        self.lon0 = torch.tensor(lon0_list, dtype=torch.float64)
        del X_np, Y_np, lat0_list, lon0_list

        mem_gb = (self.X.nbytes + self.Y.nbytes + self.lat0.nbytes + self.lon0.nbytes) / 1024**3
        print(f"  Memoire tenseurs : {mem_gb:.2f} GB")
        sys.stdout.flush()

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):
        return self.X[i], self.Y[i], self.lat0[i], self.lon0[i]


print("  Creation Train dataset...")
sys.stdout.flush()
train_ds = AISTrajDataset(train_t, SEQ_IN, SEQ_OUT, fit_scaler=True)
print(f"  Train : {len(train_ds):,} samples")
del train_t; gc.collect()

print("  Creation Val dataset...")
sys.stdout.flush()
val_ds   = AISTrajDataset(val_t,   SEQ_IN, SEQ_OUT, scaler=train_ds.scaler)
print(f"  Val   : {len(val_ds):,} samples")
del val_t; gc.collect()

print("  Creation Test dataset...")
sys.stdout.flush()
test_ds  = AISTrajDataset(test_t,  SEQ_IN, SEQ_OUT, scaler=train_ds.scaler)
print(f"  Test  : {len(test_ds):,} samples")
del test_t, processed_trajs; gc.collect()

scaler_path = os.path.join(args.output_dir, "scaler.pkl")
with open(scaler_path, "wb") as f:
    pickle.dump(train_ds.scaler, f)
print(f"  Scaler sauvegarde : {scaler_path}")

rss_gb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2
print(f"  RSS memoire processus : {rss_gb:.1f} GB")
sys.stdout.flush()

pin_mem = torch.cuda.is_available()
train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                          num_workers=args.num_workers, pin_memory=pin_mem,
                          persistent_workers=args.num_workers > 0)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,
                          num_workers=args.num_workers, pin_memory=pin_mem,
                          persistent_workers=args.num_workers > 0)
test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False,
                          num_workers=args.num_workers, pin_memory=pin_mem,
                          persistent_workers=args.num_workers > 0)

# -----------------------------------------------------------------------------
# 7. ARCHITECTURE DU MODELE
# -----------------------------------------------------------------------------
print("\n[7/8] CONSTRUCTION DU MODELE")
print("-" * 60)

class ImprovedLSTMTransformer(nn.Module):
    def __init__(self, input_dim=6, hidden_dim=512, num_layers=4,
                 num_heads=8, dropout=0.2):
        super().__init__()

        self.embed = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        self.lstm = nn.LSTM(
            hidden_dim, hidden_dim // 2, num_layers=2,
            batch_first=True, bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim, nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout, batch_first=True, activation='gelu'
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, input_dim)
        )
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        embedded       = self.embed(x)
        lstm_out, _    = self.lstm(embedded)
        transformer_out = self.transformer(lstm_out)
        output         = self.output_proj(transformer_out + lstm_out)
        return output


class CustomLoss(nn.Module):
    def __init__(self, pos_w=2.0, vel_w=1.0, dir_w=1.0):
        super().__init__()
        self.pos_w, self.vel_w, self.dir_w = pos_w, vel_w, dir_w

    def forward(self, pred, target):
        pos_loss = torch.mean((pred[:, :, :2] - target[:, :, :2]) ** 2)
        vel_loss = torch.mean((pred[:, :,  2] - target[:, :,  2]) ** 2)
        dir_loss = torch.mean((pred[:, :, 3:5] - target[:, :, 3:5]) ** 2)
        return self.pos_w * pos_loss + self.vel_w * vel_loss + self.dir_w * dir_loss


_model = ImprovedLSTMTransformer(
    input_dim=6,
    hidden_dim=args.hidden_dim,
    num_layers=args.num_layers,
    num_heads=args.num_heads,
    dropout=args.dropout
)

# DataParallel desactive (deadlock cuBLAS sur ECO) — 1 L40S 44GB suffit largement
if USE_MULTI_GPU and n_gpus > 1:
    print(f"  Multi-GPU detecte ({n_gpus} GPU) — DataParallel desactive (cuBLAS deadlock), single GPU utilise")
model = _model.to(DEVICE)

params = sum(p.numel() for p in model.parameters())
print(f"  Parametres totaux : {params:,}")
print(f"  Taille memoire    : {params*4/1024/1024:.1f} MB")

criterion = CustomLoss(2.0, 1.0, 1.0)
optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-5)
scheduler = ReduceLROnPlateau(optimizer, 'min', factor=0.5, patience=7, verbose=True)

USE_AMP = torch.cuda.is_available()
print(f"  AMP (Mixed Precision BF16) active : {USE_AMP}")
# torch.compile() desactive : Triton/inductor crashe au runtime sur ECO (gcc build fail)
# Le try/except ne protege pas le forward pass, seulement le wrapping initial.
print("  torch.compile() desactive (Triton inductor incompatible avec l'env ECO)")

# -----------------------------------------------------------------------------
# FONCTIONS TRAIN / VALIDATE / METRICS (VECTORISEES)
# -----------------------------------------------------------------------------
def train_epoch(model, loader, optimizer, criterion):
    model.train()
    total_loss = 0
    pbar = tqdm(loader, desc="  train", ncols=80, leave=False)
    for x, y, _lat0, _lon0 in pbar:
        x, y = x.to(DEVICE, non_blocking=True), y.to(DEVICE, non_blocking=True)
        optimizer.zero_grad(set_to_none=True)
        with autocast('cuda', dtype=torch.bfloat16, enabled=USE_AMP):
            pred = model(x)[:, -SEQ_OUT:, :]
            loss = criterion(pred, y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        batch_loss = loss.item()
        total_loss += batch_loss * x.size(0)
        pbar.set_postfix({'loss': f'{batch_loss:.4f}'})
    return total_loss / len(loader.dataset)

def validate(model, loader, criterion):
    model.eval()
    total_loss = 0
    with torch.no_grad():
        for x, y, _lat0, _lon0 in tqdm(loader, desc="  val  ", ncols=80, leave=False):
            x, y = x.to(DEVICE, non_blocking=True), y.to(DEVICE, non_blocking=True)
            with autocast('cuda', dtype=torch.bfloat16, enabled=USE_AMP):
                pred = model(x)[:, -SEQ_OUT:, :]
                loss = criterion(pred, y)
            total_loss += loss.item() * x.size(0)
    return total_loss / len(loader.dataset)

def haversine_np(lat1, lon1, lat2, lon2):
    """Haversine vectorise sur des arrays numpy."""
    R = 6371000.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = phi2 - phi1
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

def calculate_metrics(model, loader, scaler):
    """Metriques vectorisees par batch entier — plus de boucle sample par sample."""
    model.eval()
    all_ade, all_fde, all_pos, all_vel = [], [], [], []

    scaler_mean = scaler.mean_.astype(np.float32)
    scaler_scale = scaler.scale_.astype(np.float32)

    with torch.no_grad():
        for x, y, lat0_batch, lon0_batch in loader:
            x = x.to(DEVICE, non_blocking=True)
            pred = model(x)[:, -SEQ_OUT:, :].cpu().numpy()  # (B, T, 6)
            y_np = y.numpy()                                 # (B, T, 6)
            lat0 = lat0_batch.numpy()                        # (B,)
            lon0 = lon0_batch.numpy()                        # (B,)

            B, T = pred.shape[0], pred.shape[1]

            # Inverse scaler sur positions (colonnes 0,1)
            p_pos = pred[:, :, :2] * scaler_scale + scaler_mean  # (B, T, 2)
            y_pos = y_np[:, :, :2] * scaler_scale + scaler_mean  # (B, T, 2)

            # Convertir dx/dy -> lat/lon
            p_lat = lat0[:, None] + p_pos[:, :, 0] / 111320            # (B, T)
            p_lon = lon0[:, None] + p_pos[:, :, 1] / (111320 * np.cos(np.deg2rad(lat0[:, None])))
            t_lat = lat0[:, None] + y_pos[:, :, 0] / 111320
            t_lon = lon0[:, None] + y_pos[:, :, 1] / (111320 * np.cos(np.deg2rad(lat0[:, None])))

            # Haversine vectorise (B, T)
            dists = haversine_np(p_lat, p_lon, t_lat, t_lon)

            all_ade.append(dists.mean(axis=1))     # (B,)
            all_fde.append(dists[:, -1])            # (B,)

            pos_err = np.sqrt((p_pos[:, :, 0] - y_pos[:, :, 0])**2 +
                              (p_pos[:, :, 1] - y_pos[:, :, 1])**2)
            all_pos.append(pos_err.mean(axis=1))

            vel_err = np.abs(pred[:, :, 2] * 30 - y_np[:, :, 2] * 30)
            all_vel.append(vel_err.mean(axis=1))

    return {
        'ADE': float(np.concatenate(all_ade).mean()),
        'FDE': float(np.concatenate(all_fde).mean()),
        'Position_Error_m': float(np.concatenate(all_pos).mean()),
        'Velocity_Error_knots': float(np.concatenate(all_vel).mean())
    }

# -----------------------------------------------------------------------------
# 8. ENTRAINEMENT
# -----------------------------------------------------------------------------
print("\n[8/8] ENTRAINEMENT")
print("=" * 80)
sys.stdout.flush()

history = {'train_loss': [], 'val_loss': [], 'val_ade': [], 'val_fde': [], 'lr': []}
best_val_loss    = float('inf')
patience_counter = 0
start_global     = time.time()

log_path = os.path.join(args.output_dir, "training_log.txt")
log_file = open(log_path, "w")
log_file.write(f"Epoch,TrainLoss,ValLoss,ADE,FDE,LR,Time\n")
log_file.flush()

try:
    for epoch in range(EPOCHS):
        t0 = time.time()

        train_loss = train_epoch(model, train_loader, optimizer, criterion)
        val_loss   = validate(model, val_loader, criterion)

        if epoch % 5 == 0:
            m   = calculate_metrics(model, val_loader, train_ds.scaler)
            ade, fde = m['ADE'], m['FDE']
        else:
            ade = history['val_ade'][-1] if history['val_ade'] else 0
            fde = history['val_fde'][-1] if history['val_fde'] else 0

        scheduler.step(val_loss)
        lr      = optimizer.param_groups[0]['lr']
        elapsed = time.time() - t0

        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['val_ade'].append(ade)
        history['val_fde'].append(fde)
        history['lr'].append(lr)

        is_best = val_loss < best_val_loss
        flag    = " * BEST" if is_best else ""

        line = (f"E{epoch+1:3d}/{EPOCHS} | "
                f"TL:{train_loss:.6f} | VL:{val_loss:.6f} | "
                f"ADE:{ade:7.1f}m | FDE:{fde:7.1f}m | "
                f"LR:{lr:.2e} | {elapsed:.1f}s{flag}")
        print(line)
        sys.stdout.flush()

        log_file.write(f"{epoch+1},{train_loss:.6f},{val_loss:.6f},{ade:.2f},{fde:.2f},{lr:.2e},{elapsed:.1f}\n")
        log_file.flush()

        if is_best:
            best_val_loss    = val_loss
            patience_counter = 0
            best_path = os.path.join(args.output_dir, "best_model.pth")
            torch.save({
                'epoch':                epoch,
                'model_state_dict':     model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss':             val_loss,
                'ade':                  ade,
                'fde':                  fde,
                'args':                 vars(args),
            }, best_path)
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                print(f"\n  EARLY STOPPING a l'epoch {epoch+1} (patience={PATIENCE})")
                break

except Exception as e:
    import traceback
    print(f"\n  ERREUR pendant l'entrainement : {e}", file=sys.stderr)
    traceback.print_exc()
    sys.stderr.flush()
finally:
    log_file.close()

# -----------------------------------------------------------------------------
# EVALUATION FINALE SUR LE TEST SET
# -----------------------------------------------------------------------------
print("\n" + "=" * 80)
print("  EVALUATION FINALE — TEST SET")
print("=" * 80)

checkpoint = torch.load(os.path.join(args.output_dir, "best_model.pth"),
                        map_location=DEVICE, weights_only=True)
model.load_state_dict(checkpoint['model_state_dict'])

test_m = calculate_metrics(model, test_loader, train_ds.scaler)

print(f"  ADE (Average Displacement Error) : {test_m['ADE']:.2f} m")
print(f"  FDE (Final Displacement Error)   : {test_m['FDE']:.2f} m")
print(f"  Erreur position moyenne           : {test_m['Position_Error_m']:.2f} m")
print(f"  Erreur vitesse moyenne            : {test_m['Velocity_Error_knots']:.2f} kn")

total_time = time.time() - start_global
print("\n" + "=" * 80)
print("  TERMINE")
print("=" * 80)
print(f"  Temps total      : {total_time/60:.1f} min")
print(f"  Meilleure loss   : {best_val_loss:.6f}")
print(f"  Fichiers generes :")
print(f"    {args.output_dir}/best_model.pth")
print(f"    {args.output_dir}/scaler.pkl")
print(f"    {args.output_dir}/history.pkl")
print(f"    {args.output_dir}/training_log.txt")
print("=" * 80)

history_path = os.path.join(args.output_dir, "history.pkl")
with open(history_path, "wb") as f:
    pickle.dump(history, f)
