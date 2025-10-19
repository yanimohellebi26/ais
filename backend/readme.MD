# SeaSight Backend - Spring Boot

REST API for SeaSight project
Init with Spring Boot 3.x, Java 17, Maven.

---

## Prerequisite

- Java 17 
- [Maven](https://maven.apache.org/download.cgi) (installed and on PATH) Or use the mvnw.cmd (Wrapper
---

## Installation / setup

1. Copy .env in root : 
```bash
  cp ../.env.exemple ../.env 
```

2. Start app in dev mode
```bash
   docker compose up backend --build -d
```

## Compiled project 
- Compiled project and generated JAR in `target/`
 ```bash
   mvn clean install 
   # or with wrapper
   ./mvnw clean install  
```
## URL Swagger UI 
http://localhost:8080/swagger-ui.html

