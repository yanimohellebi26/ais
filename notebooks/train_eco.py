#!/usr/bin/env python3
"""
=============================================================================
AIS LSTM-Transformer - Script d'entraînement optimisé pour serveur ECO
=============================================================================
Serveur : ym519512@eco
CPU     : 2× AMD EPYC 9254 → 96 cœurs
RAM     : 1 TB
GPU     : 2× NVIDIA L40S (46 GB chacun)
CUDA    : 13.1 | Driver: 590.48.01
Source  : PostgreSQL → position_vessel + vessel
=============================================================================
"""

import os
import sys
import gc
import math
import pickle
import time
import argparse
import resource
from datetime import datetime

import numpy as np
import pandas as pd
import psycopg2
import sqlalchemy
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tqdm.auto import tqdm
from pyproj import Proj

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim.lr_scheduler import ReduceLROnPlateau

# ─────────────────────────────────────────────────────────────────────────────
# ARGUMENTS CLI
# ─────────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="AIS LSTM-Transformer Training on ECO")
parser.add_argument("--pg-host",     default="localhost",   help="PostgreSQL host")
parser.add_argument("--pg-port",     default=5432,          type=int)
parser.add_argument("--pg-user",     default="postgres")
parser.add_argument("--pg-password", default="ANjw/84H77C9h2")
parser.add_argument("--pg-db",       default="ais")
parser.add_argument("--epochs",      default=150,           type=int)
parser.add_argument("--batch-size",  default=512,           type=int,  help="Batch size (grand = meilleur GPU utilization)")
parser.add_argument("--lr",          default=1e-3,          type=float)
parser.add_argument("--patience",    default=20,            type=int)
parser.add_argument("--seq-in",      default=20,            type=int)
parser.add_argument("--seq-out",     default=10,            type=int)
parser.add_argument("--hidden-dim",  default=512,           type=int,  help="Dimension cachée du modèle")
parser.add_argument("--num-layers",  default=4,             type=int)
parser.add_argument("--num-heads",   default=8,             type=int)
parser.add_argument("--dropout",     default=0.2,           type=float)
parser.add_argument("--num-workers", default=8,             type=int,  help="Workers DataLoader")
parser.add_argument("--multi-gpu",   action="store_true",   default=True, help="Utiliser les 2 GPU L40S")
parser.add_argument("--limit-rows",  default=None,          type=int,  help="Limiter nb lignes BD (debug)")
parser.add_argument("--output-dir",  default="./eco_output", help="Dossier de sortie des modèles")
args = parser.parse_args()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# DEVICE SETUP  (2× L40S via DataParallel)
# ─────────────────────────────────────────────────────────────────────────────
if torch.cuda.is_available():
    n_gpus = torch.cuda.device_count()
    DEVICE = torch.device("cuda:0")
    torch.cuda.manual_seed_all(RANDOM_SEED)
else:
    n_gpus = 0
    DEVICE = torch.device("cpu")

USE_MULTI_GPU = args.multi_gpu and n_gpus > 1

print("=" * 80)
print("  AIS LSTM-TRANSFORMER — SERVEUR ECO")
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
print(f"  Output dir  : {args.output_dir}")
print("=" * 80)

# ─────────────────────────────────────────────────────────────────────────────
# 1. CHARGEMENT DONNÉES DEPUIS POSTGRESQL
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1/8] CHARGEMENT DONNÉES DEPUIS POSTGRESQL")
print("-" * 60)

DB_URL = (f"postgresql+psycopg2://{args.pg_user}:{args.pg_password}"
          f"@{args.pg_host}:{args.pg_port}/{args.pg_db}")

engine = sqlalchemy.create_engine(DB_URL, pool_pre_ping=True)

# Requête : extraire LAT/LON depuis la colonne geography + jointure vessel_type
LIMIT_CLAUSE = f"LIMIT {args.limit_rows}" if args.limit_rows else ""

