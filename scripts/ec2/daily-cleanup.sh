dsa#!/bin/bash
# Daily cleanup script for Docker
# Runs via cron at 4 AM UTC: 0 4 * * * /home/ubuntu/daily-cleanup.sh >> /home/ubuntu/logs/cleanup.log 2>&1

echo "[$(date)] Starting daily cleanup..."

# Remove dangling images and stopped containers
echo "Pruning system..."
docker system prune -f

# Remove unused images older than 1 day
echo "Removing old unused images..."
docker image prune -af --filter "until=24h"

# Remove all build cache
echo "Clearing build cache..."
docker builder prune -af

echo ""
echo "Current disk usage:"
df -h /

echo "[$(date)] Daily cleanup complete!"

