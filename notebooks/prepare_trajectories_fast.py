#!/usr/bin/env python3
"""
Préparation des trajectoires - VERSION OPTIMISÉE (10-100x plus rapide)

Charge toutes les données en une seule requête puis traite en mémoire.
"""

import argparse
import logging
import math
import sys
from typing import List, Optional, Tuple
from datetime import datetime

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from tqdm import tqdm

# ==========================================
# CONFIGURATION
# ==========================================
DB_CONFIG = {
    'host': '172.31.60.8',
    'port': 5432,
    'database': 'ais',
    'user': 'postgres',
    'password': 'ANjw/84H77C9h2'
}

DEFAULT_CONFIG = {
    'gap_min': 5,           # Gap min entre points (sec)
    'gap_max': 600,         # Gap max (10 min) - au-delà = nouveau segment
    'sog_min': 0.5,         # Vitesse min (noeuds)
    'sog_max': 50.0,        # Vitesse max
    'min_segment_points': 35,  # SEQ_IN(20) + SEQ_OUT(10) + marge
    'target_interval': 60,  # Intervalle cible (sec)
    'min_quality': 0.3,     # Score qualité min
    'min_vessel_points': 50 # Points min par navire
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================
def haversine(lat1, lon1, lat2, lon2):
    """Distance en mètres."""
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))


def quality_score(delta_ts: np.ndarray, target: float = 60) -> float:
    """Score de qualité basé sur régularité des intervalles."""
    if len(delta_ts) == 0:
        return 0.0
    valid = delta_ts[delta_ts > 0]
    if len(valid) == 0:
        return 0.0
    deviation = np.abs(valid - target) / target
    return float(np.clip(1 - np.mean(deviation), 0, 1))


