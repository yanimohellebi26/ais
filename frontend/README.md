# Frontend React + Vite

Salut à tous,

Voici le frontend de notre projet, développé avec React et Vite. Ce setup nous permet de bénéficier d'un rechargement à chaud (HMR) pour un développement rapide, ainsi que d'une configuration ESLint de base pour garder un code propre.

## C'est quoi ce projet ?

Ce dossier contient toute la partie interface utilisateur de notre application. On utilise React pour construire les composants et Vite pour le bundling et le serveur de développement.

## Comment lancer le projet ?

Pour démarrer le frontend en local :

1. Placez-vous dans ce dossier (`frontend`).
2. Installez les dépendances :
   ```bash
   npm install
   ```
3. Lancez le serveur de développement :
   ```bash
   npm run dev
   ```
4. Ouvrez votre navigateur à l'adresse indiquée dans le terminal (en général http://localhost:5173).

## Plugins utilisés

On utilise principalement deux plugins React pour Vite :
- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) (Babel)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) (SWC)

