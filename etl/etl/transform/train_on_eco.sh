#!/bin/bash
#
# Script d'entraînement sur serveur ECO avec 2 GPUs
# Usage: ./train_on_eco.sh [OPTIONS]
#

set -e  # Arrêt si erreur

echo "=============================================================="
echo "ENTRAÎNEMENT MODÈLE AIS - SERVEUR ECO (2x GPUs)"
echo "=============================================================="
echo ""

# Configuration optimisée pour serveur ECO (1x NVIDIA L40S, 46GB VRAM)
BATCH_SIZE=1024
EPOCHS=50
LR=0.0001
NUM_WORKERS=16
GPU_ID=0  # Utiliser GPU 0 uniquement (meilleur que multi-GPU pour ce cas)
SAVE_DIR="./models"

# Parse arguments
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
            echo "Option inconnue: $1"
            exit 1
            ;;
    esac
done

# Vérifier Python et environnement
echo "[1/5] Vérification de l'environnement..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non trouvé!"
    exit 1
fi
echo "   ✓ Python: $(python3 --version)"

# Vérifier PyTorch et CUDA
echo ""
echo "[2/5] Vérification de PyTorch et CUDA..."
python3 -c "import torch; print(f'   ✓ PyTorch: {torch.__version__}')"
python3 -c "import torch; print(f'   ✓ CUDA disponible: {torch.cuda.is_available()}')"
python3 -c "import torch; print(f'   ✓ Nombre de GPUs: {torch.cuda.device_count()}')" || true

# Vérifier les dépendances
echo ""
echo "[3/5] Vérification des dépendances..."
python3 -c "import numpy, pandas, sqlalchemy" && echo "   ✓ numpy, pandas, sqlalchemy" || {
    echo "❌ Dépendances manquantes!"
    exit 1
}

# Créer dossier de sauvegarde
echo ""
echo "[4/5] Préparation..."
mkdir -p "$SAVE_DIR"
echo "   ✓ Dossier de sauvegarde: $SAVE_DIR"

# Afficher GPU info
echo ""
echo "[5/5] Information GPU..."
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader || {
    echo "   ⚠ nvidia-smi non disponible (CPU mode)"
}

# Lancer l'entraînement
echo ""
echo "=============================================================="
echo "LANCEMENT DE L'ENTRAÎNEMENT"
echo "=============================================================="
echo "Configuration:"
echo "   Batch size: $BATCH_SIZE"
echo "   Epochs:     $EPOCHS"
echo "   Learning rate: $LR"
echo "   Num workers: $NUM_WORKERS"
echo "   Save dir:   $SAVE_DIR"
echo "   GPU ID:     $GPU_ID ($([ $GPU_ID -eq -1 ] && echo "tous les GPUs" || echo "GPU $GPU_ID uniquement"))"
echo ""

# Exécuter le script Python avec logging
LOG_FILE="training_$(date +%Y%m%d_%H%M%S).log"
echo "Logs sauvegardés dans: $LOG_FILE"
echo ""

python3 train_model_gpu.py \
    --batch-size "$BATCH_SIZE" \
    --epochs "$EPOCHS" \
    --lr "$LR" \
    --num-workers "$NUM_WORKERS" \
    --save-dir "$SAVE_DIR" \
    --gpu-id "$GPU_ID" \
    2>&1 | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "=============================================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ ENTRAÎNEMENT TERMINÉ AVEC SUCCÈS"
else
    echo "❌ ERREUR PENDANT L'ENTRAÎNEMENT (code: $EXIT_CODE)"
fi
echo "=============================================================="
echo ""

exit $EXIT_CODE
