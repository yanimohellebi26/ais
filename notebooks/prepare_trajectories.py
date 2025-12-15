#!/usr/bin/env python3
"""
ETL: Préparation des trajectoires AIS pour ML
Stockage dans PostgreSQL (tables trajectory_segment / trajectory_point)

Usage:
    python prepare_trajectories.py [--limit N] [--min-quality 0.5]
"""

import os
import sys
import math
import logging
import argparse
from datetime import datetime
from typing import List, Tuple, Optional
import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from tqdm import tqdm

# ============================================================
# CONFIGURATION
# ============================================================

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '172.31.60.8'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'ais'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'ANjw/84H77C9h2')
}

# Paramètres de segmentation
CONFIG = {
    'max_gap_seconds': 600,      # 10 min max entre points
    'min_gap_seconds': 10,       # Min 10s (éviter doublons)
    'target_interval': 300,      # Cible: 5 min
    
    'min_segment_points': 35,    # Min points (SEQ_IN=20 + SEQ_OUT=10 + marge)
    'max_segment_points': 500,   # Max par segment
    
    'min_sog': 0.5,              # En dessous = arrêt
    'max_sog': 50,               # Au dessus = erreur
    
    'min_quality': 0.3,          # Score min pour garder
    'min_vessel_points': 50,     # Min points pour traiter navire
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================
# UTILITAIRES
# ============================================================

def haversine(lat1, lon1, lat2, lon2):
    """Distance en mètres."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))


def quality_score(delta_ts: np.ndarray, target: float = 300) -> float:
    """Score 0-1 basé sur régularité temporelle."""
    if len(delta_ts) < 2:
        return 0.0
    valid = delta_ts[delta_ts > 0]
    if len(valid) == 0:
        return 0.0
    
    mean_dt = np.mean(valid)
    std_dt = np.std(valid)
    
    cv = std_dt / mean_dt if mean_dt > 0 else 1.0
    regularity = 1.0 / (1.0 + cv)
    
    target_penalty = min(abs(mean_dt - target) / target, 1.0)
    
    return regularity * (1.0 - 0.5 * target_penalty)


# ============================================================
# PRÉPROCESSEUR
# ============================================================

class TrajectoryPreprocessor:
    def __init__(self, config=None):
        self.config = config or CONFIG
        self.conn = None
        self.stats = {'vessels': 0, 'segments': 0, 'points': 0, 'skipped': 0}
    
    def connect(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        logger.info(f"✅ Connecté à {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def check_tables(self):
        """Vérifie que les tables existent."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'trajectory_segment'
                )
            """)
            exists = cur.fetchone()[0]
            
            if not exists:
                logger.error("❌ Tables trajectory_* non trouvées!")
                logger.error("   Exécutez d'abord: V10__create_trajectory_ml_tables.sql")
                return False
            return True
    
    def clear_tables(self):
        """Vide les tables (pour re-processing)."""
        with self.conn.cursor() as cur:
            cur.execute("TRUNCATE trajectory_point, trajectory_segment RESTART IDENTITY CASCADE")
        self.conn.commit()
        logger.info("🗑️ Tables vidées")
    
    def get_vessels(self, limit: int = None) -> List[Tuple[int, int]]:
        """Liste des navires avec assez de points."""
        query = """
            SELECT v.id, COUNT(pv.id) as n
            FROM vessel v
            JOIN position_vessel pv ON pv.vessel_id = v.id
            GROUP BY v.id
            HAVING COUNT(pv.id) >= %s
            ORDER BY COUNT(pv.id) DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        with self.conn.cursor() as cur:
            cur.execute(query, (self.config['min_vessel_points'],))
            return cur.fetchall()
    
    def get_positions(self, vessel_id: int) -> pd.DataFrame:
        """Récupère positions d'un navire."""
        query = """
            SELECT 
                pv.base_date_time as ts,
                ST_Y(pv.geom::geometry) as lat,
                ST_X(pv.geom::geometry) as lon,
                pv.sog, pv.cog,
                COALESCE(pv.heading, pv.cog) as heading,
                v.vessel_type_id
            FROM position_vessel pv
            JOIN vessel v ON v.id = pv.vessel_id
            WHERE pv.vessel_id = %s
              AND pv.sog IS NOT NULL
              AND pv.cog IS NOT NULL
            ORDER BY pv.base_date_time
        """
        return pd.read_sql(query, self.conn, params=(vessel_id,))
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoie les données."""
        df = df.dropna(subset=['lat', 'lon', 'sog', 'cog'])
        df = df[df['lat'].between(-90, 90) & df['lon'].between(-180, 180)]
        df = df[df['sog'].between(0, self.config['max_sog'])]
        df = df[df['cog'].between(0, 360)]
        df['heading'] = df['heading'].clip(0, 360)
        df = df.sort_values('ts').drop_duplicates('ts', keep='first')
        return df.reset_index(drop=True)
    
    def segment_trajectory(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """Découpe en segments valides."""
        if len(df) < self.config['min_segment_points']:
            return []
        
        segments = []
        current = []
        
        for i, row in df.iterrows():
            if not current:
                current.append(row)
                continue
            
            prev = current[-1]
            delta_t = (row['ts'] - prev['ts']).total_seconds()
            
            # Couper si gap trop grand
            if delta_t > self.config['max_gap_seconds']:
                if len(current) >= self.config['min_segment_points']:
                    segments.append(pd.DataFrame(current))
                current = [row]
            elif delta_t < self.config['min_gap_seconds']:
                continue  # Skip doublon
            else:
                current.append(row)
                if len(current) >= self.config['max_segment_points']:
                    segments.append(pd.DataFrame(current))
                    current = [row]
        
        if len(current) >= self.config['min_segment_points']:
            segments.append(pd.DataFrame(current))
        
        return segments
    
    def filter_active(self, df: pd.DataFrame) -> pd.DataFrame:
        """Garde navigation active."""
        df = df.copy()
        df['sog_ma'] = df['sog'].rolling(5, center=True, min_periods=1).mean()
        df = df[df['sog_ma'] >= self.config['min_sog']]
        return df.drop(columns=['sog_ma']).reset_index(drop=True)
    
    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule features dérivées."""
        df = df.copy()
        
        df['delta_t'] = df['ts'].diff().dt.total_seconds().fillna(0)
        
        # Accélération
        dt_safe = df['delta_t'].replace(0, 1.0)
        df['accel'] = (df['sog'].diff().fillna(0) / dt_safe).clip(-0.5, 0.5)
        
        # Taux de virage
        cog_diff = df['cog'].diff().fillna(0)
        cog_diff = (cog_diff + 180) % 360 - 180
        df['turn_rate'] = (cog_diff / dt_safe).clip(-5, 5)
        
        return df
    
    def save_segment(self, df: pd.DataFrame, vessel_id: int, seg_idx: int) -> Optional[int]:
        """Sauvegarde un segment."""
        if len(df) < self.config['min_segment_points']:
            return None
        
        # Métadonnées
        start_time = df['ts'].iloc[0]
        end_time = df['ts'].iloc[-1]
        duration = (end_time - start_time).total_seconds()
        
        delta_ts = df['delta_t'].values
        q_score = quality_score(delta_ts, self.config['target_interval'])
        
        if q_score < self.config['min_quality']:
            return None
        
        # Distance totale
        total_dist = 0
        for i in range(1, len(df)):
            total_dist += haversine(
                df['lat'].iloc[i-1], df['lon'].iloc[i-1],
                df['lat'].iloc[i], df['lon'].iloc[i]
            )
        
        # Convertir vessel_type_id en int Python natif
        vtype_id = df['vessel_type_id'].iloc[0]
        if pd.notna(vtype_id):
            vtype_id = int(vtype_id)
        else:
            vtype_id = None
        
        with self.conn.cursor() as cur:
            # Insert segment
            cur.execute("""
                INSERT INTO trajectory_segment (
                    vessel_id, segment_idx, start_time, end_time, duration_seconds,
                    num_points, vessel_type_id, avg_sog, max_sog, avg_delta_t, max_delta_t,
                    total_distance_m, min_lat, max_lat, min_lon, max_lon,
                    quality_score, is_valid
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
            """, (
                int(vessel_id), int(seg_idx), start_time, end_time, int(duration),
                int(len(df)), vtype_id,
                float(df['sog'].mean()), float(df['sog'].max()),
                float(delta_ts[delta_ts > 0].mean()) if (delta_ts > 0).any() else 0.0,
                float(delta_ts.max()),
                float(total_dist),
                float(df['lat'].min()), float(df['lat'].max()),
                float(df['lon'].min()), float(df['lon'].max()),
                float(q_score), True
            ))
            segment_id = cur.fetchone()[0]
            
            # Insert points
            points = []
            for idx, row in df.iterrows():
                points.append((
                    int(segment_id), len(points),
                    float(row['lat']), float(row['lon']), 
                    float(row['sog']), float(row['cog']), 
                    float(row['heading']) if pd.notna(row['heading']) else None,
                    row['ts'], float(row['delta_t']), 
                    float(row['accel']), float(row['turn_rate'])
                ))
            
            execute_values(cur, """
                INSERT INTO trajectory_point (
                    segment_id, point_idx, lat, lon, sog, cog, heading,
                    ts, delta_t, accel, turn_rate
                ) VALUES %s
            """, points)
            
            self.conn.commit()
            return segment_id
    
    def process_vessel(self, vessel_id: int) -> int:
        """Traite un navire."""
        df = self.get_positions(vessel_id)
        if df.empty:
            return 0
        
        df = self.clean_data(df)
        segments = self.segment_trajectory(df)
        
        created = 0
        for i, seg_df in enumerate(segments):
            seg_df = self.filter_active(seg_df)
            if len(seg_df) < self.config['min_segment_points']:
                continue
            
            seg_df = self.compute_features(seg_df)
            if self.save_segment(seg_df, vessel_id, i):
                created += 1
                self.stats['points'] += len(seg_df)
        
        return created
    
    def run(self, limit: int = None, clear: bool = False):
        """Pipeline complet."""
        self.connect()
        
        if not self.check_tables():
            return
        
        if clear:
            self.clear_tables()
        
        vessels = self.get_vessels(limit)
        logger.info(f"📊 {len(vessels)} navires à traiter")
        
        for vessel_id, n_pts in tqdm(vessels, desc="Navires"):
            try:
                n_seg = self.process_vessel(vessel_id)
                self.stats['vessels'] += 1
                self.stats['segments'] += n_seg
            except Exception as e:
                logger.warning(f"Erreur vessel {vessel_id}: {e}")
                self.conn.rollback()
                self.stats['skipped'] += 1
        
        self._print_stats()
        self.close()
    
    def _print_stats(self):
        logger.info("=" * 50)
        logger.info("📊 RÉSULTATS")
        logger.info("=" * 50)
        logger.info(f"Navires traités: {self.stats['vessels']}")
        logger.info(f"Segments créés: {self.stats['segments']}")
        logger.info(f"Points totaux: {self.stats['points']:,}")
        logger.info(f"Navires ignorés: {self.stats['skipped']}")
        
        if self.stats['segments'] > 0:
            avg = self.stats['points'] / self.stats['segments']
            logger.info(f"Points/segment: {avg:.1f}")
            
            # Estimation échantillons ML (stride=5, window=30)
            estimated = self.stats['points'] // 5
            logger.info(f"📦 Échantillons ML estimés: ~{estimated:,}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prépare trajectoires AIS pour ML")
    parser.add_argument('--limit', type=int, help="Limite de navires")
    parser.add_argument('--clear', action='store_true', help="Vider tables avant")
    parser.add_argument('--min-quality', type=float, default=0.3)
    parser.add_argument('--max-gap', type=int, default=600)
    args = parser.parse_args()
    
    CONFIG['min_quality'] = args.min_quality
    CONFIG['max_gap_seconds'] = args.max_gap
    
    preprocessor = TrajectoryPreprocessor(CONFIG)
    preprocessor.run(limit=args.limit, clear=args.clear)
