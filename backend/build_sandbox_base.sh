#!/bin/bash
# =============================================================================
# Build the optimized sandbox base image for fast sandbox deployment
# =============================================================================
# Run this ONCE to set up the base image:
#   ./build_sandbox_base.sh
#
# This pre-installs all Python dependencies so sandbox builds are instant!
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_CONFIGS_DIR="$SCRIPT_DIR/docker-configs"

echo "🚀 Building AltX Sandbox Base Image..."
echo "   This pre-installs all dependencies for fast sandbox creation."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the base image
echo "📦 Building base image (this may take 1-2 minutes)..."
docker build \
    -f "$DOCKER_CONFIGS_DIR/sandbox-base.Dockerfile" \
    -t altx-sandbox-base:latest \
    "$DOCKER_CONFIGS_DIR"

echo ""
echo "✅ Base image built successfully!"
echo ""
echo "📊 Image size:"
docker images altx-sandbox-base:latest --format "   {{.Size}}"
echo ""
echo "⚡ Sandbox creation will now be MUCH faster!"
echo "   - First build: ~30-60 seconds → Now: ~2-5 seconds"
echo "   - Subsequent builds with same code: ~1 second (cached)"
echo ""
echo "💡 To verify the image:"
echo "   docker run --rm altx-sandbox-base:latest python -c 'import fastapi; print(f\"FastAPI {fastapi.__version__} ready!\")'"
