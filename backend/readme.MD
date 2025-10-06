# SeaSight Backend - Spring Boot

REST API for SeaSight project
Init with Spring Boot 3.x, Java 17, Maven.

---

## Prerequisite

- Java 17 
- [Maven](https://maven.apache.org/download.cgi) (installed and on PATH) Or use the mvnw.cmd (Wrapper
---

## Installation / setup

1. Compiled project - Compiled project and generated JAR in `target/`
    ```bash
    mvn clean install 
    # or with wrapper
   ./mvnw clean install  
    ```

2. Start app
   ```bash
   mvn spring-boot:run
       # or with wrapper
   ./mvnw spring-boot:run 
   ```

## URL Swagger UI 
http://localhost:8080/swagger-ui.html
- Pour accéder à cette page, rentrer le compte username=admin et password=admin (voir SecurityConfig.java)


## Dev sur le backend :
- Pendant le développement lancé simplement l'application spring en local (pas en conteneur)
- Lancer uniquement le container de la base de donné (docker compose up db -d)'