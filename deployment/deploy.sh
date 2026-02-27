#!/bin/bash
# Deployment script for Job Scraper on EC2
#
# USAGE (run on EC2 server):
#   ./deployment/deploy.sh           # Restart only (code changes)
#   ./deployment/deploy.sh --build   # Rebuild with cache (new Python deps)
#   ./deployment/deploy.sh --full    # Full rebuild no cache (system deps)
#   ./deployment/deploy.sh --migrate # Run migrations only
#
# FILES ARE SYNCED VIA RSYNC FROM LOCAL MACHINE (see docs/EC2_OPERATIONS.md)
# This script does NOT pull from git - it uses whatever files are in /opt/scraper
#
# Production deployment location: /opt/scraper
# Production compose file: docker-compose.production.yml

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ $1${NC}"; }

# Parse arguments
MODE="restart"
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)   MODE="build"; shift ;;
        --full)    MODE="full"; shift ;;
        --migrate) MODE="migrate"; shift ;;
        --help|-h)
            echo "Usage: $0 [--build|--full|--migrate]"
            echo "  (no args)  Restart API only (~5 sec)"
            echo "  --build    Rebuild with cache (~3 min)"
            echo "  --full     Full rebuild no cache (~15 min)"
            echo "  --migrate  Run DB migrations only"
            exit 0
            ;;
        *) print_error "Unknown option: $1"; exit 1 ;;
    esac
done

echo "=========================================="
echo "Job Scraper Deployment - Mode: $MODE"
echo "=========================================="

# Get script directory and cd to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Verify deployment directory
EXPECTED_DIR="/opt/scraper"
if [ "$PROJECT_ROOT" != "$EXPECTED_DIR" ]; then
    print_error "WRONG DIRECTORY! Expected: $EXPECTED_DIR, Got: $PROJECT_ROOT"
    exit 1
fi

# Check required files
[ ! -f .env ] && print_error ".env file not found!" && exit 1
[ ! -f docker-compose.production.yml ] && print_error "docker-compose.production.yml not found!" && exit 1

COMPOSE="docker compose -f docker-compose.production.yml"

case $MODE in
    restart)
        print_info "Restarting API container..."
        $COMPOSE restart api
        $COMPOSE restart nginx  # Refresh DNS cache
        print_success "API restarted"
        ;;
    build)
        print_info "Building API with cache..."
        $COMPOSE build api
        $COMPOSE up -d api
        $COMPOSE restart nginx
        print_success "API rebuilt and started"
        ;;
    full)
        print_info "Full rebuild (no cache)..."
        $COMPOSE build --no-cache api
        $COMPOSE up -d api
        $COMPOSE restart nginx
        print_success "API fully rebuilt and started"
        ;;
    migrate)
        print_info "Running database migrations..."
        $COMPOSE exec -T api alembic upgrade head
        print_success "Migrations completed"
        exit 0
        ;;
esac

# Wait and verify
sleep 3
print_info "Service status:"
$COMPOSE ps api nginx

# Health check
print_info "Health check..."
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    print_success "API is healthy!"
else
    print_error "API health check failed - check logs"
    $COMPOSE logs --tail=20 api
fi

echo ""
print_success "Deployment Complete!"
echo ""

