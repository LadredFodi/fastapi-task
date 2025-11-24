FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.7.1

COPY pyproject.toml ./
COPY poetry.lock* ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi || \
    poetry install --no-interaction --no-ansi

COPY . .