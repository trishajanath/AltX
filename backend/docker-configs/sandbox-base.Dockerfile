# =============================================================================
# SANDBOX BASE IMAGE - Pre-built with all dependencies
# =============================================================================
# Build this image ONCE and reuse for all sandboxes:
#   docker build -f sandbox-base.Dockerfile -t altx-sandbox-base:latest .
#
# This dramatically speeds up sandbox creation by:
# - Pre-installing all Python packages (~30-60 seconds saved)
# - Pre-installing system dependencies (~10-20 seconds saved)
# - Caching the base layer for instant reuse
# =============================================================================

FROM python:3.11-slim AS base

# Set environment variables for faster, deterministic builds
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONPATH=/app

# Default sandbox configuration
ENV SANDBOX=true \
    DATABASE_URL=sqlite:///./data/sandbox.db \
    JWT_SECRET=sandbox-dev-secret-change-in-production

# Set working directory
WORKDIR /app

# Install system dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Pre-install ALL sandbox dependencies (the slow part)
# This layer is cached and reused for all sandbox builds
RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    pydantic>=2.0.0 \
    email-validator>=2.0.0 \
    sqlalchemy>=2.0.0 \
    aiosqlite>=0.19.0 \
    python-jose[cryptography]>=3.3.0 \
    passlib[bcrypt]>=1.7.4 \
    bcrypt>=4.0.0 \
    python-multipart>=0.0.6 \
    httpx>=0.25.0

# Create data directory for SQLite
RUN mkdir -p /app/data

# Pre-create __pycache__ to avoid permission issues
RUN mkdir -p /app/__pycache__ && chmod 777 /app/__pycache__

# Expose FastAPI port
EXPOSE 8000

# Label for identification
LABEL maintainer="AltX" \
      description="Pre-built base image for fast sandbox deployment" \
      version="1.0"
