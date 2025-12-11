# ETL Pipeline Python

Cette partie du projet contient le pipeline ETL pour traiter et insérer des données dans la base PostgreSQL.

---

## 🐍 Prérequis

- Python 3.10 à 3.12
- [Poetry](https://python-poetry.org/) pour gérer les dépendances et l'environnement
- Docker
---

## 1. 📦 Installation du projet

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

### 1.1 ⚙️ Configuration des variables d'environnement

1. Copier le fichier d'environnement à la racine du projet 
```bash 
   cp ../.env.exemple ../.env
```

2. Lancer les services dockers nécessaires :
```bash
  docker compose run db -d
```

***


## 2. 🧩 Système de Workflows ETL 

Ce module permet de définir, exécuter et superviser des workflows / pipelines ETL composés de plusieurs étapes de traitement chaînées.
Chaque workflow est une suite de fonctions qui reçoivent et retournent un objet de contexte typé contenant les données manipulées tout au long du pipeline.

Les pipelines sont définis dans un fichier YAML **pipelines.yaml**: 
```yaml
load-vessels:
  - func: extract_data_from_file
    kwargs:
      selected_map: [ "mmsi", "base_date_time", "vessel_name", "imo", "call_sign",
        "vessel_type_id", "length", "width", "draft", "cargo_type_id","transceiver_class"]
  - func: normalize_ais
    kwargs: {}
  - func: remove_rows_with_empty
    kwargs:
      required: ["mmsi","base_date_time"]
  - func: clean_vessel_duplication
    kwargs: {}
  - func: get_vessels_db
    kwargs: {}
  - func: transform_vessel_delta
    kwargs: {}
  - func: load_vessel_to_db
    kwargs:
      table: "vessel"
      upsert_keys: ["mmsi"]
```
Chaque fonction reçoit un objet **context** (dataclass) et retourne le même **contexte** mis à jour

Le contexte est un objet servant à partager les données entre les étapes du workflow

***


## 3. 🚀 Lancer les commandes CLI avec Click

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
***

## 4. 🌐 API ETL Orchestrator
L’API repose sur FastAPI et permet de piloter le système ETL à distance via des requêtes HTTP.
Elle expose des endpoints pour :
- exécuter les commandes CLI Click,
- exécuter ou lister les pipelines ETL,
- suivre l’état des tâches en cours,
- consulter les logs,
- et gérer les clés d’API pour l’authentification.

Lancer le serveur en local (Attention les dockers **etl-worker** et **redis** doivent être lancé)
```bash 
  poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Pour docker 
```bash
    docker compose up etl --build -d
```

Le Swagger est accessible sur : 
http://127.0.0.1:8000/docs#

La super clé API par défaut : `superapikey`
***


### 4.1 🔒 Authentification par clé d’API
Toutes les routes (sauf /health) sont protégées par une clé d’API.
Chaque requête doit inclure un en-tête HTTP :
```http request 
X-API-Key: <votre_clef_api>
```
Les clés sont créées et supprimées via les endpoints /apiKeys, accessibles uniquement aux super-utilisateurs.
- `POST /apiKeys/ → Créer une nouvelle clé d’API (superuser requis)`
- `DELETE /apiKeys/{key} → Supprimer une clé existante`

***


### 4.2 ⚙️ Commandes CLI exposées via l’API
L’API ne redéfinit pas les commandes, elle utilise directement le code Click du projet.
Cela signifie que toute commande CLI (etl-cli) est accessible à distance via HTTP.

Exemple :
```http request
POST /commands/{name}
```
```json
{
  "param1": "value",
  "flag_option": true
}
```
- Chaque commande est automatiquement analysée à partir de Click, de sorte que :
- Les paramètres sont validés dynamiquement.
- Les options de type is_flag (booléens) sont gérées automatiquement.
- Les erreurs de validation sont renvoyées sous forme de 422.

***


### 4.3 📋 Système de Tâches et de File d’Attente (Queue)
Chaque exécution de commande ou de pipeline crée une tâche enregistrée dans une file d’attente interne.
`GET /tasks/ → Liste des tâches (en cours, terminées, échouées)`

`GET /tasks/{id} → Statut détaillé d’une tâche`

`DELETE /tasks/{id} → Supprime une tâche terminée`

Cela permet :

- d’exécuter plusieurs commandes ou pipelines simultanément,
- de suivre l’état d’avancement de chaque exécution,
- de consulter les logs associés via /logs.

***

## 5. 🧪 Tests

Lancer tous les tests:
```bash 
  poetry run pytest
```

Les tests incluent la connexion à la base de données et le bon fonctionnement des utilitaires ETL.
