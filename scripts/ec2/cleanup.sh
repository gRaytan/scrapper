#!/bin/bash
# Weekly cleanup script for Docker resources
# Runs via cron on Sundays at 4 AM UTC: 0 4 * * 0 /home/ubuntu/cleanup.sh >> /home/ubuntu/logs/cleanup.log 2>&1

echo "[$(date)] Starting weekly cleanup..."

# Remove unused Docker images older than 7 days
echo "Cleaning unused Docker images..."
sudo docker image prune -af --filter "until=168h"

# Remove unused Docker volumes (not attached to any container)
# NOTE: Be careful - this removes unattached volumes!
echo "Cleaning unused Docker volumes..."
sudo docker volume prune -f

# Remove Docker build cache (keep 1GB)
echo "Cleaning Docker build cache..."
sudo docker builder prune -f --keep-storage=1GB

# Show disk usage
echo ""
echo "Current disk usage:"
df -h /

echo "[$(date)] Weekly cleanup complete!"

