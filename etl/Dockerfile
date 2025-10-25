FROM python:3.12-slim

# Install Poetry
RUN pip install --no-cache-dir poetry

WORKDIR /app
ENV PYTHONPATH=/app

# Copy project files
COPY pyproject.toml poetry.lock README.md ./
COPY etl/ ./etl/
COPY api/ ./api/
COPY pipelines.yaml ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction --no-ansi

EXPOSE 8000

# Entrypoint FastAPI
# Can be change to gunicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

