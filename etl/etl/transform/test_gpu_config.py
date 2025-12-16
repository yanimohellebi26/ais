#!/usr/bin/env python3
"""
Quick GPU configuration test script avant entraînement
"""
import sys
import torch
import numpy as np
import pandas as pd
from sqlalchemy import create_engine

print("="*70)
print("CONFIGURATION TEST - AIS TRAINING")
print("="*70)

# Test 1: PyTorch and CUDA
print("\n[1] PyTorch and CUDA")
print(f"   PyTorch version: {torch.__version__}")
print(f"   CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"   Number of GPUs: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"      Total memory: {props.total_memory / 1e9:.1f} GB")
        print(f"      Compute capability: {props.major}.{props.minor}")
else:
    print("   WARNING: CUDA non disponible - training will be on CPU")

# Test 2: Dépendances
print("\n[2] Python Dependencies")
try:
    import numpy
    print(f"   OK NumPy: {numpy.__version__}")
except ImportError:
    print("   ERROR NumPy missing")
    sys.exit(1)

try:
    import pandas
    print(f"   OK Pandas: {pandas.__version__}")
except ImportError:
    print("   ERROR Pandas missing")
    sys.exit(1)

try:
    import sqlalchemy
    print(f"   OK SQLAlchemy: {sqlalchemy.__version__}")
except ImportError:
    print("   ERROR SQLAlchemy missing")
    sys.exit(1)

# Test 3: Connexion base de données
print("\n[3] Database Connection")
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
    
    print(f"   OK Connection successful")
    print(f"   OK Points in trajectory_processed: {total_points:,}")
    
    # Vérifier les splits
    query = "SELECT dataset_split, COUNT(*) as count FROM trajectory_processed GROUP BY dataset_split"
    df_splits = pd.read_sql(query, engine)
    
    print("   OK Available splits:")
    for _, row in df_splits.iterrows():
        print(f"      {row['dataset_split']}: {row['count']:,} points")
    
except Exception as e:
    print(f"   ERROR Connection error: {e}")
    sys.exit(1)

# Test 4: Test GPU avec petit batch
if torch.cuda.is_available():
    print("\n[4] GPU Test with Tensor")
    try:
        # Créer un tensor et le déplacer sur GPU
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = torch.matmul(x, y)
        
        print(f"   OK GPU matrix multiplication successful")
        print(f"   OK Tensor shape: {z.shape}")
        print(f"   OK Device: {z.device}")
        
        # Test multi-GPU si disponible
        if torch.cuda.device_count() > 1:
            model = torch.nn.Linear(1000, 1000)
            model = torch.nn.DataParallel(model)
            model = model.cuda()
            output = model(x)
            print(f"   OK DataParallel works on {torch.cuda.device_count()} GPUs")
        
        del x, y, z
        torch.cuda.empty_cache()
        
    except Exception as e:
        print(f"   ERROR GPU error: {e}")
        sys.exit(1)

# Test 5: Available GPU memory
if torch.cuda.is_available():
    print("\n[5] GPU Memory")
    for i in range(torch.cuda.device_count()):
        mem_allocated = torch.cuda.memory_allocated(i) / 1e9
        mem_reserved = torch.cuda.memory_reserved(i) / 1e9
        mem_total = torch.cuda.get_device_properties(i).total_memory / 1e9
        mem_free = mem_total - mem_allocated
        
        print(f"   GPU {i}:")
        print(f"      Allocated:  {mem_allocated:.2f} GB")
        print(f"      Reserved: {mem_reserved:.2f} GB")
        print(f"      Free:    {mem_free:.2f} GB")
        print(f"      Total:   {mem_total:.2f} GB")

# Résumé
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print("\nOK Valid configuration for training!")

if torch.cuda.is_available():
    print(f"OK {torch.cuda.device_count()} GPU(s) detected")
    print(f"OK Recommended batch size: {64 * torch.cuda.device_count()}")
else:
    print("WARNING:  Training on CPU - will be slower")
    print("WARNING:  Recommended batch size: 32")

print(f"OK {total_points:,} points available for training")
print("\nReady: Ready to launch: ./train_on_eco.sh")
print("="*70)
