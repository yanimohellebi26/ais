# 📘 Utilisation de PostgreSQL dans Docker

Ce projet utilise **PostgreSQL** dans un conteneur Docker (`ais-db`) et met à disposition des scripts pour se connecter facilement ou exécuter des fichiers SQL.

---
Pour exécuter des requêtes SQL, le plus simple est d'aller sur **pgAdmin** : 

`Servers -> AIS -> Bases de données -> ais (clique droit) -> éditeur de requête`

## 🔌 Connexion au shell PostgreSQL (`psql`) en ligne de commande depuis un shell

### Windows (PowerShell)
Utiliser le script
```bash
  .\connect-db.ps1
```
### Linux / MacOS
Utiliser le script :

```bash
  ./connect-db.sh
```

Les deux ouvrent un terminal psql connecté directement à la base ais avec l’utilisateur postgres.

Pour éxécuter une requête SQL il faut la terminer par un `;`
## 📂 Exécution d’un fichier SQL

### Windows (PowerShell)
Utiliser le script
```bash
.\exec-sql.ps1 mon_script.sql
```
### Linux / MacOS
Utiliser le script :

```bash
.\exec-sql.ps1 mon_script.sql
```

### 🛠 Commandes utiles dans le shell psql

- `\dt public.*`	Lister toutes les tables (public) de la base courante (ais)
- `\l`	Lister toutes les bases de données
- `\c`  *dbname*	Se connecter à une autre base
- `\d` *table* Afficher le schéma d’une table
- `\q`	Quitter le shell psql
- `SELECT NOW();`	Exemple de requête SQL (retourne la date courante)