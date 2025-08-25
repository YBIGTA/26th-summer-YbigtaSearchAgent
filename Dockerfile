# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_SYSTEM_PYTHON=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy dependency files
COPY requirements-minimal.txt ./
COPY pyproject.toml ./

# Install minimal Python dependencies with UV (much faster than pip)
RUN uv pip install --system -r requirements-minimal.txt

# Copy source code
COPY src/ ./src/
COPY .env.example ./.env

# Create necessary directories
RUN mkdir -p data/db data/cache data/indexes data/audio

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["python", "src/backend/main.py"]