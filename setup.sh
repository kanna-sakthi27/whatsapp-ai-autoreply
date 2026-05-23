#!/bin/bash
# ============================================
# WhatsApp AI Auto-Reply - Setup Script
# ============================================
# This script performs initial setup for the project.
# Run it once after cloning the repository.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "============================================"
echo "  WhatsApp AI Auto-Reply - Setup"
echo "============================================"
echo ""

# --- Step 1: Copy .env if not exists ---
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[1/4] ✓ Created .env file from .env.example"
    echo "    Edit .env with your configuration before running."
else
    echo "[1/4] ✓ .env file already exists"
fi

# --- Step 2: Create directories ---
mkdir -p waha_sessions waha_media
mkdir -p ollama_data
echo "[2/4] ✓ Created data directories"

# --- Step 3: Check Docker ---
if command -v docker &> /dev/null; then
    echo "[3/4] ✓ Docker is installed"
    docker --version
else
    echo "[3/4] ✗ Docker is not installed"
    echo "    Please install Docker first:"
    echo "    https://docs.docker.com/engine/install/"
    echo "    After installing, run this script again."
    exit 1
fi

# --- Step 4: Pull WAHA image ---
echo "[4/4] Pulling WAHA Docker image..."
docker pull devlike/waha:latest
echo "[4/4] ✓ WAHA image pulled"

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Before starting, ensure you have:"
echo "  1. Edited .env with your settings"
echo "  2. Ollama running (if using local AI):"
echo "     docker run -d -p 11434:11434 --name ollama ollama/ollama"
echo "     docker exec ollama ollama pull llama3.2:1b"
echo ""
echo "Start the services:"
echo "  docker compose up -d"
echo ""
echo "View logs:"
echo "  docker compose logs -f"
echo ""
echo "Scan QR code (first time only):"
echo "  docker logs waha-whatsapp"
echo "  # Look for the QR code URL or scan in terminal"
echo ""