SQL = f"""
    SELECT
        v.mmsi                                             AS "MMSI",
        pv.base_date_time                                  AS "BaseDateTime",
        ST_Y(pv.geom::geometry)                            AS "LAT",
        ST_X(pv.geom::geometry)                            AS "LON",
        pv.sog                                             AS "SOG",
        pv.cog                                             AS "COG",
        COALESCE(v.vessel_type_id, 0)                      AS "VesselType"
    FROM position_vessel pv
    JOIN vessel v ON v.id = pv.vessel_id
    WHERE pv.sog IS NOT NULL
      AND pv.cog IS NOT NULL
    ORDER BY v.mmsi, pv.base_date_time
    {LIMIT_CLAUSE}
"""

t0 = time.time()
print(f"  Connexion à {args.pg_host}:{args.pg_port}/{args.pg_db} ...")
df = pd.read_sql(SQL, engine, parse_dates=["BaseDateTime"])
print(f"  ✅ {len(df):,} lignes chargées en {time.time()-t0:.1f}s")
print(f"     Navires uniques : {df['MMSI'].nunique():,}")
print(f"     Période : {df['BaseDateTime'].min()} → {df['BaseDateTime'].max()}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. NETTOYAGE
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2/8] NETTOYAGE DES DONNÉES")
print("-" * 60)

n0 = len(df)
print(f"  Points bruts : {n0:,}")

df = df.dropna(subset=['LAT', 'LON', 'SOG', 'COG'])
print(f"  ✓ Valeurs manquantes supprimées → {len(df):,} ({len(df)/n0*100:.1f}%)")

df = df.drop_duplicates(subset=["MMSI", "BaseDateTime"])
print(f"  ✓ Doublons supprimés → {len(df):,} ({len(df)/n0*100:.1f}%)")

df = df[df["LAT"].between(-90, 90) & df["LON"].between(-180, 180)]
print(f"  ✓ Positions invalides filtrées → {len(df):,}")

df = df[df["SOG"].between(0.1, 30) & df["COG"].between(0, 360)]
print(f"  ✓ SOG/COG invalides filtrés → {len(df):,}")

df = df[df["VesselType"].between(20, 90)]
print(f"  ✓ Type navire filtré → {len(df):,}")

df["dt"] = df.groupby("MMSI")["BaseDateTime"].diff().dt.total_seconds()
df = df[(df["dt"].isna()) | ((df["dt"] >= 1) & (df["dt"] <= 3600))]
df = df.drop(columns=["dt"])
print(f"  ✓ Intervalles filtrés → {len(df):,} ({len(df)/n0*100:.1f}% conservés)")

# ─────────────────────────────────────────────────────────────────────────────
# 3. EXTRACTION TRAJECTOIRES
# ─────────────────────────────────────────────────────────────────────────────
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
    print(f"  ❌ Trop courtes         : {stats['short']:,}")
    print(f"  ❌ Durée invalide       : {stats['duration']:,}")
    print(f"  ❌ Vitesse trop faible  : {stats['speed']:,}")
    print(f"  ❌ Distance trop faible : {stats['distance']:,}")
    return trajs

raw_trajs = extract_trajectories(df)
if not raw_trajs:
    raise ValueError("Aucune trajectoire extraite !")

# ─────────────────────────────────────────────────────────────────────────────
# 4. CORRECTIONS PHYSIQUES + RÉÉCHANTILLONNAGE
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4/8] CORRECTIONS PHYSIQUES + RÉÉCHANTILLONNAGE")
print("-" * 60)

