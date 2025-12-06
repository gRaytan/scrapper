#!/bin/bash
# Monitoring script for production services

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

print_header "Job Scraper Production Monitor"

# Check if docker-compose is running
if ! docker compose -f docker-compose.production.yml ps | grep -q "Up"; then
    print_error "No services are running!"
    exit 1
fi

# Service status
print_header "Service Status"
docker compose -f docker-compose.production.yml ps

# Health checks
print_header "Health Checks"

# API Health
if curl -sf http://localhost/health > /dev/null; then
    print_success "API is healthy"
else
    print_error "API health check failed"
fi

# PostgreSQL
if docker compose -f docker-compose.production.yml exec -T postgres pg_isready -U scraper > /dev/null 2>&1; then
    print_success "PostgreSQL is healthy"
else
    print_error "PostgreSQL is not responding"
fi

# Redis
if docker compose -f docker-compose.production.yml exec -T redis redis-cli -a "${REDIS_PASSWORD}" ping > /dev/null 2>&1; then
    print_success "Redis is healthy"
else
    print_error "Redis is not responding"
fi

# Resource usage
print_header "Resource Usage"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Disk usage
print_header "Disk Usage"
df -h /opt/scraper

# Recent logs
print_header "Recent Errors (Last 10)"
docker compose -f docker-compose.production.yml logs --tail=100 | grep -i error | tail -10 || echo "No recent errors"

# Worker status
print_header "Celery Worker Status"
docker compose -f docker-compose.production.yml exec -T celery_worker celery -A src.workers.celery_app inspect active || print_error "Cannot inspect workers"

# Database stats
print_header "Database Statistics"
docker compose -f docker-compose.production.yml exec -T postgres psql -U scraper -d scraper_db -c "
SELECT 
    'Companies' as table_name, COUNT(*) as count FROM companies
UNION ALL
SELECT 'Job Positions', COUNT(*) FROM job_positions
UNION ALL
SELECT 'Active Jobs', COUNT(*) FROM job_positions WHERE is_active = true
UNION ALL
SELECT 'Users', COUNT(*) FROM users
UNION ALL
SELECT 'Alerts', COUNT(*) FROM alerts;
" 2>/dev/null || print_error "Cannot query database"

echo ""
print_info "Monitor complete!"

