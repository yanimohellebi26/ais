#!/usr/bin/env python3
"""
Script de test du modèle AIS entraîné.
Visualise des prédictions sur des données réelles.
"""

import math
import random
import numpy as np
import pandas as pd
import torch
from torch import nn
import psycopg2
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# CONFIGURATION (doit correspondre au training)
# ==========================================
SEQ_IN = 20
SEQ_OUT = 10
HIDDEN = 256
N_HEADS = 8
N_LAYERS = 4
DROPOUT = 0.15
EMBED_VT = 32
INPUT_DIM = 10
SCALE_POSITION = 10000.0
SCALE_SOG = 15.0
SCALE_DT = 300.0

DB_CONFIG = {
    'host': '172.31.60.8',
    'port': 5432,
    'database': 'ais',
    'user': 'postgres',
    'password': 'ANjw/84H77C9h2'
}

MODEL_PATH = Path("./output/best_model.pth")
OUTPUT_DIR = Path("./output")

# ==========================================
# MODÈLE (copié du training)
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
    
    def forward(self, x):
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)


class AISTransformer(nn.Module):
    def __init__(self, input_dim=INPUT_DIM, vtype_card=100, vtype_emb=EMBED_VT,
                 hidden=HIDDEN, n_heads=N_HEADS, n_layers=N_LAYERS,
                 dropout=DROPOUT, pred_len=SEQ_OUT):
        super().__init__()
        self.hidden = hidden
        self.pred_len = pred_len
        
        self.vessel_embedding = nn.Embedding(vtype_card, vtype_emb)
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
        
        self.decoder_lstm = nn.LSTM(
            input_size=2 + 2 + vtype_emb,
            hidden_size=hidden,
            num_layers=2,
            dropout=dropout,
            batch_first=True
        )
        
        self.output_proj = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Linear(hidden // 2, 2)
        )
        
        self.velocity_proj = nn.Linear(hidden, 2)
    
    def forward(self, x, vtype, out_len=None, **kwargs):
        if out_len is None:
            out_len = self.pred_len
        
        B, T, _ = x.shape
        device = x.device
        
        v_emb = self.vessel_embedding(vtype)
        v_emb_exp = v_emb.unsqueeze(1).expand(-1, T, -1)
        
        x_cat = torch.cat([x, v_emb_exp], dim=2)
        x_proj = self.input_norm(self.input_proj(x_cat))
        x_enc = self.pos_encoder(x_proj)
        memory = self.encoder_norm(self.encoder(x_enc))
        
        context = memory[:, -1]
        velocity = self.velocity_proj(context)
        pos = torch.zeros(B, 2, device=device)
        
        h0 = context.unsqueeze(0).repeat(2, 1, 1)
        c0 = torch.zeros_like(h0)
        
        predictions = []
        for t in range(out_len):
            lstm_in = torch.cat([pos, velocity, v_emb], dim=1).unsqueeze(1)
            out, (h0, c0) = self.decoder_lstm(lstm_in, (h0, c0))
            delta = self.output_proj(out.squeeze(1))
            pos = pos + delta
            predictions.append(pos.unsqueeze(1))
            velocity = delta
        
        return torch.cat(predictions, dim=1)


# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================
def haversine_distance(lat1, lon1, lat2, lon2):
    """Distance en mètres."""
    R = 6371000.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))


def load_sample_trajectories(n_samples=10):
    """Charge des trajectoires exemples depuis la DB."""
    print("📊 Connexion à la base de données...")
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Trouver des navires avec assez de positions
    query = """
    WITH vessel_counts AS (
        SELECT v.mmsi, COUNT(*) as cnt
        FROM position_vessel pv
        JOIN vessel v ON pv.vessel_id = v.id
        WHERE pv.sog >= 0.5 AND pv.sog < 40
        GROUP BY v.mmsi
        HAVING COUNT(*) >= 50
        ORDER BY RANDOM()
        LIMIT %s
    )
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
    WHERE v.mmsi IN (SELECT mmsi FROM vessel_counts)
      AND pv.sog >= 0.5 AND pv.sog < 40
    ORDER BY v.mmsi, pv.base_date_time;
    """
    
    df = pd.read_sql(query, conn, params=(n_samples,))
    conn.close()
    
    print(f"✅ {len(df)} positions pour {df['MMSI'].nunique()} navires")
    return df


