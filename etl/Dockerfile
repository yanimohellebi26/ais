FROM python:3.12-slim

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./

COPY etl/ ./etl/

RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction --no-ansi

ENTRYPOINT ["etl-cli"]