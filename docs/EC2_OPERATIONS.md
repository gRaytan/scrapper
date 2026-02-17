# EC2 Operations Guide

## Server Details
- **Host:** ubuntu@16.171.142.30
- **SSH Key:** `/Users/gilr/IdeaProjects/pem/hiddenjobs-key.pem`
- **SSH:** `ssh -i /Users/gilr/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@16.171.142.30`

---

## Backups

### How It Works
- **Schedule:** Daily at 3 AM UTC (cron)
- **Retention:** Last 7 days (older backups auto-deleted)
- **Location:** `/home/ubuntu/backups/`
- **Format:** Compressed PostgreSQL dump (`.sql.gz`)
- **Size:** ~5 MB per backup (DB is ~17 MB uncompressed)

### List Backups
```bash
ls -lh /home/ubuntu/backups/
```

### Manual Backup
```bash
/home/ubuntu/backup.sh
```

### Restore a Backup
```bash
# 1. List available backups
ls -la /home/ubuntu/backups/

# 2. Restore from compressed backup
gunzip -c /home/ubuntu/backups/scraper_db_YYYYMMDD_HHMMSS.sql.gz | \
  sudo docker exec -i scraper_postgres_prod psql -U scraper -d scraper_db

# 3. Or restore from uncompressed backup
cat /home/ubuntu/backups/scraper_db_YYYYMMDD_HHMMSS.sql | \
  sudo docker exec -i scraper_postgres_prod psql -U scraper -d scraper_db
```

---

## Git Server

### Push Code from Local
```bash
cd /path/to/scrapper
GIT_SSH_COMMAND="ssh -i /path/to/hiddenjobs-key.pem" git push ec2 main
```

### Deploy After Push
```bash
ssh -i /path/to/hiddenjobs-key.pem ubuntu@16.171.142.30
cd /home/ubuntu/scraper-upload
./deploy.sh
```

### Git Remote Setup (one-time)
```bash
git remote add ec2 ubuntu@16.171.142.30:/home/ubuntu/git-repos/scraper.git
```

---

## Docker Operations

### View Running Containers
```bash
sudo docker ps
```

### View Logs
```bash
sudo docker logs --tail 100 scraper_api_prod
sudo docker logs --tail 100 scraper_celery_worker_prod
```

### Restart Services
```bash
cd /home/ubuntu/scraper-upload
sudo docker compose -f docker-compose.production.yml restart
```

### Full Redeploy (with fresh images)
```bash
./deploy.sh
```

### Run Database Migrations
```bash
sudo docker compose -f docker-compose.production.yml exec -T api alembic upgrade head
```

---

## Full Deployment Process

Complete deployment from local machine:

```bash
# 1. Push code to EC2
cd /Users/gilr/IdeaProjects/scrapper
GIT_SSH_COMMAND="ssh -i /Users/gilr/IdeaProjects/pem/hiddenjobs-key.pem" git push ec2 main

# 2. SSH to EC2
ssh -i /Users/gilr/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@16.171.142.30

# 3. Check disk space (optional)
df -h /
sudo docker system df

# 4. Free up space if needed
sudo docker system prune -af

# 5. Deploy
cd /home/ubuntu/scraper-upload
./deploy.sh

# 6. Run migrations
sudo docker compose -f docker-compose.production.yml exec -T api alembic upgrade head

# 7. Verify
sudo docker compose -f docker-compose.production.yml ps
```

---

## Cleanup

### Manual Cleanup
```bash
sudo docker system prune -af
```

### What Gets Cleaned
- Docker build cache
- Unused Docker images
- Unused Docker volumes
- Unused Docker networks

### Scheduled Cleanup
- **When:** Sunday 4 AM UTC (weekly)
- **Log:** `/home/ubuntu/logs/cleanup.log`

---

## Disk Usage

### Check Disk Space
```bash
df -h /
```

### Check Docker Usage
```bash
sudo docker system df
```

### Expected Usage
| Component | Size |
|-----------|------|
| Docker images | ~10 GB |
| Build cache | 0-1 GB |
| Database | ~80 MB |
| Backups (7 days) | ~35 MB |
| OS/System | ~7 GB |
| **Total** | ~18 GB |
| **Available** | ~11 GB |

---

## Cron Jobs

View current cron jobs:
```bash
crontab -l
```

| Schedule | Job | Log |
|----------|-----|-----|
| Daily 3 AM | Backup | `/home/ubuntu/logs/backup.log` |
| Sunday 4 AM | Cleanup | `/home/ubuntu/logs/cleanup.log` |

