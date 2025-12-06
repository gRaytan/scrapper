#!/bin/bash
# Make all deployment scripts executable

chmod +x deployment/setup_ec2.sh
chmod +x deployment/deploy.sh
chmod +x deployment/backup.sh
chmod +x deployment/monitor.sh

echo "✓ All deployment scripts are now executable"

