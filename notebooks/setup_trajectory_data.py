#!/usr/bin/env python3
"""
Script de setup pour préparer la base de données pour l'entraînement ML.

Étapes:
1. Appliquer la migration V10 (tables trajectory_segment et trajectory_point)
2. Exécuter le pré-processing des trajectoires
3. Afficher les statistiques
"""

import os
import sys
import psycopg2
from pathlib import Path

# Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '172.31.60.8'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'ais'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'music861!')
}

MIGRATION_FILE = Path(__file__).parent.parent / 'db' / 'migrations' / 'V10__create_trajectory_training_table.sql'


def check_tables_exist(conn) -> bool:
    """Vérifie si les tables existent déjà."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'trajectory_segment'
            )
        """)
        return cur.fetchone()[0]


def apply_migration(conn):
    """Applique la migration SQL."""
    print("📦 Application de la migration V10...")
    
    if not MIGRATION_FILE.exists():
        print(f"❌ Fichier migration introuvable: {MIGRATION_FILE}")
        return False
    
    with open(MIGRATION_FILE, 'r') as f:
        sql = f.read()
    
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    
    print("✅ Migration appliquée avec succès!")
    return True


def get_data_stats(conn):
    """Affiche les statistiques des données."""
    print("\n📊 STATISTIQUES DES DONNÉES")
    print("=" * 50)
    
    with conn.cursor() as cur:
        # Nombre de navires
        cur.execute("SELECT COUNT(*) FROM vessel")
        n_vessels = cur.fetchone()[0]
        print(f"Navires: {n_vessels:,}")
        
        # Nombre de positions
        cur.execute("SELECT COUNT(*) FROM position_vessel")
        n_positions = cur.fetchone()[0]
        print(f"Positions totales: {n_positions:,}")
        
        # Période couverte
        cur.execute("""
            SELECT MIN(base_date_time), MAX(base_date_time)
            FROM position_vessel
        """)
        min_date, max_date = cur.fetchone()
        print(f"Période: {min_date} → {max_date}")
        
        # Stats par type de navire
        cur.execute("""
            SELECT vt.description, COUNT(DISTINCT v.id) as n_vessels
            FROM vessel v
            LEFT JOIN vessel_type vt ON v.vessel_type_id = vt.id
            GROUP BY vt.description
            ORDER BY n_vessels DESC
            LIMIT 10
        """)
        print("\nTop 10 types de navires:")
        for desc, count in cur.fetchall():
            print(f"  {desc or 'Unknown'}: {count}")


def get_trajectory_stats(conn):
    """Affiche les stats des trajectoires pré-processées."""
    print("\n📈 STATISTIQUES DES TRAJECTOIRES PRÉ-PROCESSÉES")
    print("=" * 50)
    
    with conn.cursor() as cur:
        # Vérifier si des données existent
        cur.execute("SELECT COUNT(*) FROM trajectory_segment")
        n_segments = cur.fetchone()[0]
        
        if n_segments == 0:
            print("⚠️ Aucune trajectoire pré-processée!")
            print("   Exécutez: python etl/etl/transform/prepare_trajectories.py")
            return
        
        print(f"Segments totaux: {n_segments:,}")
        
        cur.execute("SELECT COUNT(*) FROM trajectory_segment WHERE is_valid_for_training = TRUE")
        n_valid = cur.fetchone()[0]
        print(f"Segments valides pour training: {n_valid:,}")
        
        cur.execute("SELECT COUNT(*) FROM trajectory_point")
        n_points = cur.fetchone()[0]
        print(f"Points totaux: {n_points:,}")
        
        cur.execute("""
            SELECT 
                AVG(num_points) as avg_points,
                AVG(quality_score) as avg_quality,
                AVG(avg_delta_t) as avg_interval
            FROM trajectory_segment
            WHERE is_valid_for_training = TRUE
        """)
        avg_pts, avg_qual, avg_dt = cur.fetchone()
        print(f"\nMoyennes (segments valides):")
        print(f"  Points/segment: {avg_pts:.1f}")
        print(f"  Score qualité: {avg_qual:.2f}")
        print(f"  Intervalle moyen: {avg_dt:.0f}s ({avg_dt/60:.1f} min)")
        
        # Estimation du dataset
        cur.execute("""
            SELECT SUM(GREATEST(0, num_points - 30))
            FROM trajectory_segment
            WHERE is_valid_for_training = TRUE
        """)
        estimated_samples = cur.fetchone()[0] or 0
        print(f"\n📦 Échantillons estimés pour training: ~{int(estimated_samples/5):,}")


def main():
    print("=" * 60)
    print("🚀 SETUP DONNÉES TRAJECTOIRES AIS POUR ML")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"✅ Connecté à {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        sys.exit(1)
    
    try:
        # Stats données brutes
        get_data_stats(conn)
        
        # Vérifier/appliquer migration
        if check_tables_exist(conn):
            print("\n✅ Tables trajectory_* déjà existantes")
        else:
            apply_migration(conn)
        
        # Stats trajectoires
        get_trajectory_stats(conn)
        
        print("\n" + "=" * 60)
        print("📋 PROCHAINES ÉTAPES")
        print("=" * 60)
        print("""
1. Si les trajectoires ne sont pas pré-processées:
   python etl/etl/transform/prepare_trajectories.py --limit 1000

2. Une fois les données prêtes, lancer l'entraînement:
   python notebooks/train_v3_optimized.py --epochs 100

3. Pour tester sur toutes les données:
   python etl/etl/transform/prepare_trajectories.py
        """)
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
