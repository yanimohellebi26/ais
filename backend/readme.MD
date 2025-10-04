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


## Authentication

### Endpoint `POST /api/v1/auth/register`

- **Payload**
    ```json
    {
        "username": "captain_john",
        "email": "john.doe@example.com",
        "password": "StrongPass1!",
        "role": "captain"
    }
    ```
- **Response – 201 CREATED**
    ```json
    {
        "id": 42,
        "username": "captain_john",
        "email": "john.doe@example.com",
        "role": "captain"
    }
    ```
- **Validation règles clés**
    - `username` obligatoire, max 50 caractères, unique
    - `email` format valide, unique
    - `password` ≥ 8 caractères et doit contenir : 1 majuscule, 1 minuscule, 1 chiffre, 1 caractère spécial
    - `role` doit exister parmi `admin`, `owner`, `captain`, `maritime_expert`, `financial_analyst`
- **Sécurité** : mot de passe hashé via `BCryptPasswordEncoder`

### Tests

```bash
./mvnw test
```

Utilise une base H2 en mémoire configurée dans `src/test/resources/application.properties`.


## Dev sur le backend :
- Pendant le développement lancé simplement l'application spring en local (pas en conteneur)
- Lancer uniquement le container de la base de donné (docker compose up db -d)'