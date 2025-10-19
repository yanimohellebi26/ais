# Frontend React + Vite

Interface SeaSight AIS construite avec React, Vite et React Router.

## Configuration des variables d'environnement

1. Copiez le fichier `.env.exemple` situé à la racine du projet AIS et le copier dans le même répertoire en **.env**

   ```bash
   cp ../.env.exemple ../.env
   ```

## Lancer en développement local

- Lancer le serveur web de développement via docker
```bash
   docker compose up frontend --build -d 
```

Le serveur Vite démarre en général sûr <http://localhost:5173>.

À partir de là, le site est accéssible, et se reconstruit automatiquement au moindre changement dans vos fichiers