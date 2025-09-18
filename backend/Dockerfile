# Étape de build multi-stage pour le backend Spring Boot
FROM maven:3.9.9-eclipse-temurin-17 AS build
WORKDIR /app
# Copie du fichier pom.xml pour gérer les dépendances Maven
COPY pom.xml .
# Pré-téléchargement des dépendances pour accélérer les builds suivants
RUN mvn -B -e -DskipTests dependency:go-offline || true
# Copie du code source de l'application
COPY src ./src
# Construction du jar sans exécuter les tests
RUN mvn -B -DskipTests package

# Étape d'exécution avec une image JRE légère
FROM eclipse-temurin:17-jre
WORKDIR /app
# Variable d'environnement pour personnaliser les options JVM
ENV JAVA_OPTS=""
# Copie du jar généré lors de l'étape de build
COPY --from=build /app/target/*.jar /app/app.jar
# Exposition du port 8080 (par défaut pour Spring Boot)
EXPOSE 8080
# Commande de lancement de l'application Spring Boot
ENTRYPOINT ["sh","-c","java $JAVA_OPTS -jar /app/app.jar"]
