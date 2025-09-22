# AIS - Stack Docker/Compose

Ce projet contient trois composants:
- frontend (Vite + React)
- backend (Spring Boot 3, Java 17)
- etl (Python)

Tous les services peuvent être lancés avec Docker Compose.

## Prérequis
- Docker et Docker Compose installés

## Lancement rapide

Depuis la racine du projet (Pour forcer le build)

```bash
docker compose up --build
```

Pour lancer les dockers en environnement de dev :
```bash
docker compose up -d
```

Services exposés:
- Frontend: http://localhost/
- Backend: http://localhost:8080/
- Base de données PostGIS  http://localhost:5432 (user: postgres, mdp: postgres, db: ais)
- PgAdmin : http://localhost:5050 (user: admin@local.dev, mdp: admin).

L'ETL s'exécute via le conteneur `ais-etl` avec la commande par défaut `python -m etl.main`.

## Structure des images
- frontend: construit l'app Vite et la sert avec Nginx (port 80)
- backend: construit le jar Spring Boot via Maven (port 8080)
- etl: image Python 3.12 exécutant le module `etl.main`
- db: Postgres 16 + PostGIS avec volume persistant `db_data`

## Commandes utiles
- Recompiler sans cache: `docker compose build --no-cache`
- Lancer en arrière-plan: `docker compose up -d`
- Arrêter: `docker compose down`

## Notes
- Aucun lien direct n'est configuré entre le backend et la base de données par défaut; adaptez `application.properties` si nécessaire.
- Vous pouvez modifier les variables d'environnement de la base de données dans `docker-compose.yml`.
