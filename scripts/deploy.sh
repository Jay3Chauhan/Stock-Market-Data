#!/bin/bash
# NSE Scraper - Deployment Script
# Run this script to deploy or update the application

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Change to project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=========================================="
echo "NSE Scraper - Deployment"
echo "=========================================="

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Run setup_oracle_vm.sh first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed. Run setup_oracle_vm.sh first."
    exit 1
fi

# Check config files
if [ ! -f "config.production.ini" ]; then
    log_error "config.production.ini not found!"
    log_info "Creating from template..."
    cp config.production.template.ini config.production.ini
    log_warn "Please edit config.production.ini with your MongoDB URI"
    exit 1
fi

if [ ! -f ".env" ]; then
    log_error ".env file not found!"
    log_info "Creating from template..."
    cp .env.template .env
    log_warn "Please edit .env with your MongoDB URI"
    exit 1
fi

# Parse command line arguments
ACTION=${1:-deploy}

case $ACTION in
    deploy)
        log_info "Deploying NSE Scraper..."
        docker-compose -f docker-compose.prod.yml up -d --build
        ;;
    update)
        log_info "Updating NSE Scraper..."
        git pull origin main
        docker-compose -f docker-compose.prod.yml up -d --build
        ;;
    restart)
        log_info "Restarting NSE Scraper..."
        docker-compose -f docker-compose.prod.yml restart
        ;;
    stop)
        log_info "Stopping NSE Scraper..."
        docker-compose -f docker-compose.prod.yml down
        ;;
    logs)
        log_info "Showing logs..."
        docker-compose -f docker-compose.prod.yml logs -f
        ;;
    status)
        log_info "Checking status..."
        docker-compose -f docker-compose.prod.yml ps
        echo ""
        log_info "Health check..."
        curl -s http://localhost:1020/health | python3 -m json.tool 2>/dev/null || log_warn "Health check failed"
        ;;
    *)
        echo "Usage: $0 {deploy|update|restart|stop|logs|status}"
        exit 1
        ;;
esac

echo ""
log_info "Done!"

# Show status after deploy/update/restart
if [[ "$ACTION" == "deploy" || "$ACTION" == "update" || "$ACTION" == "restart" ]]; then
    echo ""
    log_info "Container Status:"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    log_info "Waiting for service to start..."
    sleep 10
    
    log_info "Health Check:"
    curl -s http://localhost:1020/health | python3 -m json.tool 2>/dev/null || log_warn "Service may still be starting..."
    
    echo ""
    log_info "API Documentation: http://<YOUR_IP>:1020/docs"
fi
