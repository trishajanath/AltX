# =============================================================================
# FAST SANDBOX DOCKERFILE - Uses pre-built base image
# =============================================================================
# OPTIMAL: Build the base image first (one-time setup):
#   docker build -f sandbox-base.Dockerfile -t altx-sandbox-base:latest .
#
# When using pre-built base: Build time ~2-5 seconds (deps pre-installed)
# When using fallback: Build time ~30-60 seconds (deps installed on build)
# =============================================================================

# Try to use pre-built base, fallback to python:3.11-slim if not available
ARG BASE_IMAGE=altx-sandbox-base:latest
FROM ${BASE_IMAGE}

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SANDBOX=true \
    DATABASE_URL=sqlite:///./data/sandbox.db

WORKDIR /app

# Copy all files first (requirements may or may not exist)
COPY . .

# Install dependencies if not using base image (checks if uvicorn exists)
# Also install curl for healthcheck if not present
# Uses requirements.txt if exists, otherwise installs minimal deps inline
RUN python -c "import uvicorn" 2>/dev/null || \
    (apt-get update && apt-get install -y --no-install-recommends curl && \
     rm -rf /var/lib/apt/lists/* && \
     if [ -f sandbox_requirements.txt ]; then \
       pip install --no-cache-dir -r sandbox_requirements.txt; \
     elif [ -f requirements.txt ]; then \
       pip install --no-cache-dir -r requirements.txt; \
     else \
       pip install --no-cache-dir fastapi uvicorn[standard] pydantic sqlalchemy python-jose[cryptography] passlib[bcrypt] python-multipart; \
     fi)

# Create data directory if not exists
RUN mkdir -p /app/data

# Expose FastAPI port
EXPOSE 8000

# Faster health check - start checking sooner, fail faster
HEALTHCHECK --interval=5s --timeout=3s --start-period=3s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn - optimized for fast startup
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