# ==========================================
# CLASSE PRINCIPALE
# ==========================================
class FastTrajectoryETL:
    def __init__(self, config: dict = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.conn = None
        self.stats = {'segments': 0, 'points': 0, 'vessels': 0, 'skipped': 0}
    
    def connect(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        logger.info(f"✅ Connecté à {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def clear_tables(self):
        """Vide les tables."""
        with self.conn.cursor() as cur:
            cur.execute("TRUNCATE trajectory_point, trajectory_segment RESTART IDENTITY CASCADE")
            self.conn.commit()
        logger.info("🗑️ Tables vidées")
    
    def load_all_data(self, limit: int = None) -> pd.DataFrame:
        """Charge TOUTES les données en une requête."""
        logger.info("📥 Chargement des données (une seule requête)...")
        
        # Requête optimisée avec filtre
        query = """
            WITH vessel_counts AS (
                SELECT vessel_id, COUNT(*) as cnt
                FROM position_vessel
                WHERE sog IS NOT NULL AND cog IS NOT NULL
                GROUP BY vessel_id
                HAVING COUNT(*) >= %(min_points)s
                ORDER BY cnt DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        query += """
            )
            SELECT 
                pv.vessel_id,
                pv.base_date_time as ts,
                ST_Y(pv.geom::geometry) as lat,
                ST_X(pv.geom::geometry) as lon,
                pv.sog, pv.cog,
                COALESCE(pv.heading, pv.cog) as heading,
                v.vessel_type_id
            FROM position_vessel pv
            JOIN vessel v ON v.id = pv.vessel_id
            JOIN vessel_counts vc ON vc.vessel_id = pv.vessel_id
            WHERE pv.sog IS NOT NULL 
              AND pv.cog IS NOT NULL
              AND pv.sog >= %(sog_min)s
              AND pv.sog <= %(sog_max)s
            ORDER BY pv.vessel_id, pv.base_date_time
        """
        
        params = {
            'min_points': self.config['min_vessel_points'],
            'sog_min': self.config['sog_min'],
            'sog_max': self.config['sog_max']
        }
        
        start = datetime.now()
        df = pd.read_sql(query, self.conn, params=params)
        elapsed = (datetime.now() - start).total_seconds()
        
        n_vessels = df['vessel_id'].nunique()
        logger.info(f"✅ {len(df):,} positions pour {n_vessels:,} navires en {elapsed:.1f}s")
        
        return df
    
    def process_vessel_data(self, df: pd.DataFrame) -> List[Tuple[dict, pd.DataFrame]]:
        """Traite les données d'un navire."""
        segments = []
        
        # Nettoyage
        df = df.dropna(subset=['lat', 'lon', 'sog', 'cog'])
        df = df[df['lat'].between(-90, 90) & df['lon'].between(-180, 180)]
        df = df[df['cog'].between(0, 360)]
        df['heading'] = df['heading'].fillna(df['cog']).clip(0, 360)
        df = df.sort_values('ts').drop_duplicates('ts', keep='first').reset_index(drop=True)
        
        if len(df) < self.config['min_segment_points']:
            return []
        
        # Calcul delta_t
        df['delta_t'] = df['ts'].diff().dt.total_seconds().fillna(0)
        
        # Accélération et taux de virage
        dt_safe = df['delta_t'].replace(0, 1.0)
        df['accel'] = (df['sog'].diff().fillna(0) / dt_safe).clip(-0.5, 0.5)
        
        cog_diff = df['cog'].diff().fillna(0)
        cog_diff = (cog_diff + 180) % 360 - 180
        df['turn_rate'] = (cog_diff / dt_safe).clip(-3, 3)
        
        # Segmentation par gaps
        df['gap'] = (df['delta_t'] > self.config['gap_max']) | (df['delta_t'] < self.config['gap_min'])
        df['segment_id'] = df['gap'].cumsum()
        
        # Traiter chaque segment
        for seg_idx, seg_df in df.groupby('segment_id'):
            if len(seg_df) < self.config['min_segment_points']:
                continue
            
            seg_df = seg_df.reset_index(drop=True)
            delta_ts = seg_df['delta_t'].values
            q_score = quality_score(delta_ts, self.config['target_interval'])
            
            if q_score < self.config['min_quality']:
                continue
            
            # Métadonnées segment
            start_time = seg_df['ts'].iloc[0]
            end_time = seg_df['ts'].iloc[-1]
            duration = (end_time - start_time).total_seconds()
            
            # Distance totale
            total_dist = 0
            for i in range(1, len(seg_df)):
                total_dist += haversine(
                    seg_df['lat'].iloc[i-1], seg_df['lon'].iloc[i-1],
                    seg_df['lat'].iloc[i], seg_df['lon'].iloc[i]
                )
            
            vtype_id = seg_df['vessel_type_id'].iloc[0]
            if pd.notna(vtype_id):
                vtype_id = int(vtype_id)
            else:
                vtype_id = None
            
            meta = {
                'vessel_id': int(seg_df['vessel_id'].iloc[0]),
                'segment_idx': int(seg_idx),
                'start_time': start_time,
                'end_time': end_time,
                'duration_seconds': int(duration),
                'num_points': int(len(seg_df)),
                'vessel_type_id': vtype_id,
                'avg_sog': float(seg_df['sog'].mean()),
                'max_sog': float(seg_df['sog'].max()),
                'avg_delta_t': float(delta_ts[delta_ts > 0].mean()) if (delta_ts > 0).any() else 0.0,
                'max_delta_t': float(delta_ts.max()),
                'total_distance_m': float(total_dist),
                'min_lat': float(seg_df['lat'].min()),
                'max_lat': float(seg_df['lat'].max()),
                'min_lon': float(seg_df['lon'].min()),
                'max_lon': float(seg_df['lon'].max()),
                'quality_score': float(q_score)
            }
            
            segments.append((meta, seg_df))
        
        return segments
    
    def save_segments_batch(self, all_segments: List[Tuple[dict, pd.DataFrame]]):
        """Sauvegarde tous les segments en batch."""
        if not all_segments:
            return
        
        logger.info(f"💾 Sauvegarde de {len(all_segments)} segments...")
        
        with self.conn.cursor() as cur:
            # Préparer les données segments
            segment_data = []
            for meta, _ in all_segments:
                segment_data.append((
                    meta['vessel_id'], meta['segment_idx'], meta['start_time'], meta['end_time'],
                    meta['duration_seconds'], meta['num_points'], meta['vessel_type_id'],
                    meta['avg_sog'], meta['max_sog'], meta['avg_delta_t'], meta['max_delta_t'],
                    meta['total_distance_m'], meta['min_lat'], meta['max_lat'],
                    meta['min_lon'], meta['max_lon'], meta['quality_score'], True
                ))
            
            # Insert segments et récupérer IDs
            segment_ids = []
            for data in segment_data:
                cur.execute("""
                    INSERT INTO trajectory_segment (
                        vessel_id, segment_idx, start_time, end_time, duration_seconds,
                        num_points, vessel_type_id, avg_sog, max_sog, avg_delta_t, max_delta_t,
                        total_distance_m, min_lat, max_lat, min_lon, max_lon,
                        quality_score, is_valid
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                """, data)
                segment_ids.append(cur.fetchone()[0])
            
            # Préparer points (batch)
            all_points = []
            for (seg_id, (_, seg_df)) in zip(segment_ids, all_segments):
                for point_idx, row in seg_df.iterrows():
                    heading = float(row['heading']) if pd.notna(row['heading']) else None
                    all_points.append((
                        int(seg_id), int(point_idx),
                        float(row['lat']), float(row['lon']),
                        float(row['sog']), float(row['cog']), heading,
                        row['ts'], float(row['delta_t']),
                        float(row['accel']), float(row['turn_rate'])
                    ))
            
            # Insert points en batch
            execute_values(cur, """
                INSERT INTO trajectory_point (
                    segment_id, point_idx, lat, lon, sog, cog, heading,
                    ts, delta_t, accel, turn_rate
                ) VALUES %s
            """, all_points, page_size=5000)
            
            self.conn.commit()
            
            self.stats['segments'] += len(all_segments)
            self.stats['points'] += len(all_points)
    
    def run(self, limit: int = None, clear: bool = False):
        """Exécute l'ETL complet."""
        self.connect()
        
        try:
            if clear:
                self.clear_tables()
            
            # Charger toutes les données
            df = self.load_all_data(limit)
            
            if df.empty:
                logger.warning("⚠️ Aucune donnée trouvée!")
                return
            
            # Grouper par navire et traiter
            vessel_groups = df.groupby('vessel_id')
            n_vessels = len(vessel_groups)
            logger.info(f"📊 Traitement de {n_vessels} navires...")
            
            all_segments = []
            batch_size = 100  # Sauvegarder par batch de 100 segments
            
            for vessel_id, vessel_df in tqdm(vessel_groups, desc="Navires", total=n_vessels):
                segments = self.process_vessel_data(vessel_df.copy())
                
                if segments:
                    all_segments.extend(segments)
                    self.stats['vessels'] += 1
                else:
                    self.stats['skipped'] += 1
                
                # Sauvegarder par batch pour éviter trop de mémoire
                if len(all_segments) >= batch_size:
                    self.save_segments_batch(all_segments)
                    all_segments = []
            
            # Sauvegarder le reste
            if all_segments:
                self.save_segments_batch(all_segments)
            
            # Stats finales
            self._print_stats()
            self._update_overview()
            
        finally:
            self.close()
    
    def _print_stats(self):
        logger.info("=" * 50)
        logger.info("📊 RÉSULTATS")
        logger.info(f"   Navires traités: {self.stats['vessels']}")
        logger.info(f"   Segments créés: {self.stats['segments']}")
        logger.info(f"   Points totaux: {self.stats['points']}")
        logger.info(f"   Navires ignorés: {self.stats['skipped']}")
        
        if self.stats['segments'] > 0:
            avg_pts = self.stats['points'] / self.stats['segments']
            logger.info(f"   Points/segment: {avg_pts:.1f}")
    
    def _update_overview(self):
        """Met à jour la table overview par type de navire."""
        with self.conn.cursor() as cur:
            # Vider et repeupler
            cur.execute("TRUNCATE trajectory_overview")
            cur.execute("""
                INSERT INTO trajectory_overview (
                    vessel_type_id, num_segments, total_points,
                    avg_points, avg_sog, avg_interval_s, avg_quality
                )
                SELECT 
                    COALESCE(vessel_type_id, 0),
                    COUNT(*),
                    SUM(num_points),
                    AVG(num_points),
                    AVG(avg_sog),
                    AVG(avg_delta_t),
                    AVG(quality_score)
                FROM trajectory_segment
                WHERE is_valid = true
                GROUP BY COALESCE(vessel_type_id, 0)
            """)
            self.conn.commit()
        logger.info("✅ Overview mis à jour")


# ==========================================
# MAIN
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="Préparation trajectoires ML (FAST)")
    parser.add_argument('--limit', type=int, help="Limite navires")
    parser.add_argument('--clear', action='store_true', help="Vider tables avant")
    args = parser.parse_args()
    
    etl = FastTrajectoryETL()
    etl.run(limit=args.limit, clear=args.clear)


if __name__ == "__main__":
    main()
