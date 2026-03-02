#!/bin/bash
# =============================================================================
#  deploy_eco.sh — Déploiement et lancement entraînement sur serveur ECO
#  Usage : ./deploy_eco.sh
# =============================================================================

set -e

ECO_USER="ym519512"
ECO_HOST="eco"
ECO_DIR="/home1/${ECO_USER}/ais_training"
LOCAL_SCRIPT="$(dirname "$0")/train_eco.py"

echo "============================================================"
echo " DÉPLOIEMENT AIS LSTM-Transformer → ECO"
echo "============================================================"
echo " Cible : ${ECO_USER}@${ECO_HOST}:${ECO_DIR}"
echo ""

# 1. Créer le dossier distant
echo "[1/5] Création du dossier distant..."
ssh ${ECO_USER}@${ECO_HOST} "mkdir -p ${ECO_DIR}/eco_output"

# 2. Copier le script d'entraînement
echo "[2/5] Copie du script train_eco.py..."
scp "${LOCAL_SCRIPT}" ${ECO_USER}@${ECO_HOST}:${ECO_DIR}/train_eco.py
echo "     ✅ train_eco.py copié"

# 3. Vérifier / installer les dépendances Python sur ECO
echo "[3/5] Vérification des dépendances Python..."
ssh ${ECO_USER}@${ECO_HOST} bash << 'REMOTE_SETUP'
set -e
cd /home1/ym519512/ais_training

# Créer un venv si absent
if [ ! -d "venv" ]; then
    echo "  Création du venv Python..."
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
    psycopg2-binary \
    sqlalchemy \
    tqdm \
    pyproj

echo "  ✅ Dépendances OK"
python3 -c "import torch; print(f'  PyTorch {torch.__version__}, CUDA={torch.cuda.is_available()}, GPU={torch.cuda.device_count()}')"
REMOTE_SETUP

echo "     ✅ Dépendances prêtes"

# 4. Vérifier la connexion PostgreSQL depuis ECO
# Note: le serveur ECO doit pouvoir accéder à votre PostgreSQL
# Option A : si PostgreSQL tourne en local sur votre machine avec accès réseau
# Option B : tunnel SSH inverse pour exposer le PostgreSQL local sur ECO
echo "[4/5] Configuration tunnel SSH inverse PostgreSQL..."
echo "     Votre PostgreSQL local (localhost:5432) sera exposé sur ECO:15432"

# Tuer un éventuel ancien tunnel
ssh ${ECO_USER}@${ECO_HOST} "pkill -f 'ssh.*15432' 2>/dev/null || true"

# Tunnel inverse : ECO:15432 → votre_machine:5432
ssh -f -N -R 15432:localhost:5432 ${ECO_USER}@${ECO_HOST}
echo "     ✅ Tunnel actif : ECO:15432 → localhost:5432"

# 5. Lancer l'entraînement dans un screen/tmux (persistant)
echo "[5/5] Lancement de l'entraînement..."
ssh ${ECO_USER}@${ECO_HOST} bash << 'REMOTE_TRAIN'
set -e
cd /home1/ym519512/ais_training
source venv/bin/activate

# Tuer d'anciens processus d'entraînement
pkill -u ym519512 -f 'train_eco' 2>/dev/null || true
sleep 1

# Utiliser tmux si disponible, sinon nohup
SESSION="ais_train"

if command -v tmux &> /dev/null; then
    # Tuer une session existante
    tmux kill-session -t ${SESSION} 2>/dev/null || true

    tmux new-session -d -s ${SESSION} \
        "python3 -u train_eco.py \
            --pg-host 127.0.0.1 \
            --pg-port 15432 \
            --pg-user postgres \
            --pg-password 'ANjw/84H77C9h2' \
            --pg-db ais \
            --epochs 150 \
            --batch-size 512 \
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
    echo "  ✅ Entraînement lancé dans tmux session '${SESSION}'"
    echo ""
    echo "  Pour suivre les logs :"
    echo "    ssh ${ECO_USER}@eco"
    echo "    tmux attach -t ${SESSION}"
    echo ""
    echo "  Pour voir les logs sans attacher :"
    echo "    ssh ${ECO_USER}@eco 'tail -f /home1/ym519512/ais_training/eco_output/train.log'"
else
    # Fallback nohup
    nohup python3 -u train_eco.py \
        --pg-host 127.0.0.1 \
        --pg-port 15432 \
        --pg-user postgres \
        --pg-password 'ANjw/84H77C9h2' \
        --pg-db ais \
        --epochs 150 \
        --batch-size 512 \
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
    echo "  ✅ Entraînement lancé (nohup)"
    echo "  Logs : /home1/ym519512/ais_training/eco_output/train.log"
fi
REMOTE_TRAIN

echo ""
echo "============================================================"
echo " DÉPLOIEMENT TERMINÉ"
echo "============================================================"
echo ""
echo " Suivre les logs en direct :"
echo "   ssh ${ECO_USER}@${ECO_HOST} 'tail -f /home1/ym519512/ais_training/eco_output/train.log'"
echo ""
echo " Récupérer les modèles après entraînement :"
echo "   scp -r ${ECO_USER}@${ECO_HOST}:${ECO_DIR}/eco_output/ ./eco_output/"
echo ""
