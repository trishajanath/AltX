# Lightweight Dockerfile for AI-generated FastAPI sandbox backends
# Optimized for fast builds and minimal dependencies

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Default sandbox configuration
ENV SANDBOX=true \
    DATABASE_URL=sqlite:///./sandbox.db \
    JWT_SECRET=sandbox-dev-secret-change-in-production

# Set working directory
WORKDIR /app

# Install minimal system dependencies (no heavy packages for sandbox)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy and install minimal requirements for sandbox
COPY sandbox_requirements.txt .
RUN pip install --no-cache-dir -r sandbox_requirements.txt

# Copy the application code
COPY . .

# Create directory for SQLite database
RUN mkdir -p /app/data

# Expose FastAPI port
EXPOSE 8000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run FastAPI with uvicorn
CMD ["python", "-m", "uvicorn", "sandbox_main:app", "--host", "0.0.0.0", "--port", "8000"]
