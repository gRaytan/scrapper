#!/bin/bash
#
# fix_migration_sync.sh
# Fixes Alembic migration sync issues when database state doesn't match migration history
#
# Usage: ./scripts/fix_migration_sync.sh [--dry-run]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DRY_RUN=false
BACKUP_DIR="./backups"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true ;;
        -h|--help) 
            echo "Usage: $0 [--dry-run]"
            echo "  --dry-run    Show what would be done without making changes"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if we're in the right directory
if [ ! -f "alembic.ini" ]; then
    log_error "alembic.ini not found. Please run this script from the project root."
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    log_warn "Virtual environment not activated. Attempting to activate..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        log_error "Could not find virtual environment. Please activate it manually."
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "  Alembic Migration Sync Fix Script"
echo "=========================================="
echo ""

if [ "$DRY_RUN" = true ]; then
    log_warn "DRY RUN MODE - No changes will be made"
    echo ""
fi

# Step 1: Show current migration state
log_info "Step 1: Checking current migration state..."
echo ""
alembic current
echo ""

# Step 2: Show migration history
log_info "Step 2: Showing migration history..."
echo ""
alembic history --indicate-current
echo ""

# Step 3: Check for tables that might already exist
log_info "Step 3: Checking database for existing tables/columns..."
echo ""

# Load database URL from environment or .env file
if [ -z "$DATABASE_URL" ]; then
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | grep DATABASE_URL | xargs)
    fi
fi

if [ -z "$DATABASE_URL" ]; then
    log_warn "DATABASE_URL not set. Skipping database checks."
else
    # Extract connection details and check tables
    log_info "Checking if 'interview_questions' table exists..."
    psql "$DATABASE_URL" -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'interview_questions');" 2>/dev/null || log_warn "Could not check database"
    
    log_info "Checking if 'industry_category' column exists on companies..."
    psql "$DATABASE_URL" -c "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'companies' AND column_name = 'industry_category');" 2>/dev/null || log_warn "Could not check database"
fi
echo ""

# Step 4: Identify migrations that need stamping
log_info "Step 4: Identifying migrations that may need stamping..."
echo ""

# Known problematic migrations (add more as needed)
MIGRATIONS_TO_CHECK=(
    "i3j4k5l6m7n8:interview_questions table"
    "j4k5l6m7n8o9:industry_category column"
)

for migration_info in "${MIGRATIONS_TO_CHECK[@]}"; do
    IFS=':' read -r migration_id description <<< "$migration_info"
    log_info "  - $migration_id: $description"
done
echo ""

# Step 5: Interactive stamping
log_info "Step 5: Migration stamping..."
echo ""

read -p "Do you need to stamp any migrations? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    log_info "Enter migration IDs to stamp (one per line, empty line to finish):"
    
    STAMPS=()
    while true; do
        read -p "  Migration ID: " migration_id
        if [ -z "$migration_id" ]; then
            break
        fi
        STAMPS+=("$migration_id")
    done
    
    if [ ${#STAMPS[@]} -gt 0 ]; then
        for stamp in "${STAMPS[@]}"; do
            if [ "$DRY_RUN" = true ]; then
                log_info "[DRY RUN] Would stamp: $stamp"
            else
                log_info "Stamping migration: $stamp"
                alembic stamp "$stamp"
                log_success "Stamped: $stamp"
            fi
        done
    fi
fi
echo ""

# Step 6: Run upgrade
log_info "Step 6: Running alembic upgrade head..."
echo ""

if [ "$DRY_RUN" = true ]; then
    log_info "[DRY RUN] Would run: alembic upgrade head"
    log_info "Showing SQL that would be executed:"
    alembic upgrade head --sql 2>/dev/null || log_warn "Could not generate SQL preview"
else
    read -p "Proceed with 'alembic upgrade head'? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        alembic upgrade head
        log_success "Migrations applied successfully!"
    else
        log_warn "Skipped upgrade. You can run it manually: alembic upgrade head"
    fi
fi
echo ""

# Step 7: Verify final state
log_info "Step 7: Verifying final migration state..."
echo ""
alembic current
echo ""

# Summary
echo "=========================================="
echo "  Summary"
echo "=========================================="
if [ "$DRY_RUN" = true ]; then
    log_warn "DRY RUN completed. No changes were made."
else
    log_success "Migration sync fix completed!"
fi
echo ""
log_info "Next steps:"
echo "  1. Restart your application"
echo "  2. Test alert creation"
echo "  3. Monitor logs for any errors"
echo ""
