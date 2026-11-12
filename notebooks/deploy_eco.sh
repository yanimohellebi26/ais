#!/bin/bash
# =============================================================================
#  deploy_eco.sh — Deploiement et lancement entrainement sur serveur ECO
#  Usage : ./deploy_eco.sh
# =============================================================================

set -e

ECO_USER="ym519512"
ECO_HOST="eco"
ECO_DIR="/home1/${ECO_USER}/ais_training"
LOCAL_SCRIPT="$(dirname "$0")/train_eco.py"

echo "============================================================"
echo " DEPLOIEMENT AIS LSTM-Transformer -> ECO"
echo "============================================================"
echo " Cible : ${ECO_USER}@${ECO_HOST}:${ECO_DIR}"
echo ""

# 1. Creer le dossier distant
echo "[1/4] Creation du dossier distant..."
ssh ${ECO_USER}@${ECO_HOST} "mkdir -p ${ECO_DIR}/eco_output"

# 2. Copier le script d'entrainement
echo "[2/4] Copie du script train_eco.py..."
scp "${LOCAL_SCRIPT}" ${ECO_USER}@${ECO_HOST}:${ECO_DIR}/train_eco.py
echo "     train_eco.py copie"

# 3. Verifier / installer les dependances Python sur ECO
echo "[3/4] Verification des dependances Python..."
ssh ${ECO_USER}@${ECO_HOST} bash << 'REMOTE_SETUP'
set -e
cd /home1/ym519512/ais_training

# Creer un venv si absent
if [ ! -d "venv" ]; then
    echo "  Creation du venv Python..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "  Installation des packages..."
pip install --quiet --upgrade pip

# PyTorch avec support CUDA 12.x (compatible CUDA 13.1 driver)
pip install --quiet torch torchvision --index-url https://download.pytorch.org/whl/cu121

pip install --quiet \
    numpy \
    pandas \
    scikit-learn \
    tqdm \
    pyproj

echo "  Dependances OK"
python3 -c "import torch; print(f'  PyTorch {torch.__version__}, CUDA={torch.cuda.is_available()}, GPU={torch.cuda.device_count()}')"
REMOTE_SETUP

echo "     Dependances pretes"

# 4. Lancer l'entrainement dans tmux (persistant)
echo "[4/4] Lancement de l'entrainement..."
ssh ${ECO_USER}@${ECO_HOST} bash << 'REMOTE_TRAIN'
set -e
cd /home1/ym519512/ais_training
source venv/bin/activate

# Tuer d'anciens processus d'entrainement
pkill -u ym519512 -f 'train_eco' 2>/dev/null || true
sleep 1

SESSION="ais_train"

if command -v tmux &> /dev/null; then
    tmux kill-session -t ${SESSION} 2>/dev/null || true

    tmux new-session -d -s ${SESSION} \
        "python3 -u train_eco.py \
            --csv-file ais_data.csv \
            --epochs 150 \
            --batch-size 16384 \
            --lr 1e-3 \
            --patience 20 \
            --hidden-dim 512 \
            --num-layers 4 \
            --num-heads 8 \
            --num-workers 8 \
            --multi-gpu \
            --output-dir ./eco_output \
        2>&1 | tee eco_output/train.log"

    echo ""
    echo "  Entrainement lance dans tmux session '${SESSION}'"
    echo ""
    echo "  Pour suivre les logs :"
    echo "    ssh ym519512@eco"
    echo "    tmux attach -t ${SESSION}"
    echo ""
    echo "  Pour voir les logs sans attacher :"
    echo "    ssh ym519512@eco 'tail -f /home1/ym519512/ais_training/eco_output/train.log'"
else
    nohup python3 -u train_eco.py \
        --csv-file ais_data.csv \
        --epochs 150 \
        --batch-size 16384 \
        --lr 1e-3 \
        --patience 20 \
        --hidden-dim 512 \
        --num-layers 4 \
        --num-heads 8 \
        --num-workers 8 \
        --multi-gpu \
        --output-dir ./eco_output \
    > eco_output/train.log 2>&1 &

    echo "  PID : $!"
    echo "  Entrainement lance (nohup)"
    echo "  Logs : /home1/ym519512/ais_training/eco_output/train.log"
fi
REMOTE_TRAIN

echo ""
echo "============================================================"
echo " DEPLOIEMENT TERMINE"
echo "============================================================"
echo ""
echo " Suivre les logs en direct :"
echo "   ssh ${ECO_USER}@${ECO_HOST} 'tail -f /home1/ym519512/ais_training/eco_output/train.log'"
echo ""
echo " Recuperer les modeles apres entrainement :"
echo "   scp -r ${ECO_USER}@${ECO_HOST}:${ECO_DIR}/eco_output/ ./eco_output/"
echo ""