def correct_speed(traj):
    sog = traj["SOG"].values.copy()
    t   = traj["BaseDateTime"].values
    corr = 0
    for i in range(1, len(traj) - 1):
        dt1 = (t[i] - t[i-1]) / np.timedelta64(1, "s")
        dt2 = (t[i+1] - t[i]) / np.timedelta64(1, "s")
        if dt1 <= 0 or dt2 <= 0:
            continue
        if abs(sog[i] - sog[i-1]) > amax_knots * dt1:
            w1, w2 = 1.0/dt1, 1.0/dt2
            sog[i] = (w1*sog[i-1] + w2*sog[i+1]) / (w1+w2)
            corr += 1
    traj = traj.copy()
    traj["SOG"] = sog
    return traj, corr

def correct_position(traj):
    lat = traj["LAT"].values.copy()
    lon = traj["LON"].values.copy()
    sog = traj["SOG"].values
    t   = traj["BaseDateTime"].values
    x, y = proj(lon, lat)
    corr = 0
    for i in range(1, len(traj) - 1):
        dt = (t[i] - t[i-1]) / np.timedelta64(1, "s")
        if dt <= 0:
            continue
        dmax = sog[i-1]*0.514*dt + 0.5*amax*(dt**2)
        if math.hypot(x[i]-x[i-1], y[i]-y[i-1]) > dmax * 1.5:
            dt2 = (t[i+1] - t[i]) / np.timedelta64(1, "s")
            if dt2 <= 0:
                continue
            alpha = dt / (dt + dt2)
            x[i] = x[i-1] + alpha * (x[i+1] - x[i-1])
            y[i] = y[i-1] + alpha * (y[i+1] - y[i-1])
            corr += 1
    lon_c, lat_c = proj(x, y, inverse=True)
    traj = traj.copy()
    traj["LAT"] = lat_c
    traj["LON"] = lon_c
    return traj, corr

def resample_trajectory(traj):
    for col in ["LAT", "LON", "SOG", "COG"]:
        traj[col] = pd.to_numeric(traj[col], errors='coerce')
    traj = traj.set_index("BaseDateTime")
    traj = traj.infer_objects(copy=False)
    traj_res = traj.resample("1min").interpolate(method='linear')
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
        traj, s = correct_speed(traj)
        traj, p = correct_position(traj)
        total_sc += s
        total_pc += p
    traj_res = resample_trajectory(traj)
    if len(traj_res) >= SEQ_IN + SEQ_OUT:
        processed_trajs.append(traj_res)

print(f"  Trajectoires finales     : {len(processed_trajs):,}")
print(f"  Corrections vitesse      : {total_sc:,}")
print(f"  Corrections position     : {total_pc:,}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. SPLIT TRAIN / VAL / TEST
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5/8] SPLIT TRAIN / VAL / TEST")
print("-" * 60)

train_t, temp  = train_test_split(processed_trajs, test_size=0.3,  random_state=RANDOM_SEED)
val_t,   test_t = train_test_split(temp,            test_size=0.5,  random_state=RANDOM_SEED)

n_total = len(processed_trajs)
print(f"  🔵 Train : {len(train_t):,}  ({len(train_t)/n_total*100:.1f}%)")
print(f"  🟡 Val   : {len(val_t):,}  ({len(val_t)/n_total*100:.1f}%)")
print(f"  🟢 Test  : {len(test_t):,}  ({len(test_t)/n_total*100:.1f}%)")

# ─────────────────────────────────────────────────────────────────────────────
# 6. DATASET PYTORCH
# ─────────────────────────────────────────────────────────────────────────────
print("\n[6/8] CRÉATION DATASETS PYTORCH")
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

            for i in range(len(feats) - seq_in - seq_out + 1):
                X_list.append(feats[i:i+seq_in])
                Y_list.append(feats[i+seq_in:i+seq_in+seq_out])
                lat0_list.append(lat0)
                lon0_list.append(lon0)

        if fit_scaler:
            all_f = np.concatenate(all_features, axis=0)
            self.scaler = StandardScaler()
            self.scaler.fit(all_f[:, :2])
            print(f"  Scaler : μ={self.scaler.mean_}, σ={self.scaler.scale_}")
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
        print(f"  Mémoire tenseurs : {mem_gb:.2f} GB")
        sys.stdout.flush()

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):
        return self.X[i], self.Y[i], self.lat0[i], self.lon0[i]


