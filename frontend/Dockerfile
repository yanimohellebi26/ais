# Multi-stage build: build Vite React app, then serve with Apache httpd

# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# Runtime stage
FROM httpd:2.4-alpine
# Copy Apache configuration with SPA fallback
COPY ./httpd.conf /usr/local/apache2/conf/httpd.conf
# Copy built static files
COPY --from=build /app/dist/ /usr/local/apache2/htdocs/
