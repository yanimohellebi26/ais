# AIS - Stack Docker/Compose

Stack 
- frontend (Vite + React)
- backend (Spring Boot 3, Java 17)
- etl (Python)

Tous les services peuvent être lancés avec Docker Compose.

## Prérequis
- Docker et Docker Compose installés

## Lancement rapide

Depuis la racine du projet (Pour forcer le build)

```bash
docker compose up --build -d
```

Pour lancer les dockers en environnement de dev :
```bash
docker compose up -d
```

Services exposés:
- Frontend: http://localhost:5173
- Backend: http://localhost:8080/
- Base de données PostGIS  http://localhost:5432 (user: postgres, mdp: postgres, db: ais)
- PgAdmin : http://localhost:5050 (user: admin@local.dev, mdp: admin).
- ETL éxution en local directement depuis un environnement poetry

## Structure des images
- frontend: construit l'app Vite et la sert avec Nginx (port 80)
- backend: construit le jar Spring Boot via Maven (port 8080)
- etl: image Python 3.12 exécutant le module `etl.cli`
- db: Postgres 16 + PostGIS avec volume persistant `db_data`

## Commandes utiles
- Recompiler sans cache: `docker compose build --no-cache`
- Lancer en arrière-plan: `docker compose up -d`
- Arrêter: `docker compose down`
- Arrêter et supprimer les volumes: `docker compose down -v`

