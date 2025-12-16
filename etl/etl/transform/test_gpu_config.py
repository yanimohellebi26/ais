#!/usr/bin/env python3
"""
GPU configuration test script for AIS training
"""
import sys
import torch
import numpy as np
import pandas as pd
from sqlalchemy import create_engine

print("="*70)
print("AIS TRAINING CONFIGURATION TEST")
print("="*70)

# Test 1: PyTorch and CUDA
print("\n[1] PyTorch and CUDA")
print(f"    PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"    GPUs: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"    GPU {i}: {torch.cuda.get_device_name(i)} ({props.total_memory / 1e9:.1f} GB)")
else:
    print("    WARNING: CUDA not available - training will use CPU")

# Test 2: Dependencies
print("\n[2] Python Dependencies")
try:
    import numpy
    print(f"    NumPy: {numpy.__version__}")
except ImportError:
    print("    ERROR: NumPy missing")
    sys.exit(1)

try:
    import pandas
    print(f"    Pandas: {pandas.__version__}")
except ImportError:
    print("    ERROR: Pandas missing")
    sys.exit(1)

try:
    import sqlalchemy
    print(f"    SQLAlchemy: {sqlalchemy.__version__}")
except ImportError:
    print("    ERROR: SQLAlchemy missing")
    sys.exit(1)

# Test 3: Database Connection
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
    
    query = "SELECT COUNT(*) as total FROM trajectory_processed"
    df = pd.read_sql(query, engine)
    total_points = df['total'].iloc[0]
    
    print(f"    Connection successful, {total_points:,} points in trajectory_processed")
    
    query = "SELECT dataset_split, COUNT(*) as count FROM trajectory_processed GROUP BY dataset_split"
    df_splits = pd.read_sql(query, engine)
    
    print("    Splits:", end="")
    for _, row in df_splits.iterrows():
        print(f" {row['dataset_split']}={row['count']:,}", end="")
    print()
    
except Exception as e:
    print(f"    ERROR: Connection failed - {e}")
    sys.exit(1)

# Test 4: GPU Tensor Test
if torch.cuda.is_available():
    print("\n[4] GPU Tensor Test")
    try:
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = torch.matmul(x, y)
        
        print(f"    Matrix multiplication successful on {z.device}")
        
        if torch.cuda.device_count() > 1:
            model = torch.nn.Linear(1000, 1000)
            model = torch.nn.DataParallel(model).cuda()
            output = model(x)
            print(f"    DataParallel works on {torch.cuda.device_count()} GPUs")
        
        del x, y, z
        torch.cuda.empty_cache()
        
    except Exception as e:
        print(f"    ERROR: GPU test failed - {e}")
        sys.exit(1)

# Test 5: GPU Memory
if torch.cuda.is_available():
    print("\n[5] GPU Memory")
    for i in range(torch.cuda.device_count()):
        mem_allocated = torch.cuda.memory_allocated(i) / 1e9
        mem_total = torch.cuda.get_device_properties(i).total_memory / 1e9
        mem_free = mem_total - mem_allocated
        
        print(f"    GPU {i}: {mem_free:.1f} GB free / {mem_total:.1f} GB total")

# Summary
print("\n" + "="*70)
print("CONFIGURATION VALID - READY FOR TRAINING")
print("="*70)

if torch.cuda.is_available():
    print(f"Device: {torch.cuda.device_count()} GPU(s), Recommended batch size: {64 * torch.cuda.device_count()}")
else:
    print("Device: CPU, Recommended batch size: 32")

print(f"Dataset: {total_points:,} points available")
print("\nRun: ./train_on_eco.sh")
print("="*70)
