FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install uv
RUN pip install uv

# Copy root config for the workspace
COPY pyproject.toml ./
COPY tools/pyproject.toml ./tools/
COPY rag_service/pyproject.toml ./rag_service/

# Install dependencies for the tools package
RUN uv sync --no-dev --package tools

COPY tools/ ./tools/
WORKDIR /app/tools

# Use 'uv run' to ensure the environment is correctly activated
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]