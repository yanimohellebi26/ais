#!/usr/bin/env python3
"""
ETL Pipeline: Préparation des trajectoires AIS pour l'entraînement ML

Ce script transforme les données AIS brutes en segments de trajectoires
propres et réguliers, optimisés pour la prédiction de trajectoire.

Critères de qualité:
- Intervalle temporel régulier (< 10 min entre points)
- Vitesse cohérente (0.5 - 50 knots pour navigation active)
- Pas de sauts spatiaux aberrants
- Minimum 30 points par segment (pour SEQ_IN=20 + SEQ_OUT=10)
"""

import os
import sys
import math
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from tqdm import tqdm

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '172.31.60.8'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'ais'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'music861!')
}

# Paramètres de segmentation
CONFIG = {
    # Temporel
    'max_gap_seconds': 600,      # 10 min max entre 2 points
    'min_gap_seconds': 10,       # Minimum 10s (éviter doublons)
    'target_interval': 300,      # Intervalle cible: 5 min
    
    # Longueur segment
    'min_segment_length': 35,    # Min points (SEQ_IN + SEQ_OUT + marge)
    'max_segment_length': 500,   # Max points par segment
    
    # Vitesse (knots)
    'min_sog_active': 0.5,       # En dessous = à l'arrêt
    'max_sog_realistic': 50,     # Au dessus = erreur
    
    # Spatial
    'max_speed_jump_factor': 3,  # Vitesse implicite max = 3x SOG reporté
    
    # Qualité
    'min_quality_score': 0.5,    # Score minimum pour training
    
    # Processing
    'batch_size': 1000,          # Navires par batch
    'min_vessel_points': 50,     # Min points pour traiter un navire
}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance en mètres entre deux points GPS."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))


def calculate_implicit_speed(lat1: float, lon1: float, lat2: float, lon2: float, 
                             delta_t: float) -> float:
    """Vitesse implicite en knots basée sur le déplacement."""
    if delta_t <= 0:
        return 0.0
    distance_m = haversine_distance(lat1, lon1, lat2, lon2)
    speed_ms = distance_m / delta_t
    return speed_ms * 1.94384  # m/s -> knots


def normalize_angle(angle: float) -> float:
    """Normalise un angle entre 0 et 360."""
    return angle % 360


def angle_difference(a1: float, a2: float) -> float:
    """Différence d'angle signée (-180, 180)."""
    diff = (a2 - a1 + 180) % 360 - 180
    return diff


def calculate_quality_score(delta_ts: np.ndarray, target_interval: float = 300) -> float:
    """
    Score de qualité basé sur la régularité temporelle.
    1.0 = parfait (tous les intervalles = target)
    0.0 = très irrégulier
    """
    if len(delta_ts) < 2:
        return 0.0
    
    # Écart-type relatif par rapport à l'intervalle cible
    mean_dt = np.mean(delta_ts[delta_ts > 0])
    std_dt = np.std(delta_ts[delta_ts > 0])
    
    if mean_dt == 0:
        return 0.0
    
    # Coefficient de variation (plus bas = plus régulier)
    cv = std_dt / mean_dt
    
    # Pénalité si moyenne loin de la cible
    mean_penalty = abs(mean_dt - target_interval) / target_interval
    mean_penalty = min(mean_penalty, 1.0)
    
    # Score combiné
    regularity_score = 1.0 / (1.0 + cv)
    target_score = 1.0 - mean_penalty * 0.5
    
    return regularity_score * target_score

