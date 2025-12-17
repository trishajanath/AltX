#!/bin/bash
set -e

echo "🚀 Starting XVERTA backend server..."

# Optimal workers depending on ECS CPU
# Default: 5 workers (good for 2 vCPU)
WORKERS=${WORKERS:-5}

echo "📊 Starting with $WORKERS workers"

exec gunicorn main:app \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 600 \
    --graceful-timeout 60 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile - \
    --log-level info
