#!/bin/bash
# Daily database backup script
# Runs via cron at 3 AM UTC: 0 3 * * * /home/ubuntu/backup.sh >> /home/ubuntu/logs/backup.log 2>&1

BACKUP_DIR="/home/ubuntu/backups"
RETENTION_DAYS=7

echo "[$(date)] Starting database backup..."

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup filename with timestamp
BACKUP_FILE="$BACKUP_DIR/scraper_db_$(date +%Y%m%d_%H%M%S).sql"

# Dump the database
sudo docker exec scraper_postgres_prod pg_dump -U scraper -d scraper_db > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    # Compress the backup
    gzip "$BACKUP_FILE"
    BACKUP_SIZE=$(ls -lh "${BACKUP_FILE}.gz" | awk '{print $5}')
    echo "[$(date)] ✅ Backup created: ${BACKUP_FILE}.gz ($BACKUP_SIZE)"
    
    # Delete backups older than retention period
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "[$(date)] 📁 Current backups:"
    ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
else
    echo "[$(date)] ❌ ERROR: Backup failed!"
    exit 1
fi

