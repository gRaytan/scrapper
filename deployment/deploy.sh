#!/bin/bash
# Deployment script for Job Scraper on EC2
# Run this script as the 'scraper' user

set -e  # Exit on error

echo "=========================================="
echo "Job Scraper Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_info "Please create .env file from .env.production template"
    exit 1
fi

print_success ".env file found"

# Check if docker-compose.production.yml exists
if [ ! -f docker-compose.production.yml ]; then
    print_error "docker-compose.production.yml not found!"
    exit 1
fi

print_success "docker-compose.production.yml found"

# Pull latest changes (if using git)
if [ -d .git ]; then
    print_info "Pulling latest changes from git..."
    git pull
    print_success "Git pull completed"
fi

# Build Docker images
print_info "Building Docker images..."
docker compose -f docker-compose.production.yml build --no-cache
print_success "Docker images built"

# Stop existing containers
print_info "Stopping existing containers..."
docker compose -f docker-compose.production.yml down
print_success "Existing containers stopped"

# Start services
print_info "Starting services..."
docker compose -f docker-compose.production.yml up -d
print_success "Services started"

# Wait for services to be healthy
print_info "Waiting for services to be healthy..."
sleep 10

# Check service status
print_info "Checking service status..."
docker compose -f docker-compose.production.yml ps

# Run database migrations
print_info "Running database migrations..."
docker compose -f docker-compose.production.yml exec -T api alembic upgrade head
print_success "Database migrations completed"

# Show logs
print_info "Showing recent logs..."
docker compose -f docker-compose.production.yml logs --tail=50

echo ""
echo "=========================================="
print_success "Deployment Complete!"
echo "=========================================="
echo ""
print_info "Service URLs:"
echo "  API: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):80"
echo "  Health: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):80/health"
echo ""
print_info "Useful commands:"
echo "  View logs: docker compose -f docker-compose.production.yml logs -f [service]"
echo "  Restart: docker compose -f docker-compose.production.yml restart [service]"
echo "  Stop all: docker compose -f docker-compose.production.yml down"
echo "  Shell access: docker compose -f docker-compose.production.yml exec [service] /bin/bash"
echo ""