print("  Création Train dataset...")
sys.stdout.flush()
train_ds = AISTrajDataset(train_t, SEQ_IN, SEQ_OUT, fit_scaler=True)
print(f"  ✅ Train : {len(train_ds):,} samples")
del train_t; gc.collect()

print("  Création Val dataset...")
sys.stdout.flush()
val_ds   = AISTrajDataset(val_t,   SEQ_IN, SEQ_OUT, scaler=train_ds.scaler)
print(f"  ✅ Val   : {len(val_ds):,} samples")
del val_t; gc.collect()

print("  Création Test dataset...")
sys.stdout.flush()
test_ds  = AISTrajDataset(test_t,  SEQ_IN, SEQ_OUT, scaler=train_ds.scaler)
print(f"  ✅ Test  : {len(test_ds):,} samples")
del test_t, processed_trajs; gc.collect()

scaler_path = os.path.join(args.output_dir, "scaler.pkl")
with open(scaler_path, "wb") as f:
    pickle.dump(train_ds.scaler, f)
print(f"  💾 Scaler sauvegardé : {scaler_path}")

# Mémoire RSS actuelle
rss_gb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2
print(f"  📊 RSS mémoire processus : {rss_gb:.1f} GB")
sys.stdout.flush()

# DataLoaders — pin_memory + persistent_workers pour maximiser le débit GPU
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

# ─────────────────────────────────────────────────────────────────────────────
# 7. ARCHITECTURE DU MODÈLE
# ─────────────────────────────────────────────────────────────────────────────
print("\n[7/8] CONSTRUCTION DU MODÈLE")
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

# DataParallel sur les 2 L40S
if USE_MULTI_GPU:
    _model = nn.DataParallel(_model, device_ids=list(range(n_gpus)))
    print(f"  ⚡ DataParallel activé sur {n_gpus} GPU")

model = _model.to(DEVICE)

params = sum(p.numel() for p in model.parameters())
print(f"  Paramètres totaux : {params:,}")
print(f"  Taille mémoire    : {params*4/1024/1024:.1f} MB")

criterion = CustomLoss(2.0, 1.0, 1.0)
optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-5)
scheduler = ReduceLROnPlateau(optimizer, 'min', factor=0.5, patience=7, verbose=True)

