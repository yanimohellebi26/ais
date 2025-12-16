#!/bin/bash
# Train AIS model on ECO server with GPU support

set -e

BATCH_SIZE=1024
EPOCHS=50
LR=0.0001
NUM_WORKERS=16
GPU_ID=0
SAVE_DIR="./models"

while [[ $# -gt 0 ]]; do
    case $1 in
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --epochs)
            EPOCHS="$2"
            shift 2
            ;;
        --lr)
            LR="$2"
            shift 2
            ;;
        --num-workers)
            NUM_WORKERS="$2"
            shift 2
            ;;
        --gpu-id)
            GPU_ID="$2"
            shift 2
            ;;
        --save-dir)
            SAVE_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if ! command -v python3 &> /dev/null; then
    echo "Python3 not found"
    exit 1
fi

mkdir -p "$SAVE_DIR"

LOG_FILE="training_$(date +%Y%m%d_%H%M%S).log"

python3 train_model_gpu.py \
    --batch-size "$BATCH_SIZE" \
    --epochs "$EPOCHS" \
    --lr "$LR" \
    --num-workers "$NUM_WORKERS" \
    --save-dir "$SAVE_DIR" \
    --gpu-id "$GPU_ID" \
    2>&1 | tee "$LOG_FILE"

exit ${PIPESTATUS[0]}
