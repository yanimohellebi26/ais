#!/usr/bin/env python3
"""
Script de test rapide pour vérifier la configuration GPU avant entraînement
"""
import sys
import torch
import numpy as np
import pandas as pd
from sqlalchemy import create_engine

print("="*70)
print("TEST DE CONFIGURATION - ENTRAÎNEMENT AIS")
print("="*70)

# Test 1: PyTorch et CUDA
print("\n[1] PyTorch et CUDA")
print(f"   PyTorch version: {torch.__version__}")
print(f"   CUDA disponible: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"   Nombre de GPUs: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"      Mémoire totale: {props.total_memory / 1e9:.1f} GB")
        print(f"      Compute capability: {props.major}.{props.minor}")
else:
    print("   ⚠ CUDA non disponible - entraînement sera sur CPU")

# Test 2: Dépendances
print("\n[2] Dépendances Python")
try:
    import numpy
    print(f"   ✓ NumPy: {numpy.__version__}")
except ImportError:
    print("   ❌ NumPy manquant")
    sys.exit(1)

try:
    import pandas
    print(f"   ✓ Pandas: {pandas.__version__}")
except ImportError:
    print("   ❌ Pandas manquant")
    sys.exit(1)

try:
    import sqlalchemy
    print(f"   ✓ SQLAlchemy: {sqlalchemy.__version__}")
except ImportError:
    print("   ❌ SQLAlchemy manquant")
    sys.exit(1)

# Test 3: Connexion base de données
print("\n[3] Connexion Base de Données")
DB_CONFIG = {
    'host': '172.31.60.8',
    'port': 5432,
    'database': 'ais',
    'user': 'postgres',
    'password': 'ANjw/84H77C9h2'
}

DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Test connexion
    query = "SELECT COUNT(*) as total FROM trajectory_processed"
    df = pd.read_sql(query, engine)
    total_points = df['total'].iloc[0]
    
    print(f"   ✓ Connexion réussie")
    print(f"   ✓ Points dans trajectory_processed: {total_points:,}")
    
    # Vérifier les splits
    query = "SELECT dataset_split, COUNT(*) as count FROM trajectory_processed GROUP BY dataset_split"
    df_splits = pd.read_sql(query, engine)
    
    print("   ✓ Splits disponibles:")
    for _, row in df_splits.iterrows():
        print(f"      {row['dataset_split']}: {row['count']:,} points")
    
except Exception as e:
    print(f"   ❌ Erreur de connexion: {e}")
    sys.exit(1)

# Test 4: Test GPU avec petit batch
if torch.cuda.is_available():
    print("\n[4] Test GPU avec Tensor")
    try:
        # Créer un tensor et le déplacer sur GPU
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = torch.matmul(x, y)
        
        print(f"   ✓ Multiplication matricielle GPU réussie")
        print(f"   ✓ Tensor shape: {z.shape}")
        print(f"   ✓ Device: {z.device}")
        
        # Test multi-GPU si disponible
        if torch.cuda.device_count() > 1:
            model = torch.nn.Linear(1000, 1000)
            model = torch.nn.DataParallel(model)
            model = model.cuda()
            output = model(x)
            print(f"   ✓ DataParallel fonctionne sur {torch.cuda.device_count()} GPUs")
        
        del x, y, z
        torch.cuda.empty_cache()
        
    except Exception as e:
        print(f"   ❌ Erreur GPU: {e}")
        sys.exit(1)

# Test 5: Mémoire GPU disponible
if torch.cuda.is_available():
    print("\n[5] Mémoire GPU")
    for i in range(torch.cuda.device_count()):
        mem_allocated = torch.cuda.memory_allocated(i) / 1e9
        mem_reserved = torch.cuda.memory_reserved(i) / 1e9
        mem_total = torch.cuda.get_device_properties(i).total_memory / 1e9
        mem_free = mem_total - mem_allocated
        
        print(f"   GPU {i}:")
        print(f"      Allouée:  {mem_allocated:.2f} GB")
        print(f"      Réservée: {mem_reserved:.2f} GB")
        print(f"      Libre:    {mem_free:.2f} GB")
        print(f"      Totale:   {mem_total:.2f} GB")

# Résumé
print("\n" + "="*70)
print("RÉSUMÉ DU TEST")
print("="*70)
print("\n✅ Configuration valide pour l'entraînement!")

if torch.cuda.is_available():
    print(f"✅ {torch.cuda.device_count()} GPU(s) détecté(s)")
    print(f"✅ Batch size recommandé: {64 * torch.cuda.device_count()}")
else:
    print("⚠  Entraînement sur CPU - sera plus lent")
    print("⚠  Batch size recommandé: 32")

print(f"✅ {total_points:,} points disponibles pour entraînement")
print("\n🚀 Prêt à lancer: ./train_on_eco.sh")
print("="*70)
