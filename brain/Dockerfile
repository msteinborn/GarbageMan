FROM ghcr.io/astral-sh/uv:python3.11-alpine

WORKDIR /app

# Enable bytecode compilation and optimized linking
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1

# 1. Copy the workspace-level project files
COPY pyproject.toml ./

# 2. Copy the specific service files (paths are relative to build context: root)
COPY brain/pyproject.toml ./brain/

# 3. Install only the brain package dependencies
RUN uv sync --no-dev --package brain

# 4. Copy the actual source code
COPY brain/ ./brain/

# Expose web server port
EXPOSE 8001

# Move into the service directory to run
WORKDIR /app/brain

# Start the web server instead of CLI
CMD ["uv", "run", "ui/web_server.py"]