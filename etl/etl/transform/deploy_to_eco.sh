#!/bin/bash
#
# Script de déploiement complet sur serveur ECO
# Exécuter depuis votre machine locale
#

set -e

SERVER="ym519512@eco"
LOCAL_DIR="/home/yani/master1/PROJET/ais/etl/etl/transform"
REMOTE_DIR="~/ais/etl/etl/transform"

echo "=============================================================="
echo "DÉPLOIEMENT ENTRAÎNEMENT AIS SUR SERVEUR ECO"
echo "=============================================================="
echo ""

# Vérifier que les fichiers existent localement
echo "[1/6] Vérification des fichiers locaux..."
FILES=(
    "train_model_gpu.py"
    "train_on_eco.sh"
    "test_gpu_config.py"
    "requirements_training.txt"
    "README_TRAINING.md"
)

for file in "${FILES[@]}"; do
    if [ ! -f "$LOCAL_DIR/$file" ]; then
        echo "❌ Fichier manquant: $file"
        exit 1
    fi
    echo "   ✓ $file"
done

# Créer le répertoire distant si nécessaire
echo ""
echo "[2/6] Création du répertoire distant..."
ssh $SERVER "mkdir -p $REMOTE_DIR"
echo "   ✓ Répertoire créé: $REMOTE_DIR"

# Transférer les fichiers
echo ""
echo "[3/6] Transfert des fichiers vers ECO..."
for file in "${FILES[@]}"; do
    echo "   Transfert: $file"
    scp "$LOCAL_DIR/$file" "$SERVER:$REMOTE_DIR/"
done
echo "   ✓ Tous les fichiers transférés"

# Rendre les scripts exécutables
echo ""
echo "[4/6] Configuration des permissions..."
ssh $SERVER "cd $REMOTE_DIR && chmod +x train_on_eco.sh test_gpu_config.py"
echo "   ✓ Scripts rendus exécutables"

# Installer PyTorch avec CUDA
echo ""
echo "[5/6] Installation de PyTorch avec CUDA..."
echo ""
echo "IMPORTANT: Vérifiez d'abord la version CUDA sur le serveur:"
echo ""
echo "   ssh $SERVER nvidia-smi"
echo ""
echo "Puis installez PyTorch correspondant:"
echo ""
echo "   Pour CUDA 11.8:"
echo "   ssh $SERVER 'pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118'"
echo ""
echo "   Pour CUDA 12.1:"
echo "   ssh $SERVER 'pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121'"
echo ""
read -p "Appuyez sur Entrée après avoir installé PyTorch..."

# Installer les dépendances
echo ""
echo "[6/6] Installation des dépendances..."
ssh $SERVER "cd $REMOTE_DIR && pip3 install -r requirements_training.txt"
echo "   ✓ Dépendances installées"

# Test de configuration
echo ""
echo "=============================================================="
echo "DÉPLOIEMENT TERMINÉ - TEST DE CONFIGURATION"
echo "=============================================================="
echo ""
echo "Exécution du test de configuration sur ECO..."
echo ""
ssh $SERVER "cd $REMOTE_DIR && python3 test_gpu_config.py"

echo ""
echo "=============================================================="
echo "PRÊT À LANCER L'ENTRAÎNEMENT!"
echo "=============================================================="
echo ""
echo "Commandes pour démarrer l'entraînement:"
echo ""
echo "   # Connexion au serveur"
echo "   ssh $SERVER"
echo ""
echo "   # Aller dans le répertoire"
echo "   cd $REMOTE_DIR"
echo ""
echo "   # Lancer l'entraînement"
echo "   ./train_on_eco.sh"
echo ""
echo "   # OU avec options personnalisées"
echo "   ./train_on_eco.sh --batch-size 256 --epochs 100"
echo ""
echo "   # Surveiller les GPUs (dans un autre terminal)"
echo "   watch -n 1 nvidia-smi"
echo ""
echo "=============================================================="
