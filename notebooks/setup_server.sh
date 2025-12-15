#!/bin/bash
# Script de setup pour le serveur ECO avec A100

echo " Setup de l'environnement pour l'entraînement AIS"
echo "=================================================="

# Créer un environnement virtuel
echo " Création de l'environnement virtuel..."
python3 -m venv ~/ais_env
source ~/ais_env/bin/activate

# Installer les dépendances
echo " Installation des dépendances..."
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install numpy pandas tqdm scikit-learn psycopg2-binary matplotlib seaborn

# Vérifier CUDA
echo ""
echo " Vérification de CUDA..."
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA disponible: {torch.cuda.is_available()}'); print(f'Nombre de GPUs: {torch.cuda.device_count()}'); [print(f'  GPU {i}: {torch.cuda.get_device_name(i)}') for i in range(torch.cuda.device_count())]"

echo ""
echo " Setup terminé!"
echo ""
echo "Pour lancer l'entraînement:"
echo "  source ~/ais_env/bin/activate"
echo "  python train_remote_a100.py"