# ─────────────────────────────────────────────────────────────────────────────
# FONCTIONS TRAIN / VALIDATE / METRICS
# ─────────────────────────────────────────────────────────────────────────────
def train_epoch(model, loader, optimizer, criterion):
    model.train()
    total_loss = 0
    for x, y, _lat0, _lon0 in loader:
        x, y = x.to(DEVICE, non_blocking=True), y.to(DEVICE, non_blocking=True)
        optimizer.zero_grad()
        pred = model(x)[:, -SEQ_OUT:, :]
        loss = criterion(pred, y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        total_loss += loss.item() * x.size(0)
    return total_loss / len(loader.dataset)

def validate(model, loader, criterion):
    model.eval()
    total_loss = 0
    with torch.no_grad():
        for x, y, _lat0, _lon0 in loader:
            x, y = x.to(DEVICE, non_blocking=True), y.to(DEVICE, non_blocking=True)
            pred = model(x)[:, -SEQ_OUT:, :]
            loss = criterion(pred, y)
            total_loss += loss.item() * x.size(0)
    return total_loss / len(loader.dataset)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi  = phi2 - phi1
    dlam  = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

def calculate_metrics(model, loader, scaler):
    model.eval()
    all_ade, all_fde, all_pos, all_vel = [], [], [], []
    with torch.no_grad():
        for x, y, lat0_batch, lon0_batch in loader:
            x    = x.to(DEVICE, non_blocking=True)
            pred = model(x)[:, -SEQ_OUT:, :].cpu()
            for b in range(pred.shape[0]):
                p_d, y_d = pred[b].clone(), y[b].clone()
                p_d[:, :2] = torch.tensor(scaler.inverse_transform(p_d[:, :2].numpy()), dtype=torch.float32)
                y_d[:, :2] = torch.tensor(scaler.inverse_transform(y_d[:, :2].numpy()), dtype=torch.float32)
                lat0 = lat0_batch[b].item()
                lon0 = lon0_batch[b].item()
                p_lat = lat0 + p_d[:, 0].numpy() / 111320
                p_lon = lon0 + p_d[:, 1].numpy() / (111320 * np.cos(np.deg2rad(lat0)))
                t_lat = lat0 + y_d[:, 0].numpy() / 111320
                t_lon = lon0 + y_d[:, 1].numpy() / (111320 * np.cos(np.deg2rad(lat0)))
                dists = np.array([haversine(p_lat[i], p_lon[i], t_lat[i], t_lon[i])
                                  for i in range(len(p_lat))])
                all_ade.append(dists.mean())
                all_fde.append(dists[-1])
                pos_err = np.sqrt((p_d[:, 0].numpy()-y_d[:, 0].numpy())**2 +
                                  (p_d[:, 1].numpy()-y_d[:, 1].numpy())**2)
                all_pos.append(pos_err.mean())
                vel_err = np.abs(p_d[:, 2].numpy()*30 - y_d[:, 2].numpy()*30)
                all_vel.append(vel_err.mean())
    return {
        'ADE': np.mean(all_ade),
        'FDE': np.mean(all_fde),
        'Position_Error_m': np.mean(all_pos),
        'Velocity_Error_knots': np.mean(all_vel)
    }

# ─────────────────────────────────────────────────────────────────────────────
# 8. ENTRAÎNEMENT
# ─────────────────────────────────────────────────────────────────────────────
print("\n[8/8] ENTRAÎNEMENT")
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

        # Métriques complètes tous les 5 epochs
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
        flag    = " ★ BEST" if is_best else ""

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
                print(f"\n⏹  EARLY STOPPING à l'epoch {epoch+1} (patience={PATIENCE})")
                break

except Exception as e:
    import traceback
    print(f"\n❌ ERREUR pendant l'entraînement : {e}", file=sys.stderr)
    traceback.print_exc()
    sys.stderr.flush()
finally:
    log_file.close()

# ─────────────────────────────────────────────────────────────────────────────
# ÉVALUATION FINALE SUR LE TEST SET
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("  ÉVALUATION FINALE — TEST SET")
print("=" * 80)

checkpoint = torch.load(os.path.join(args.output_dir, "best_model.pth"),
                        map_location=DEVICE)
model.load_state_dict(checkpoint['model_state_dict'])

test_m = calculate_metrics(model, test_loader, train_ds.scaler)

print(f"  ADE (Average Displacement Error) : {test_m['ADE']:.2f} m")
print(f"  FDE (Final Displacement Error)   : {test_m['FDE']:.2f} m")
print(f"  Erreur position moyenne           : {test_m['Position_Error_m']:.2f} m")
print(f"  Erreur vitesse moyenne            : {test_m['Velocity_Error_knots']:.2f} kn")

total_time = time.time() - start_global
print("\n" + "=" * 80)
print("  TERMINÉ")
print("=" * 80)
print(f"  Temps total      : {total_time/60:.1f} min")
print(f"  Meilleure loss   : {best_val_loss:.6f}")
print(f"  Fichiers générés :")
print(f"    {args.output_dir}/best_model.pth")
print(f"    {args.output_dir}/scaler.pkl")
print(f"    {args.output_dir}/history.pkl")
print(f"    {args.output_dir}/training_log.txt")
print("=" * 80)

history_path = os.path.join(args.output_dir, "history.pkl")
with open(history_path, "wb") as f:
    pickle.dump(history, f)
