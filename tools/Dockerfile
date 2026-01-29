FROM ghcr.io/astral-sh/uv:python3.11-alpine

WORKDIR /app

# Ensure we don't use the host's virtualenv
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy root config for the workspace
COPY pyproject.toml uv.lock ./
COPY tools/pyproject.toml ./tools/

# Install dependencies for the tools package
RUN uv sync --frozen --no-dev --package tools

COPY tools/ ./tools/
WORKDIR /app/tools

# Use 'uv run' to ensure the environment is correctly activated
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]