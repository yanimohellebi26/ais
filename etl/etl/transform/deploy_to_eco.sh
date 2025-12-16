#!/bin/bash
# Deploy training scripts to ECO server

set -e

SERVER="ym519512@eco"
LOCAL_DIR="/home/yani/master1/PROJET/ais/etl/etl/transform"
REMOTE_DIR="~/ais/etl/etl/transform"

FILES=(
    "train_model_gpu.py"
    "train_on_eco.sh"
    "test_gpu_config.py"
    "requirements_training.txt"
)

echo "Checking local files..."
for file in "${FILES[@]}"; do
    if [ ! -f "$LOCAL_DIR/$file" ]; then
        echo "Missing file: $file"
        exit 1
    fi
done

echo "Creating remote directory..."
ssh $SERVER "mkdir -p $REMOTE_DIR"

echo "Transferring files..."
for file in "${FILES[@]}"; do
    scp "$LOCAL_DIR/$file" "$SERVER:$REMOTE_DIR/"
done

echo "Setting permissions..."
ssh $SERVER "cd $REMOTE_DIR && chmod +x train_on_eco.sh test_gpu_config.py"

echo "Installing dependencies..."
ssh $SERVER "cd $REMOTE_DIR && pip3 install -r requirements_training.txt"

echo "Testing configuration..."
ssh $SERVER "cd $REMOTE_DIR && python3 test_gpu_config.py"

echo "Deployment complete. To start training:"
echo "  ssh $SERVER"
echo "  cd $REMOTE_DIR"
echo "  ./train_on_eco.sh"
