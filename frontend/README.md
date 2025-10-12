# Frontend React + Vite

Interface SeaSight AIS construite avec React, Vite et React Router.

## Configuration des variables d'environnement

1. Copiez le fichier `.env.example` vers l'environnement souhaité :

   ```bash
   cp .env.example .env.development
   ```

2. Ajustez la valeur de `VITE_API_URL` si l'API ne tourne pas sur `http://localhost:8080`.

Le bundle utilise `import.meta.env.VITE_API_URL` pour toutes les requêtes HTTP (login, register, etc.).

## Lancer en développement

```bash
npm install
npm run dev
```

Le serveur Vite démarre en général sur <http://localhost:5173>.

## Build Docker

```bash
docker build -t seasight-frontend .
docker run --rm -p 8081:80 --env-file .env.production seasight-frontend
```

- L'image est construite en Node 20 (phase build) puis servie via Nginx.
- La configuration Nginx inclut un fallback SPA (`try_files $uri /index.html`).
- Pensez à créer un fichier `.env.production` (par exemple via `cp .env.example .env.production`) avant de lancer le conteneur.

## Structure rapide

- `src/Pages` contient les écrans principaux (Home, Login, Register, pages par rôle).
- `src/components/BaseComponents` rassemble les composants UI partagés.
- `Dockerfile` permet de builder et servir la version statique.

## Scripts utiles

- `npm run dev` : mode développement
- `npm run build` : build de production (output `dist/`)
- `npm run preview` : prévisualisation du build
- `npm run lint` : linting ESlint

