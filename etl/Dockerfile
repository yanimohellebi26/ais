# docker/ Dockerfile
FROM python:3.11-slim

# Installer poetry
RUN pip install --no-cache-dir poetry

# Copier le projet
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root  # install deps sans installer le package

COPY etl/ /app/etl/

# Entrypoint pour lancer le pipeline
ENTRYPOINT ["poetry", "run", "python", "-m", "etl.main"]
