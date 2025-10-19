# ETL Pipeline Python

Cette partie du projet contient le pipeline ETL pour traiter et insérer des données dans la base PostgreSQL.

---

## 🐍 Prérequis

- Python 3.10 à 3.12
- [Poetry](https://python-poetry.org/) pour gérer les dépendances et l'environnement
- Docker
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
```

## ⚙️ Configuration des variables d'environnement

1. Copier le fichier d'environnement à la racine du projet 
```bash 
   cp ../.env.exemple ../.env
```

2. Lancer les services dockers nécessaires :
```bash
  docker compose run db -d
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

## 🧪 Tests

Lancer tous les tests:
```bash 
  poetry run pytest
```

Les tests incluent la connexion à la base de données et le bon fonctionnement des utilitaires ETL.
