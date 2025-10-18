# ETL Pipeline Python

Cette partie du projet contient le pipeline ETL pour traiter et insérer des données dans la base PostgreSQL.

---

## 🐍 Prérequis

- Python 3.10 à 3.12
- [Poetry](https://python-poetry.org/) pour gérer les dépendances et l'environnement
- Docker pour héberger la base de données PostgreSQL.
---

## 📦 Installation du projet

1. Vérifier votre version de Python : 
```bash
  python --version
```
   
2. Créer l'environnement Poetry :
```bash
  poetry env use python3.12 #(Pas obliger si IDE configurer)
```
   
3. Installer les dépendances : 
```bash
   poetry install
   poetry install --with arm64 #Uniquement pour les utilisateur de systèmes ARM64 
```

## ⚙️ Configuration des variables d'environnement

1. Copier le fichier d'exemple .env.example en .env :
```bash 
   cp .env.example .env
```

2. Modifier les variables d'environnement pour correspondre à votre config
```bash
   ENV=dev
   LOG_DIR=data/local/logs
   AIS_DOWNLOAD_FOLDER=data/local/downloads
   AIS_BASE_URL=https://coast.noaa.gov/htdata/CMSP/AISDataHandler
   
   DB_HOST=localhost
   DB_PORT=5432        # ou 5433 selon votre installation si vous avez psotgresql d'installer notamment.
   DB_NAME=ais
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_DRIVER=psycopg    # mettre 'pg8000' si vous êtes sur ARM64
```
Le paramètre DB_DRIVER permet de choisir le driver PostgreSQL : psycopg (classique) ou pg8000 (ARM64).

Pour lancer uniquement le container docker de la base de donnée :
```bash
    docker compose up db -d
```

## 🧩 Système de Workflows ETL 

Ce module permet de définir, exécuter et superviser des workflows / pipelines ETL composés de plusieurs étapes de traitement chaînées.
Chaque workflow est une suite de fonctions qui reçoivent et retournent un objet de contexte typé contenant les données manipulées tout au long du pipeline.

Les pipelines sont définis dans le dictionnaire **PIPELINES**: 
```python
PIPELINES = {
    "load-vessels": [
        (extract_function, {}),
        (transform_function, {}),
        (load_function, {})
    ]
}
```
Chaque fonction reçoit un objet **context** (dataclass) et retourne le même **contexte** mis à jour

Le contexte est un objet servant à partager les données entre les étapes du workflow
```python
    from dataclasses import dataclass
    from typing import Optional
    import pandas as pd
    
    @dataclass
    class VesselContext:
        file: Optional[str] = None          
        df: Optional[pd.DataFrame] = None   
        df_db: Optional[pd.DataFrame] = None 
        workflow_id: Optional[str] = None
```

Exemple de fonction de traitement 
```python
def my_task(context: VesselContext, **kwargs) -> VesselContext:
    # 1. Lire les données depuis le contexte
    df = context.df
    # 2. Effectuer un traitement
    df = df.dropna(subset=["mmsi"])
    # 3. Mettre à jour le contexte
    context.df = df
    return context
```

## 🚀 Lancer les commandes CLI avec Click

Le projet contient des commandes CLI définies avec Click

- Lister les commandes disponibles :
```bash
   poetry run etl-cli --help
```
Exemple
```bash 
   poetry run etl-cli download
   poetry run etl-cli run-pipeline -p load-vessels -f file.csv
```

Les options disponibles pour les workflows : 
```bash
--pipeline, -p -> "Nom du workflow"
--file, -f -> "Fichier a analyser"
--continue-on-error, -coe -> "Le workflow ne s'interrompt pas si une erreur survient"
--use-timer, -t -> "Log les temps d éxécution de chaque traitement"
--workflow-name, -n -> "Donner un nom au workflow"
```

## 📝 Logger et gestion des logs

Le projet utilise colorlog pour centraliser le logging.

Exemple d'utilisation:
```python   
   from etl.utils.logger import Logger
   Logger.info("Démarrage du traitement ETL")
   Logger.error("Une erreur est survenue")
```

Les logs seront écrits dans le dossier défini par LOG_DIR dans votre .env.

## 💾 Accès à la base de données

Le projet utilise SQLAlchemy avec un pattern singleton pour les sessions :


```python
   from etl.utils.db import get_session
   from etl.models import User
   
   
   with get_session() as session:
       # Ajouter un utilisateur
       user = User(name="Bob", age=30)
       session.add(user)
   
       # Requête ORM
       users = session.query(User).filter(User.age > 20).all()
       for u in users:
           print(u.id, u.name)

```



Pour des requêtes SQL brutes :
```python
from sqlalchemy import text
from etl.utils.db import get_session

with db.get_session() as session:
    result = session.execute(text("SELECT * FROM users WHERE age > :age"), {"age": 20}).mappings()
    for row in result:
        print(row["id"], row["name"])
```

Si vous êtes sur ARM64 et que vous utilisez pg8000, cela fonctionne automatiquement via la variable DB_DRIVER.

## 🧪 Tests

Lancer tous les tests:
```bash 
  poetry run pytest
```

Les tests incluent la connexion à la base de données et le bon fonctionnement des utilitaires ETL.

## 📂 Structure du projet

etl/
- cli.py           **# Commandes CLI**
- workflow.py      **# Scripts de workflow**
- utils/
  - db.py        **# Gestion des sessions SQLAlchemy**
  - logger.py    **# Logger centralisé**
- models/          **# Définition des modèles ORM**
- tests/           **# Tests unitaires**
- pyproject.toml   **# Configuration Poetry**