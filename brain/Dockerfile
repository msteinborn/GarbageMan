FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv
RUN pip install uv

# Copy workspace-level project files
COPY pyproject.toml ./

# Copy all workspace members' pyproject.toml files
COPY brain/pyproject.toml ./brain/
COPY rag_service/pyproject.toml ./rag_service/

# Install only the brain package dependencies
RUN uv sync --no-dev --package brain

# Copy the actual source code
COPY brain/ ./brain/
COPY rag_service/ ./rag_service/

# Expose web server port
EXPOSE 8001

# Move into the service directory to run
WORKDIR /app/brain

# Start the web server instead of CLI
CMD ["uv", "run", "ui/web_server.py"]