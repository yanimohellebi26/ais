# ETL Project

Pipeline ETL en Python avec [Poetry](https://python-poetry.org/).

L'ETL utilise click pour générer une CLI, et exécuté des workflows.

##  Prérequis
- Python **>=3.10,<3.13** (recommandé : 3.12)
- [Poetry](https://python-poetry.org/docs/#installation)
- (optionnel) Docker et Docker Compose

## 🔧 Configurer les variables d'environnement 

Dupliquer le fichier `.env.exemple` en un fichier `.env` avec les paramètres d'environnements adapté (Dev local, ou production).

## 🔧 Installation locale

1. Vérifier votre version de Python : 
   ```bash
   python --version
   ```
   
2. Créer l'environnement Poetry :
   ```bash
   poetry env use python3.12 #(Pas obliger si IDE configurer)
   poetry install
   ```
3. Lancer les tests :
    ```bash 
    poetry run pytest 
    ```
4. Lancer une commande CLI 
   ```bash
   poetry run etl-cli download -d 2024-01-13
   poetry run etl-cli --help
   ```
5. Lancer un workflow complet
   ```bash 
      poetry run etl-wkf run-workflow -w daily
      poetry run etl-cli --help
   ```
   

## Utilisation avec Docker et CRON 
_A compléter avec devops_