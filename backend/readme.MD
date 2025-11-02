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

## API key for dev purpose only :

Key can be used with X-API-KEY HTTP Header via tools
like postman/insomnia or from the swaggerUi.

| Role              | Username              | Email                         | API Key                  | Password |
|-------------------|-----------------------|-------------------------------|--------------------------|----------|
| ADMIN             | dev_ADMIN             | dev_admin@sea.com             | apikey_admin             | Sea@1234 | 
| OWNER             | dev_OWNER             | dev_owner@sea.com             | apikey_owner             | Sea@1234 |
| CAPTAIN           | dev_CAPTAIN           | dev_captain@sea.com           | apikey_captain           | Sea@1234 |
| MARITIME_EXPERT   | dev_MARITIME_EXPERT   | dev_maritime_expert@sea.com   | apikey_maritime_expert   | Sea@1234 |
| FINANCIAL_ANALYST | dev_FINANCIAL_ANALYST | dev_financial_analyst@sea.com | apikey_financial_analyst | Sea@1234 |

## URL Swagger UI 
http://localhost:8080/swagger-ui.html

