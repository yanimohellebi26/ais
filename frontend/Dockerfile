# Étape de build : construction de l'application avec Node.js
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json .
COPY package.json .
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# Étape de production : déploiement de l'application avec Nginx
FROM nginx:1.27-alpine
# Suppression du site par défaut de Nginx et ajout du build de l'application
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/dist/ /usr/share/nginx/html/
# Configuration simple de Nginx adaptée à une SPA
RUN printf "server {\n  listen 80;\n  server_name _;\n  root /usr/share/nginx/html;\n  index index.html;\n  location / {\n    try_files \$uri /index.html;\n  }\n}\n" > /etc/nginx/conf.d/default.conf
EXPOSE 80
# Vérification de l'état de santé du service toutes les 30 secondes
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -qO- http://localhost:80/ || exit 1
