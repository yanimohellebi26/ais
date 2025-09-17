# ETL Project

Pipeline ETL en Python avec [Poetry](https://python-poetry.org/).

## 🚀 Prérequis
- Python **>=3.10,<3.13** (recommandé : 3.12)
- [Poetry](https://python-poetry.org/docs/#installation)
- (optionnel) Docker et Docker Compose

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
4. Lancer le script de base ETL
   ```bash
   poetry run etl
   ```

## Utilisation avec Docker
_A compléter avec devops_