#!/bin/bash
# Solarware Development Bootstrap Script

set -e

echo "🌞 Solarware Development Setup"
echo "==============================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Install via Docker Desktop or manually."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.template .env
    echo "✅ .env created. Edit as needed."
else
    echo "✅ .env already exists"
fi

echo ""
echo "📦 Starting services with docker-compose..."
echo ""

# Start services
docker-compose up -d

echo ""
echo "✅ Services started!"
echo ""
echo "📋 Next steps:"
echo "   1. Backend API: http://localhost:8000"
echo "   2. Frontend: http://localhost:3000 (or http://localhost:5173)"
echo "   3. API Docs: http://localhost:8000/docs"
echo "   4. Database: localhost:5432 (user: solarware, password: solarware_dev_password)"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f backend"
echo "   docker-compose logs -f frontend"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
echo "💡 To run tests:"
echo "   docker-compose exec backend pytest"
echo ""
