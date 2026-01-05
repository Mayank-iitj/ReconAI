#!/bin/bash

# SmartRecon-AI Quick Setup Script

set -e

echo "=========================================="
echo "SmartRecon-AI - Quick Setup"
echo "=========================================="
echo ""

# Check prerequisites
echo "[1/8] Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }
echo "✓ Prerequisites met"
echo ""

# Create environment file
echo "[2/8] Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
    echo "⚠️  IMPORTANT: Edit .env and set your API keys and passwords!"
    echo ""
    read -p "Press Enter to continue after editing .env..."
else
    echo "✓ .env file already exists"
fi
echo ""

# Create required directories
echo "[3/8] Creating directories..."
mkdir -p storage reports logs
chmod 755 storage reports logs
echo "✓ Directories created"
echo ""

# Build recon tools image
echo "[4/8] Building recon tools container..."
docker build -t smartrecon/tools:latest -f docker/tools/Dockerfile docker/tools/
echo "✓ Recon tools container built"
echo ""

# Build application containers
echo "[5/8] Building application containers..."
docker-compose build
echo "✓ Application containers built"
echo ""

# Start services
echo "[6/8] Starting services..."
docker-compose up -d
echo "✓ Services started"
echo ""

# Wait for database
echo "[7/8] Waiting for database to be ready..."
sleep 10
docker-compose exec -T db pg_isready -U smartrecon || sleep 5
echo "✓ Database ready"
echo ""

# Run database migrations
echo "[8/8] Running database migrations..."
docker-compose exec -T api alembic upgrade head
echo "✓ Database migrated"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Services are now running:"
echo "  • Frontend:    http://localhost:3000"
echo "  • API:         http://localhost:8000"
echo "  • API Docs:    http://localhost:8000/docs"
echo "  • Flower:      http://localhost:5555"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: (check your .env file)"
echo ""
echo "Useful commands:"
echo "  • View logs:        docker-compose logs -f"
echo "  • Stop services:    docker-compose down"
echo "  • Restart:          docker-compose restart"
echo ""
echo "⚠️  IMPORTANT REMINDERS:"
echo "  1. Change the default admin password"
echo "  2. Set a strong JWT_SECRET in .env"
echo "  3. Configure your LLM API keys"
echo "  4. Always obtain authorization before scanning"
echo ""
echo "Happy hunting! 🎯"