def prepare_sequence(trajectory_df, start_idx, seq_in=SEQ_IN, seq_out=SEQ_OUT):
    """Prépare une séquence pour l'inférence."""
    total_len = seq_in + seq_out
    if start_idx + total_len > len(trajectory_df):
        return None
    
    window = trajectory_df.iloc[start_idx:start_idx + total_len]
    
    # Calculer Delta_t
    times = pd.to_datetime(window['BaseDateTime'])
    delta_t = times.diff().dt.total_seconds().fillna(0).values
    
    # Vérifier pas de gap > 10 min
    if (delta_t > 600).any():
        return None
    
    # Données brutes
    lats = window['LAT'].values.astype(np.float32)
    lons = window['LON'].values.astype(np.float32)
    sogs = window['SOG'].values.astype(np.float32)
    cogs = window['COG'].values.astype(np.float32)
    headings = window['Heading'].values.astype(np.float32)
    vtype = int(window['VesselType'].iloc[0])
    
    # Point de référence = dernier point de l'entrée
    base_lat = lats[seq_in - 1]
    base_lon = lons[seq_in - 1]
    
    METER_PER_DEG_LAT = 111320.0
    meter_per_deg_lon = 40075000.0 * math.cos(math.radians(base_lat)) / 360.0
    
    # Features d'entrée normalisées
    inp_lats = lats[:seq_in]
    inp_lons = lons[:seq_in]
    inp_sogs = sogs[:seq_in]
    inp_cogs = cogs[:seq_in]
    inp_headings = headings[:seq_in]
    inp_delta_t = delta_t[:seq_in]
    
    # Accélération et ROT
    dt_safe = np.where(inp_delta_t == 0, 1.0, inp_delta_t)
    accel = np.clip(np.diff(inp_sogs, prepend=inp_sogs[0]) / dt_safe, -0.5, 0.5)
    
    cog_diff = np.diff(inp_cogs, prepend=inp_cogs[0])
    cog_diff = (cog_diff + 180) % 360 - 180
    rot = np.clip(cog_diff / dt_safe, -3, 3)
    
    # Normalisation
    x = np.stack([
        (inp_lats - base_lat) * METER_PER_DEG_LAT / SCALE_POSITION,
        (inp_lons - base_lon) * meter_per_deg_lon / SCALE_POSITION,
        inp_sogs / SCALE_SOG,
        np.sin(np.radians(inp_cogs)),
        np.cos(np.radians(inp_cogs)),
        np.sin(np.radians(inp_headings)),
        np.cos(np.radians(inp_headings)),
        np.clip(inp_delta_t / SCALE_DT, 0, 2),
        accel,
        rot / 3.0
    ], axis=1).astype(np.float32)
    
    # Cibles (ground truth)
    out_lats = lats[seq_in:]
    out_lons = lons[seq_in:]
    
    y = np.stack([
        (out_lats - base_lat) * METER_PER_DEG_LAT / SCALE_POSITION,
        (out_lons - base_lon) * meter_per_deg_lon / SCALE_POSITION
    ], axis=1).astype(np.float32)
    
    return {
        'x': torch.from_numpy(x).unsqueeze(0),
        'y': y,
        'vtype': torch.tensor([vtype], dtype=torch.long),
        'anchor': (base_lat, base_lon),
        'scale_lat': METER_PER_DEG_LAT,
        'scale_lon': meter_per_deg_lon,
        'input_coords': (inp_lats, inp_lons),
        'target_coords': (out_lats, out_lons),
        'times': times.values
    }


def predict_and_visualize(model, sample, device):
    """Fait une prédiction et retourne les coordonnées."""
    model.eval()
    
    with torch.no_grad():
        x = sample['x'].to(device)
        vtype = sample['vtype'].to(device)
        pred = model(x, vtype)
        pred = pred.squeeze(0).cpu().numpy()
    
    # Reconversion en lat/lon
    base_lat, base_lon = sample['anchor']
    scale_lat = sample['scale_lat']
    scale_lon = sample['scale_lon']
    
    pred_lats = base_lat + (pred[:, 0] * SCALE_POSITION) / scale_lat
    pred_lons = base_lon + (pred[:, 1] * SCALE_POSITION) / scale_lon
    
    return pred_lats, pred_lons


