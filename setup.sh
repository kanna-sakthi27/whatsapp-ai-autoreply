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
docker pull devlikeapro/waha:latest
echo "[4/4] ✓ WAHA image pulled"

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "1\) Edit your .env file with your settings:"
echo "  nano .env"
echo ""
echo "2\) Start the services:"
echo "  docker compose up -d"
echo ""
echo "3\) Get WAHA Dashboard credentials (auto-echo):"
echo "  docker compose logs waha | grep -i "credential\|login\|user\|password""
echo ""
echo "4\) Open WAHA Dashboard:"
echo "  http://localhost:3000/dashboard"
echo "  Login with the credentials shown above (default: admin / your API key)"
echo ""
echo "5\) Scan QR code (first time only):"
echo "  Open WhatsApp > Linked Devices > Link a Device > Scan the QR code"
echo ""
echo "6\) Open Frontend Dashboard:"
echo "  http://localhost:8080"
echo ""
echo "View logs anytime:"
echo "  docker compose logs -f"
echo ""
