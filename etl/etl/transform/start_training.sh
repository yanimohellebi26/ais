#!/bin/bash
# Script pour lancer l'entraînement complet en arrière-plan

cd ~/ais/etl/etl/transform

# Lancer l'entraînement
nohup ./train_on_eco.sh --batch-size 1024 --epochs 50 --num-workers 16 --gpu-id 0 &

echo "Training lancé en arrière-plan. PID: $!"
echo "Surveillez le log avec: tail -f training_*.log"
echo "Arrêtez le training avec: kill $!"
