#!/bin/bash

# ===========================================
# Poker MTT Helper - Deployment Script
# ===========================================
# Usage: ./deploy.sh [dev|prod|status|logs|backup|stop]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODE=${1:-dev}

echo "🎰 Poker MTT Helper Deployment"
echo "================================"
echo "Mode: $MODE"
echo ""

# ===========================================
# Check Docker
# ===========================================
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

# Use docker compose v2 if available
if docker compose version &> /dev/null; then
    COMPOSE="docker compose"
else
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed"
        exit 1
    fi
    COMPOSE="docker-compose"
fi

# ===========================================
# Load environment variables
# ===========================================
load_env() {
    if [ -f ".env.production" ]; then
        echo "📋 Loading .env.production"
        set -a
        source .env.production
        set +a
    elif [ -f "env.example" ] && [ "$MODE" = "prod" ]; then
        echo "⚠️  .env.production not found. Copy from env.example:"
        echo "   cp env.example .env.production"
        echo "   nano .env.production"
        exit 1
    fi
}

# ===========================================
# Commands
# ===========================================
case "$MODE" in
    dev)
        echo "🔧 Starting development environment..."
        
        $COMPOSE up -d
        
        echo ""
        echo "✅ Development environment ready!"
        echo ""
        echo "Services:"
        echo "  - Frontend: http://localhost:5173"
        echo "  - Backend API: http://localhost:8000"
        echo "  - API Docs: http://localhost:8000/docs"
        echo "  - Training: http://localhost:5173/training"
        echo "  - PostgreSQL: localhost:5432"
        echo "  - Redis: localhost:6379"
        ;;
        
    prod)
        load_env
        
        echo "📦 Building production images..."
        
        # Check for SSL certificates
        if [ ! -f "nginx/ssl/fullchain.pem" ]; then
            echo "⚠️  SSL certificates not found in nginx/ssl/"
            echo "   Run ./scripts/ssl-setup.sh your-domain.com first"
            echo "   Or continue without HTTPS (not recommended)"
            read -p "Continue without HTTPS? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            # Use HTTP-only nginx config
            cp nginx/nginx.conf nginx/nginx.prod.conf.bak
            cat nginx/nginx.conf > nginx/nginx.prod.conf
        fi
        
        # Build images
        $COMPOSE -f docker-compose.prod.yml build
        
        echo "🚀 Starting production services..."
        $COMPOSE -f docker-compose.prod.yml up -d
        
        # Wait for services to be healthy
        echo "⏳ Waiting for services to be healthy..."
        sleep 10
        
        # Check health
        if curl -sf http://localhost/health > /dev/null 2>&1; then
            echo "✅ Health check passed"
        else
            echo "⚠️  Health check failed - services may still be starting"
        fi
        
        echo ""
        echo "✅ Production deployment complete!"
        echo ""
        echo "Services:"
        if [ -f "nginx/ssl/fullchain.pem" ]; then
            echo "  - Frontend: https://${DOMAIN:-localhost}"
            echo "  - API: https://${DOMAIN:-localhost}/api"
            echo "  - WebSocket: wss://${DOMAIN:-localhost}/ws/analyze"
        else
            echo "  - Frontend: http://localhost"
            echo "  - API: http://localhost/api"
            echo "  - WebSocket: ws://localhost/ws/analyze"
        fi
        echo ""
        echo "Useful commands:"
        echo "  ./deploy.sh logs    - View logs"
        echo "  ./deploy.sh status  - Service status"
        echo "  ./deploy.sh backup  - Create backup"
        echo "  ./deploy.sh stop    - Stop services"
        ;;
        
    status)
        echo "📊 Service Status"
        echo ""
        $COMPOSE -f docker-compose.prod.yml ps 2>/dev/null || $COMPOSE ps
        ;;
        
    logs)
        SERVICE=${2:-}
        if [ -n "$SERVICE" ]; then
            $COMPOSE -f docker-compose.prod.yml logs -f "$SERVICE" 2>/dev/null || \
            $COMPOSE logs -f "$SERVICE"
        else
            $COMPOSE -f docker-compose.prod.yml logs -f 2>/dev/null || \
            $COMPOSE logs -f
        fi
        ;;
        
    backup)
        echo "🗄️ Creating backup..."
        ./scripts/backup.sh
        ;;
        
    stop)
        echo "⏹️ Stopping services..."
        $COMPOSE -f docker-compose.prod.yml down 2>/dev/null || $COMPOSE down
        echo "✅ Services stopped"
        ;;
        
    restart)
        echo "🔄 Restarting services..."
        $COMPOSE -f docker-compose.prod.yml restart 2>/dev/null || $COMPOSE restart
        echo "✅ Services restarted"
        ;;
        
    update)
        echo "📥 Updating application..."
        git pull
        $COMPOSE -f docker-compose.prod.yml build
        $COMPOSE -f docker-compose.prod.yml up -d
        echo "✅ Update complete"
        ;;
        
    *)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  dev      - Start development environment"
        echo "  prod     - Deploy production"
        echo "  status   - Show service status"
        echo "  logs     - View logs (optionally: logs <service>)"
        echo "  backup   - Create database backup"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  update   - Pull updates and redeploy"
        exit 1
        ;;
esac

echo ""
echo "📋 View logs: $COMPOSE logs -f"
echo "🛑 Stop: ./deploy.sh stop"