def main():
    print("=" * 60)
    print("🚢 Test du modèle AIS Trajectory Prediction")
    print("=" * 60)
    
    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"📱 Device: {device}")
    
    # Charger le modèle
    print(f"\n📦 Chargement du modèle: {MODEL_PATH}")
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    
    config = checkpoint.get('config', {})
    print(f"   Config: {config}")
    print(f"   Epoch: {checkpoint.get('epoch', '?')}")
    print(f"   ADE: {checkpoint.get('ade', '?'):.0f}m")
    print(f"   FDE: {checkpoint.get('fde', '?'):.0f}m")
    
    model = AISTransformer(
        input_dim=config.get('input_dim', INPUT_DIM),
        hidden=config.get('hidden', HIDDEN),
        n_heads=config.get('n_heads', N_HEADS),
        n_layers=config.get('n_layers', N_LAYERS),
        pred_len=config.get('seq_out', SEQ_OUT)
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()
    
    print("✅ Modèle chargé!")
    
    # Charger des données
    print("\n📊 Chargement des trajectoires...")
    df = load_sample_trajectories(n_samples=20)
    
    # Préparer les visualisations
    fig, axes = plt.subplots(3, 3, figsize=(15, 15))
    axes = axes.flatten()
    
    sample_idx = 0
    errors_ade = []
    errors_fde = []
    
    for mmsi, group in df.groupby('MMSI'):
        if sample_idx >= 9:
            break
        
        group = group.reset_index(drop=True)
        
        # Trouver une séquence valide
        for start_idx in range(0, len(group) - SEQ_IN - SEQ_OUT, 10):
            sample = prepare_sequence(group, start_idx)
            if sample is None:
                continue
            
            # Prédiction
            pred_lats, pred_lons = predict_and_visualize(model, sample, device)
            
            # Ground truth
            true_lats, true_lons = sample['target_coords']
            inp_lats, inp_lons = sample['input_coords']
            
            # Calcul erreurs
            distances = haversine_distance(pred_lats, pred_lons, true_lats, true_lons)
            ade = np.mean(distances)
            fde = distances[-1]
            errors_ade.append(ade)
            errors_fde.append(fde)
            
            # Visualisation
            ax = axes[sample_idx]
            
            # Entrée (bleu)
            ax.plot(inp_lons, inp_lats, 'b.-', label='Entrée', linewidth=2, markersize=6)
            
            # Vérité (vert)
            ax.plot(true_lons, true_lats, 'g.-', label='Vérité', linewidth=2, markersize=6)
            
            # Prédiction (rouge)
            ax.plot(pred_lons, pred_lats, 'r.--', label='Prédiction', linewidth=2, markersize=6)
            
            # Connexion
            ax.plot([inp_lons[-1], true_lons[0]], [inp_lats[-1], true_lats[0]], 
                   'g--', alpha=0.5, linewidth=1)
            ax.plot([inp_lons[-1], pred_lons[0]], [inp_lats[-1], pred_lats[0]], 
                   'r--', alpha=0.5, linewidth=1)
            
            ax.set_title(f'MMSI: {mmsi}\nADE: {ade:.0f}m | FDE: {fde:.0f}m')
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            
            sample_idx += 1
            break
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / 'test_predictions.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n📊 Visualisation sauvegardée: {output_path}")
    plt.show()
    
    # Stats finales
    print("\n" + "=" * 60)
    print("📈 Résultats sur échantillon de test:")
    print(f"   ADE moyen: {np.mean(errors_ade):.0f}m (± {np.std(errors_ade):.0f}m)")
    print(f"   FDE moyen: {np.mean(errors_fde):.0f}m (± {np.std(errors_fde):.0f}m)")
    print(f"   ADE min/max: {np.min(errors_ade):.0f}m / {np.max(errors_ade):.0f}m")
    print(f"   FDE min/max: {np.min(errors_fde):.0f}m / {np.max(errors_fde):.0f}m")
    print("=" * 60)


if __name__ == "__main__":
    main()
