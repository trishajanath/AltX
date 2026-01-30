# =============================================================================
# FAST SANDBOX DOCKERFILE - Uses pre-built base image
# =============================================================================
# REQUIRES: Build the base image first (one-time setup):
#   docker build -f sandbox-base.Dockerfile -t altx-sandbox-base:latest .
#
# This Dockerfile only copies code - all deps are pre-installed in base!
# Build time: ~2-5 seconds (vs 30-60 seconds without base)
# =============================================================================

# Try to use pre-built base, fallback to python:3.11-slim if not available
ARG BASE_IMAGE=altx-sandbox-base:latest
FROM ${BASE_IMAGE} AS with-base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SANDBOX=true \
    DATABASE_URL=sqlite:///./data/sandbox.db

WORKDIR /app

# Copy application code (this is all we need - deps are in base!)
COPY . .

# Create data directory if not exists
RUN mkdir -p /app/data

# Expose FastAPI port
EXPOSE 8000

# Faster health check - start checking sooner, fail faster
HEALTHCHECK --interval=5s --timeout=3s --start-period=3s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn - optimized for fast startup
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
