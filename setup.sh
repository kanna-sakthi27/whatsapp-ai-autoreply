#!/bin/bash
# ============================================
# WhatsApp AI Auto-Reply - Setup Script
# ============================================
# One-command setup: copies .env, creates dirs,
# pulls images, starts services, shows credentials.

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
echo "[1/5] ✓ Created .env file from .env.example"
echo "    Edit .env with your configuration before running."
else
echo "[1/5] ✓ .env file already exists"
fi

# --- Step 2: Create directories ---
mkdir -p waha_sessions waha_media
mkdir -p ollama_data
echo "[2/5] ✓ Created data directories"

# --- Step 3: Check Docker ---
if command -v docker &> /dev/null; then
echo "[3/5] ✓ Docker is installed"
docker --version
else
echo "[3/5] ✗ Docker is not installed"
echo "    Please install Docker first:"
echo "    https://docs.docker.com/engine/install/"
echo "    After installing, run this script again."
exit 1
fi

# --- Step 4: Pull WAHA image ---
echo "[4/5] Pulling WAHA Docker image..."
docker pull devlikeapro/waha:latest
echo "[4/5] ✓ WAHA image pulled"

echo "[5/5] Starting all services..."
docker compose up -d

echo ""
echo "Waiting for WAHA container to initialize (30s)..."
sleep 30

echo ""
echo "============================================"
echo "  Setup Complete! All Services Running!"
echo "============================================"
echo ""

echo "=== WAHA Dashboard Credentials ==="
echo "(checking container logs for credentials...)"
echo ""
docker compose logs waha 2>/dev/null | grep -i "credential\|login\|user\|password" || echo "  Default credentials: admin / your WAHA_API_KEY"
echo ""
echo "WAHA_DASHBOARD_URL : http://localhost:3000/dashboard"
echo "FRONTEND_URL       : http://localhost:8080"
echo "AI_SERVICE_API_URL : http://localhost:8000"
echo ""
echo "--- Available Commands ---"
echo "View all logs:    docker compose logs -f"
echo "View WAHA logs:   docker compose logs waha"
echo "View AI logs:     docker compose logs ai-service"
echo "View Frontend:    docker compose logs frontend"
echo "Stop services:    docker compose down"
echo "Restart:          docker compose restart"
echo ""
echo "First-time setup: Open http://localhost:3000/dashboard"
echo "Scan QR code with WhatsApp > Linked Devices > Link a Device"
echo ""
