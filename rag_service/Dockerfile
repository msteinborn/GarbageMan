FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock* ./
RUN pip install uv && uv sync --frozen

# Copy application
COPY . .

# Run service
CMD ["uv", "run", "main.py"]
