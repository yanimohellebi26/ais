#!/usr/bin/env python3
"""
Visualisation des prédictions AIS sur carte interactive (Folium).
"""

import math
import numpy as np
import pandas as pd
import torch
from torch import nn
import psycopg2
import folium
from folium import plugins
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
SEQ_IN = 20      # Doit correspondre au modèle entraîné
SEQ_OUT = 10     # Doit correspondre au modèle entraîné
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
# MODÈLE
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
# FONCTIONS
# ==========================================
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))


def load_trajectories(n_samples=15):
    print("📊 Connexion à la base de données...")
    conn = psycopg2.connect(**DB_CONFIG)
    
    query = """
    WITH vessel_counts AS (
        SELECT v.mmsi, COUNT(*) as cnt
        FROM position_vessel pv
        JOIN vessel v ON pv.vessel_id = v.id
        WHERE pv.sog >= 1.0 AND pv.sog < 30
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
      AND pv.sog >= 1.0 AND pv.sog < 30
    ORDER BY v.mmsi, pv.base_date_time;
    """
    
    df = pd.read_sql(query, conn, params=(n_samples,))
    conn.close()
    print(f"✅ {len(df)} positions pour {df['MMSI'].nunique()} navires")
    return df


def prepare_sequence(trajectory_df, start_idx, seq_in=SEQ_IN, seq_out=SEQ_OUT):
    total_len = seq_in + seq_out
    if start_idx + total_len > len(trajectory_df):
        return None
    
    window = trajectory_df.iloc[start_idx:start_idx + total_len]
    times = pd.to_datetime(window['BaseDateTime'])
    delta_t = times.diff().dt.total_seconds().fillna(0).values
    
    if (delta_t > 600).any():
        return None
    
    lats = window['LAT'].values.astype(np.float32)
    lons = window['LON'].values.astype(np.float32)
    sogs = window['SOG'].values.astype(np.float32)
    cogs = window['COG'].values.astype(np.float32)
    headings = window['Heading'].values.astype(np.float32)
    vtype = int(window['VesselType'].iloc[0])
    
    base_lat = lats[seq_in - 1]
    base_lon = lons[seq_in - 1]
    
    METER_PER_DEG_LAT = 111320.0
    meter_per_deg_lon = 40075000.0 * math.cos(math.radians(base_lat)) / 360.0
    
    inp_lats = lats[:seq_in]
    inp_lons = lons[:seq_in]
    inp_sogs = sogs[:seq_in]
    inp_cogs = cogs[:seq_in]
    inp_headings = headings[:seq_in]
    inp_delta_t = delta_t[:seq_in]
    
    dt_safe = np.where(inp_delta_t == 0, 1.0, inp_delta_t)
    accel = np.clip(np.diff(inp_sogs, prepend=inp_sogs[0]) / dt_safe, -0.5, 0.5)
    cog_diff = np.diff(inp_cogs, prepend=inp_cogs[0])
    cog_diff = (cog_diff + 180) % 360 - 180
    rot = np.clip(cog_diff / dt_safe, -3, 3)
    
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
    
    out_lats = lats[seq_in:]
    out_lons = lons[seq_in:]
    
    return {
        'x': torch.from_numpy(x).unsqueeze(0),
        'vtype': torch.tensor([vtype], dtype=torch.long),
        'anchor': (base_lat, base_lon),
        'scale_lat': METER_PER_DEG_LAT,
        'scale_lon': meter_per_deg_lon,
        'input_coords': list(zip(inp_lats, inp_lons)),
        'target_coords': list(zip(out_lats, out_lons)),
        'mmsi': trajectory_df['MMSI'].iloc[0],
        'times': times.values
    }


def predict(model, sample, device):
    model.eval()
    with torch.no_grad():
        x = sample['x'].to(device)
        vtype = sample['vtype'].to(device)
        pred = model(x, vtype)
        pred = pred.squeeze(0).cpu().numpy()
    
    base_lat, base_lon = sample['anchor']
    scale_lat = sample['scale_lat']
    scale_lon = sample['scale_lon']
    
    pred_lats = base_lat + (pred[:, 0] * SCALE_POSITION) / scale_lat
    pred_lons = base_lon + (pred[:, 1] * SCALE_POSITION) / scale_lon
    
    return list(zip(pred_lats, pred_lons))


