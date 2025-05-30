#!/bin/bash

# Start development environment script

echo "🚀 Starting Medical Terminology Mapper Development Environment..."

# Get the directory where the script is located (now in root)
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to project directory
cd "$PROJECT_DIR"

# Check if .env exists, if not copy from example
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Stop any running containers
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans

# Remove old containers and volumes for clean start
echo "🧹 Cleaning up old containers..."
docker-compose rm -f

# Build and start services
echo "🔨 Building services..."
docker-compose build

echo "🎬 Starting services..."
docker-compose up -d

# Wait for services to be ready with retry logic
echo "⏳ Waiting for services to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
API_READY=false
FRONTEND_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$API_READY" = false ]; do
    sleep 2
    API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null || echo "000")
    if [ "$API_HEALTH" = "200" ]; then
        API_READY=true
        echo "✅ API is running at http://localhost:8000"
        echo "📚 API documentation available at http://localhost:8000/docs"
    else
        echo -n "."
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

if [ "$API_READY" = false ]; then
    echo ""
    echo "⚠️  API failed to start. Check logs with: docker-compose logs api"
fi

# Check frontend
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ] || [ "$FRONTEND_HEALTH" = "304" ]; then
    FRONTEND_READY=true
    echo "✅ Frontend is running at http://localhost:3000"
fi

# Open browser tabs if services are ready
if [ "$API_READY" = true ] || [ "$FRONTEND_READY" = true ]; then
    echo ""
    echo "🌐 Opening browser tabs..."
    
    # Detect the operating system and open browser accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if [ "$FRONTEND_READY" = true ]; then
            open "http://localhost:3000" &
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v xdg-open > /dev/null; then
            if [ "$FRONTEND_READY" = true ]; then
                xdg-open "http://localhost:3000" &
            fi
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        if [ "$FRONTEND_READY" = true ]; then
            start "http://localhost:3000" &
        fi
    fi
fi

echo ""
echo "📋 Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: ./stop-dev.sh"
echo "  - Rebuild: docker-compose build --no-cache"
echo "  - Shell into API: docker-compose exec api bash"
echo "  - Shell into Frontend: docker-compose exec frontend sh"
echo ""

if [ "$API_READY" = true ] && [ "$FRONTEND_READY" = true ]; then
    echo "🎉 Development environment is ready!"
else
    echo "⚠️  Some services may still be starting. Check logs for details."
fi

# Tail logs for monitoring
echo ""
echo "📜 Showing logs (Ctrl+C to exit)..."
echo "========================================="
docker-compose logs -f --tail=50