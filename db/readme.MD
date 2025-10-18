# 📘 Utilisation de PostgreSQL dans Docker

Ce projet utilise **PostgreSQL** dans un conteneur Docker `(ais-db)` et met à disposition des scripts pour se connecter facilement ou exécuter des fichiers SQL.

Nous utilisons également **Flyway** pour gérer les migrations de la base de données.

## 🚀 Flyway

Flyway est un outil de gestion de migrations de base de données. Il permet de :

- Versionner la structure et les modifications de la base (tables, colonnes, contraintes…) via des scripts **SQL**.

- Appliquer automatiquement les migrations manquantes sur une base de **développement**, **test** ou **production**.

- Suivre l’historique des migrations directement dans la base grâce à la table `flyway_schema_history`.

- Garantir que toutes les bases de différents environnements sont synchronisées.

## ⚡ Comment utiliser Flyway

### 1. Placez vos scripts de migration SQL dans le dossier `./db/migrations` :
```bash
    V1__init.sql
    V2__UC-12_add_ship_table.sql
```

### 2.  Pour appliquer les migrations :

- Avec Docker Compose :
```bash 
  docker-compose run --rm flyway
```
- Avec Flyway CLI sur votre machine :
```bash 
    flyway -url=jdbc:postgresql://localhost:5432/ais \
    -user=postgres \
    -password=postgres migrate
```

### 3. Pour vérifier quelles migrations ont été appliquées :

```bash 
  docker-compose run --rm flyway info
```

ou
```bash 
  flyway info
```

## 🧪 Tester les migrations en local

1. Créez un nouveau fichier **SQL** dans `./db/migrations` pour chaque changement que vous voulez tester, **avec un nouveau numéro de version**.

2. Appliquez la migration avec **Flyway** `(docker-compose run --rm flyway`).

3. Vérifiez l’état avec `flyway info`.

4. Si tout est correct, les migrations peuvent être merged et appliquées sur d’autres environnements.

 💡 **Astuce** : Pas besoin de relancer le **backend** ou l’**ETL** pour tester une migration. **Flyway** s’occupe de tout.

## 📝 Nommer les migrations

- Le nom des fichiers de migration doit respecter le format **Flyway** :
```bash
  V<version>__<description>.sql
```

- Pour les tickets, incluez le **numéro du ticket** dans le nom pour plus de lisibilité :
```bash 
    V3__UC-12_add_ship_table.sql
    V4__UC-15_add_position_column.sql 
```

## 💡 Bonnes pratiques pour les scripts SQL

**Les migrations Flyway doivent uniquement contenir des commandes DDL et DML nécessaires pour faire évoluer la base.**

Pour des scripts utiles uniquement pour exécuter des requêtes (INSERT, UPDATE, SELECT, etc.) :

- Placez-les dans un dossier à part si besoin.

- Ne modifiez pas la structure de la base via ces scripts, ils servent uniquement à tester ou insérer des données.

## 🔌 Connexion au shell PostgreSQL (psql) depuis un shell
### Windows (PowerShell)
```bash
    .\connect-db.ps1
```

### Linux / MacOS
```bash
  ./connect-db.sh
```

Les deux ouvrent un terminal `psql` connecté à la base `ais` avec l’utilisateur `postgres`.
Pour exécuter une requête SQL, terminez toujours par un `;`.

## 📂 Exécution d’un fichier SQL
### Windows (PowerShell)
```bash 
  .\exec-sql.ps1 mon_script.sql
```

### Linux / MacOS
```bash 
  ./exec-sql.sh mon_script.sql
```

### 🛠 Commandes utiles dans le shell psql

`\dt public.*` → Lister toutes les tables (public) de la base courante (ais)

`\l` → Lister toutes les bases de données

`\c <dbname>` → Se connecter à une autre base

`\d <table>` → Afficher le schéma d’une table

`\q` → Quitter le shell psql

`SELECT NOW();` → Exemple de requête SQL (retourne la date courante)