class TrajectoryPreprocessor:
    """Préprocesseur de trajectoires AIS."""
    
    def __init__(self, config: dict = None):
        self.config = config or CONFIG
        self.conn = None
        self.stats = {
            'vessels_processed': 0,
            'segments_created': 0,
            'points_created': 0,
            'segments_rejected': 0,
            'reasons': {}
        }
    
    def connect(self):
        """Connexion à la base de données."""
        self.conn = psycopg2.connect(**DB_CONFIG)
        logger.info(f"Connecté à {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    def close(self):
        """Fermeture connexion."""
        if self.conn:
            self.conn.close()
    
    def get_vessels_to_process(self) -> List[Tuple[int, int]]:
        """Récupère la liste des navires avec assez de points."""
        query = """
            SELECT v.id, COUNT(pv.id) as num_points
            FROM vessel v
            JOIN position_vessel pv ON pv.vessel_id = v.id
            GROUP BY v.id
            HAVING COUNT(pv.id) >= %s
            ORDER BY COUNT(pv.id) DESC
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (self.config['min_vessel_points'],))
            return cur.fetchall()
    
    def get_vessel_positions(self, vessel_id: int) -> pd.DataFrame:
        """Récupère les positions d'un navire."""
        query = """
            SELECT 
                pv.id,
                pv.base_date_time,
                ST_Y(pv.geom::geometry) as lat,
                ST_X(pv.geom::geometry) as lon,
                pv.sog,
                pv.cog,
                pv.heading,
                v.vessel_type_id,
                v.length,
                v.width
            FROM position_vessel pv
            JOIN vessel v ON v.id = pv.vessel_id
            WHERE pv.vessel_id = %s
            ORDER BY pv.base_date_time
        """
        return pd.read_sql(query, self.conn, params=(vessel_id,))
    
    def clean_positions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoie les positions aberrantes."""
        original_len = len(df)
        
        # Supprimer les NaN
        df = df.dropna(subset=['lat', 'lon', 'sog', 'cog'])
        
        # Coordonnées valides
        df = df[df['lat'].between(-90, 90) & df['lon'].between(-180, 180)]
        
        # SOG réaliste
        df = df[df['sog'].between(0, self.config['max_sog_realistic'])]
        
        # COG valide
        df = df[df['cog'].between(0, 360)]
        
        # Heading (peut être NULL, remplacer par COG)
        df['heading'] = df['heading'].fillna(df['cog'])
        df.loc[~df['heading'].between(0, 360), 'heading'] = df['cog']
        
        # Trier par temps
        df = df.sort_values('base_date_time').reset_index(drop=True)
        
        # Supprimer doublons temporels
        df = df.drop_duplicates(subset=['base_date_time'], keep='first')
        
        logger.debug(f"Nettoyage: {original_len} -> {len(df)} positions")
        return df
    
    def segment_trajectory(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """
        Découpe une trajectoire en segments valides.
        Un nouveau segment commence quand:
        - Gap temporel > max_gap_seconds
        - Saut spatial incohérent avec la vitesse
        - Navire à l'arrêt prolongé
        """
        if len(df) < self.config['min_segment_length']:
            return []
        
        segments = []
        current_segment = []
        
        for i, row in df.iterrows():
            if not current_segment:
                # Premier point
                current_segment.append(row)
                continue
            
            prev = current_segment[-1]
            
            # Calculer delta_t
            delta_t = (row['base_date_time'] - prev['base_date_time']).total_seconds()
            
            # Vérifier si on doit couper
            should_cut = False
            reason = None
            
            # Gap temporel trop grand
            if delta_t > self.config['max_gap_seconds']:
                should_cut = True
                reason = 'gap_temporel'
            
            # Gap trop petit (doublon)
            elif delta_t < self.config['min_gap_seconds']:
                continue  # Skip ce point
            
            # Vérifier cohérence spatiale
            else:
                implicit_speed = calculate_implicit_speed(
                    prev['lat'], prev['lon'], row['lat'], row['lon'], delta_t
                )
                reported_speed = max(prev['sog'], row['sog'], 0.1)
                
                if implicit_speed > reported_speed * self.config['max_speed_jump_factor']:
                    should_cut = True
                    reason = 'saut_spatial'
            
            if should_cut:
                # Sauvegarder segment actuel si assez long
                if len(current_segment) >= self.config['min_segment_length']:
                    segments.append(pd.DataFrame(current_segment))
                current_segment = [row]
            else:
                current_segment.append(row)
                
                # Vérifier longueur max
                if len(current_segment) >= self.config['max_segment_length']:
                    segments.append(pd.DataFrame(current_segment))
                    current_segment = [row]  # Overlap d'un point
        
        # Dernier segment
        if len(current_segment) >= self.config['min_segment_length']:
            segments.append(pd.DataFrame(current_segment))
        
        return segments
    
    def filter_active_navigation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtre pour garder uniquement la navigation active."""
        # Moyenne mobile de SOG
        df = df.copy()
        df['sog_ma'] = df['sog'].rolling(window=5, center=True, min_periods=1).mean()
        
        # Garder si vitesse moyenne > seuil
        df = df[df['sog_ma'] >= self.config['min_sog_active']]
        
        return df.drop(columns=['sog_ma'])
    
    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les features dérivées pour chaque point."""
        df = df.copy().reset_index(drop=True)
        
        # Delta_t
        df['delta_t'] = df['base_date_time'].diff().dt.total_seconds().fillna(0)
        
        # Accélération (changement de SOG)
        df['acceleration'] = df['sog'].diff().fillna(0)
        df.loc[df['delta_t'] > 0, 'acceleration'] /= df.loc[df['delta_t'] > 0, 'delta_t']
        df['acceleration'] = df['acceleration'].clip(-0.5, 0.5)  # Limiter
        
        # Taux de virage
        df['cog_diff'] = df['cog'].diff().fillna(0)
        df['cog_diff'] = df['cog_diff'].apply(lambda x: (x + 180) % 360 - 180)
        df['turn_rate'] = 0.0
        mask = df['delta_t'] > 0
        df.loc[mask, 'turn_rate'] = df.loc[mask, 'cog_diff'] / df.loc[mask, 'delta_t']
        df['turn_rate'] = df['turn_rate'].clip(-5, 5)  # deg/s max
        
        return df.drop(columns=['cog_diff'])
    
    def save_segment(self, df: pd.DataFrame, vessel_id: int, segment_num: int) -> Optional[int]:
        """Sauvegarde un segment en base."""
        if len(df) < self.config['min_segment_length']:
            return None
        
        # Calculer métadonnées
        start_time = df['base_date_time'].iloc[0]
        end_time = df['base_date_time'].iloc[-1]
        duration = (end_time - start_time).total_seconds()
        
        delta_ts = df['delta_t'].values
        quality = calculate_quality_score(delta_ts, self.config['target_interval'])
        
        # Distance totale
        total_dist = 0
        for i in range(1, len(df)):
            total_dist += haversine_distance(
                df['lat'].iloc[i-1], df['lon'].iloc[i-1],
                df['lat'].iloc[i], df['lon'].iloc[i]
            )
        
        # Vérifier qualité minimum
        is_valid = quality >= self.config['min_quality_score']
        
        with self.conn.cursor() as cur:
            # Insérer segment
            cur.execute("""
                INSERT INTO trajectory_segment (
                    vessel_id, segment_id, start_time, end_time, duration_seconds,
                    num_points, vessel_type_id, vessel_length, vessel_width,
                    avg_sog, max_sog, min_sog, avg_delta_t, max_delta_t,
                    total_distance_meters, min_lat, max_lat, min_lon, max_lon,
                    quality_score, is_valid_for_training
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                vessel_id, segment_num, start_time, end_time, int(duration),
                len(df), df['vessel_type_id'].iloc[0], df['length'].iloc[0], df['width'].iloc[0],
                float(df['sog'].mean()), float(df['sog'].max()), float(df['sog'].min()),
                float(delta_ts[delta_ts > 0].mean()) if (delta_ts > 0).any() else 0,
                float(delta_ts.max()),
                total_dist,
                float(df['lat'].min()), float(df['lat'].max()),
                float(df['lon'].min()), float(df['lon'].max()),
                quality, is_valid
            ))
            segment_id = cur.fetchone()[0]
            
            # Insérer points
            points_data = []
            for idx, row in df.iterrows():
                points_data.append((
                    segment_id,
                    len(points_data),  # point_index
                    row['lat'], row['lon'],
                    row['sog'], row['cog'], row['heading'],
                    row['base_date_time'],
                    row['delta_t'],
                    row['acceleration'],
                    row['turn_rate']
                ))
            
            execute_values(cur, """
                INSERT INTO trajectory_point (
                    segment_id, point_index, lat, lon, sog, cog, heading,
                    timestamp, delta_t, acceleration, turn_rate
                ) VALUES %s
            """, points_data)
            
            self.conn.commit()
            return segment_id
    
    def process_vessel(self, vessel_id: int) -> int:
        """Traite un navire complet."""
        df = self.get_vessel_positions(vessel_id)
        if df.empty:
            return 0
        
        # Pipeline de traitement
        df = self.clean_positions(df)
        segments = self.segment_trajectory(df)
        
        segments_created = 0
        for i, seg_df in enumerate(segments):
            # Filtrer navigation active
            seg_df = self.filter_active_navigation(seg_df)
            if len(seg_df) < self.config['min_segment_length']:
                continue
            
            # Calculer features
            seg_df = self.compute_features(seg_df)
            
            # Sauvegarder
            segment_id = self.save_segment(seg_df, vessel_id, i)
            if segment_id:
                segments_created += 1
                self.stats['points_created'] += len(seg_df)
        
        return segments_created
    
    def run(self, limit: int = None):
        """Exécute le pipeline complet."""
        self.connect()
        
        try:
            # Vérifier/créer tables
            logger.info("Vérification des tables...")
            
            # Récupérer navires
            vessels = self.get_vessels_to_process()
            if limit:
                vessels = vessels[:limit]
            
            logger.info(f" {len(vessels)} navires à traiter")
            
            # Traitement par batch
            for vessel_id, num_points in tqdm(vessels, desc="Navires"):
                try:
                    segments = self.process_vessel(vessel_id)
                    self.stats['vessels_processed'] += 1
                    self.stats['segments_created'] += segments
                except Exception as e:
                    logger.error(f"Erreur vessel {vessel_id}: {e}")
                    self.conn.rollback()
            
            # Rafraîchir vue matérialisée
            logger.info("Rafraîchissement des statistiques...")
            with self.conn.cursor() as cur:
                cur.execute("REFRESH MATERIALIZED VIEW trajectory_stats")
            self.conn.commit()
            
            # Afficher stats
            self._print_stats()
            
        finally:
            self.close()
    
    def _print_stats(self):
        """Affiche les statistiques."""
        logger.info("=" * 60)
        logger.info(" STATISTIQUES DE TRAITEMENT")
        logger.info("=" * 60)
        logger.info(f"Navires traités: {self.stats['vessels_processed']}")
        logger.info(f"Segments créés: {self.stats['segments_created']}")
        logger.info(f"Points créés: {self.stats['points_created']}")
        if self.stats['vessels_processed'] > 0:
            avg_seg = self.stats['segments_created'] / self.stats['vessels_processed']
            logger.info(f"Moyenne segments/navire: {avg_seg:.1f}")
        if self.stats['segments_created'] > 0:
            avg_pts = self.stats['points_created'] / self.stats['segments_created']
            logger.info(f"Moyenne points/segment: {avg_pts:.1f}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Préparation trajectoires AIS pour ML")
    parser.add_argument('--limit', type=int, help="Limite de navires à traiter")
    parser.add_argument('--max-gap', type=int, default=600, help="Gap max en secondes (défaut: 600)")
    parser.add_argument('--min-points', type=int, default=35, help="Min points par segment (défaut: 35)")
    parser.add_argument('--min-quality', type=float, default=0.5, help="Score qualité min (défaut: 0.5)")
    args = parser.parse_args()
    
    # Mettre à jour config
    CONFIG['max_gap_seconds'] = args.max_gap
    CONFIG['min_segment_length'] = args.min_points
    CONFIG['min_quality_score'] = args.min_quality
    
    preprocessor = TrajectoryPreprocessor(CONFIG)
    preprocessor.run(limit=args.limit)
