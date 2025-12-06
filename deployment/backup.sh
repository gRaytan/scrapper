#!/bin/bash
# Database backup script for production
# Run this script regularly via cron

set -e

# Configuration
BACKUP_DIR="/opt/scraper/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="scraper_db_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=7

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting database backup...${NC}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Perform backup
docker compose -f /opt/scraper/docker-compose.production.yml exec -T postgres \
    pg_dump -U scraper scraper_db | gzip > "${BACKUP_DIR}/${BACKUP_FILE}"

echo -e "${GREEN}✓ Backup created: ${BACKUP_FILE}${NC}"

# Remove old backups
find "$BACKUP_DIR" -name "scraper_db_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
echo -e "${GREEN}✓ Old backups cleaned (retention: ${RETENTION_DAYS} days)${NC}"

# Optional: Upload to S3
# if [ ! -z "$AWS_S3_BACKUP_BUCKET" ]; then
#     aws s3 cp "${BACKUP_DIR}/${BACKUP_FILE}" "s3://${AWS_S3_BACKUP_BUCKET}/backups/"
#     echo -e "${GREEN}✓ Backup uploaded to S3${NC}"
# fi

echo -e "${GREEN}✓ Backup complete!${NC}"

