#!/bin/bash

# Health check script for services

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🏥 Checking service health..."
echo ""

# Check Docker daemon
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker daemon is running"
else
    echo -e "${RED}✗${NC} Docker daemon is not running"
    exit 1
fi

# Check if containers are running
API_CONTAINER=$(docker-compose ps -q api 2>/dev/null)
FRONTEND_CONTAINER=$(docker-compose ps -q frontend 2>/dev/null)

if [ -n "$API_CONTAINER" ]; then
    API_STATUS=$(docker inspect -f '{{.State.Running}}' "$API_CONTAINER" 2>/dev/null)
    if [ "$API_STATUS" = "true" ]; then
        echo -e "${GREEN}✓${NC} API container is running"
        
        # Check API health endpoint
        API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null || echo "000")
        if [ "$API_HEALTH" = "200" ]; then
            echo -e "${GREEN}✓${NC} API health check passed"
        else
            echo -e "${YELLOW}⚠${NC} API health check failed (HTTP $API_HEALTH)"
        fi
    else
        echo -e "${RED}✗${NC} API container is not running"
    fi
else
    echo -e "${RED}✗${NC} API container not found"
fi

if [ -n "$FRONTEND_CONTAINER" ]; then
    FRONTEND_STATUS=$(docker inspect -f '{{.State.Running}}' "$FRONTEND_CONTAINER" 2>/dev/null)
    if [ "$FRONTEND_STATUS" = "true" ]; then
        echo -e "${GREEN}✓${NC} Frontend container is running"
        
        # Check frontend accessibility
        FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
        if [ "$FRONTEND_HEALTH" = "200" ] || [ "$FRONTEND_HEALTH" = "304" ]; then
            echo -e "${GREEN}✓${NC} Frontend is accessible"
        else
            echo -e "${YELLOW}⚠${NC} Frontend not accessible (HTTP $FRONTEND_HEALTH)"
        fi
    else
        echo -e "${RED}✗${NC} Frontend container is not running"
    fi
else
    echo -e "${RED}✗${NC} Frontend container not found"
fi

# Check port availability
echo ""
echo "📡 Port status:"
for port in 3000 8000; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Port $port is in use"
    else
        echo -e "${YELLOW}⚠${NC} Port $port is not in use"
    fi
done

# Show container logs if requested
if [ "$1" = "--logs" ]; then
    echo ""
    echo "📜 Recent logs:"
    echo "========================================="
    docker-compose logs --tail=20
fi

echo ""
echo "💡 Use './check-health.sh --logs' to see recent container logs"