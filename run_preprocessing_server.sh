#!/bin/bash
# Script to run trajectory preprocessing on ECO server
# Optimized for 96 CPUs and 1TB RAM

echo "=========================================="
echo "AIS Trajectory Preprocessing Pipeline"
echo "Server: ECO (96 CPUs, 1TB RAM)"
echo "=========================================="
echo ""

# System info
echo "System resources:"
echo "  CPUs: $(nproc --all)"
echo "  RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  Available RAM: $(free -h | grep Mem | awk '{print $7}')"
echo ""

# Navigate to ETL directory
cd ~/ais/etl || exit 1

echo "Starting preprocessing pipeline..."
echo "Start time: $(date)"
echo ""

# Run preprocessing with time measurement
time python -m etl.transform.transform_trajectory_preprocessing

EXIT_CODE=$?

echo ""
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✓ Preprocessing completed successfully!"
    echo ""
    echo "Checking results in database..."
    python -c "
from utils.db import engine
import pandas as pd

query = '''
SELECT 
    dataset_split,
    COUNT(*) as points,
    COUNT(DISTINCT trajectory_id) as trajectories,
    COUNT(DISTINCT mmsi) as vessels
FROM trajectory_processed
GROUP BY dataset_split
ORDER BY dataset_split;
'''

with engine.connect() as conn:
    df = pd.read_sql(query, conn)
    
print(df.to_string(index=False))
print('')

query_total = 'SELECT COUNT(*) as total_points, COUNT(DISTINCT trajectory_id) as total_trajectories FROM trajectory_processed;'
with engine.connect() as conn:
    df_total = pd.read_sql(query_total, conn)
    
print('TOTAL:', df_total.to_string(index=False))
"
else
    echo ""
    echo "✗ Preprocessing failed with exit code $EXIT_CODE"
fi

echo ""
echo "=========================================="