def create_map(predictions_data):
    """Crée une carte Folium avec toutes les trajectoires."""
    
    # Centrer la carte sur la moyenne des positions
    all_lats = []
    all_lons = []
    for data in predictions_data:
        for lat, lon in data['input']:
            all_lats.append(lat)
            all_lons.append(lon)
    
    center_lat = np.mean(all_lats)
    center_lon = np.mean(all_lons)
    
    # Créer la carte
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='CartoDB positron'
    )
    
    # Ajouter plusieurs fonds de carte
    folium.TileLayer('OpenStreetMap').add_to(m)
    folium.TileLayer('CartoDB dark_matter').add_to(m)
    
    # Couleurs pour différents navires
    colors = ['blue', 'green', 'red', 'purple', 'orange', 'darkred', 
              'darkblue', 'darkgreen', 'cadetblue', 'pink']
    
    for idx, data in enumerate(predictions_data):
        color = colors[idx % len(colors)]
        mmsi = data['mmsi']
        ade = data['ade']
        fde = data['fde']
        
        # Groupe pour ce navire
        fg = folium.FeatureGroup(name=f"MMSI {mmsi} (ADE: {ade:.0f}m)")
        
        # Trajectoire d'entrée (bleue, ligne pleine)
        input_coords = data['input']
        folium.PolyLine(
            input_coords,
            color='blue',
            weight=3,
            opacity=0.8,
            popup=f"Entrée - MMSI: {mmsi}"
        ).add_to(fg)
        
        # Marqueurs d'entrée
        for i, (lat, lon) in enumerate(input_coords):
            folium.CircleMarker(
                [lat, lon],
                radius=4,
                color='blue',
                fill=True,
                fillOpacity=0.7,
                popup=f"Input {i+1}"
            ).add_to(fg)
        
        # Dernier point d'entrée (point de départ prédiction)
        folium.Marker(
            input_coords[-1],
            icon=folium.Icon(color='blue', icon='ship', prefix='fa'),
            popup=f"Position actuelle<br>MMSI: {mmsi}"
        ).add_to(fg)
        
        # Trajectoire vérité terrain (verte)
        target_coords = data['target']
        folium.PolyLine(
            target_coords,
            color='green',
            weight=3,
            opacity=0.8,
            dash_array='5, 5',
            popup=f"Vérité - MMSI: {mmsi}"
        ).add_to(fg)
        
        for i, (lat, lon) in enumerate(target_coords):
            folium.CircleMarker(
                [lat, lon],
                radius=4,
                color='green',
                fill=True,
                fillOpacity=0.7,
                popup=f"Vérité {i+1}"
            ).add_to(fg)
        
        # Trajectoire prédite (rouge)
        pred_coords = data['prediction']
        folium.PolyLine(
            pred_coords,
            color='red',
            weight=3,
            opacity=0.8,
            dash_array='10, 5',
            popup=f"Prédiction - MMSI: {mmsi}<br>ADE: {ade:.0f}m | FDE: {fde:.0f}m"
        ).add_to(fg)
        
        for i, (lat, lon) in enumerate(pred_coords):
            folium.CircleMarker(
                [lat, lon],
                radius=4,
                color='red',
                fill=True,
                fillOpacity=0.7,
                popup=f"Prédiction {i+1}"
            ).add_to(fg)
        
        # Point final prédit
        folium.Marker(
            pred_coords[-1],
            icon=folium.Icon(color='red', icon='flag', prefix='fa'),
            popup=f"Prédiction finale<br>FDE: {fde:.0f}m"
        ).add_to(fg)
        
        # Point final vérité
        folium.Marker(
            target_coords[-1],
            icon=folium.Icon(color='green', icon='flag-checkered', prefix='fa'),
            popup=f"Position réelle finale"
        ).add_to(fg)
        
        fg.add_to(m)
    
    # Légende
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; 
                background-color: white; padding: 10px; border-radius: 5px;
                border: 2px solid grey; font-size: 14px;">
        <b>Légende</b><br>
        <i style="background: blue; width: 20px; height: 3px; display: inline-block;"></i> Trajectoire passée (entrée)<br>
        <i style="background: green; width: 20px; height: 3px; display: inline-block;"></i> Trajectoire réelle (vérité)<br>
        <i style="background: red; width: 20px; height: 3px; display: inline-block;"></i> Trajectoire prédite<br>
        <br>
        <b>🚢</b> Position actuelle<br>
        <b>🏁</b> Position finale
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Contrôle des couches
    folium.LayerControl().add_to(m)
    
    # Plugin fullscreen
    plugins.Fullscreen().add_to(m)
    
    return m


def main():
    print("=" * 60)
    print("🗺️ Visualisation des prédictions AIS sur carte")
    print("=" * 60)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"📱 Device: {device}")
    
    # Charger le modèle
    print(f"\n📦 Chargement du modèle...")
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    config = checkpoint.get('config', {})
    
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
    df = load_trajectories(n_samples=50)  # Plus de navires
    
    # Collecter les prédictions
    predictions_data = []
    
    for mmsi, group in df.groupby('MMSI'):
        group = group.reset_index(drop=True)
        
        for start_idx in range(0, len(group) - SEQ_IN - SEQ_OUT, 15):
            sample = prepare_sequence(group, start_idx)
            if sample is None:
                continue
            
            pred_coords = predict(model, sample, device)
            target_coords = sample['target_coords']
            
            # Calcul erreurs
            distances = []
            for (plat, plon), (tlat, tlon) in zip(pred_coords, target_coords):
                distances.append(haversine_distance(plat, plon, tlat, tlon))
            
            ade = np.mean(distances)
            fde = distances[-1]
            
            predictions_data.append({
                'mmsi': mmsi,
                'input': sample['input_coords'],
                'target': target_coords,
                'prediction': pred_coords,
                'ade': ade,
                'fde': fde
            })
            
            break  # Un seul par navire
        
        if len(predictions_data) >= 20:  # Afficher 20 bateaux
            break
    
    print(f"\n📍 {len(predictions_data)} trajectoires à afficher")
    
    # Créer la carte
    print("🗺️ Création de la carte...")
    m = create_map(predictions_data)
    
    # Sauvegarder
    output_path = OUTPUT_DIR / 'predictions_map.html'
    m.save(str(output_path))
    print(f"\n✅ Carte sauvegardée: {output_path}")
    
    # Stats
    print("\n📊 Statistiques:")
    ades = [d['ade'] for d in predictions_data]
    fdes = [d['fde'] for d in predictions_data]
    print(f"   ADE moyen: {np.mean(ades):.0f}m")
    print(f"   FDE moyen: {np.mean(fdes):.0f}m")
    
    print(f"\n🌐 Ouvrez le fichier dans votre navigateur:")
    print(f"   file://{output_path.absolute()}")


if __name__ == "__main__":
    main()
