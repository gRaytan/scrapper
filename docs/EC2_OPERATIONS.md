# EC2 Operations Guide

Daily operations runbook for the HiddenJobs scraper on EC2.

> **For initial EC2 setup** (first-time provisioning), see: **[deployment/README.md](../deployment/README.md)**

---

## Server Details
- **Host:** api.hiddenjobs.me (16.171.142.30)
- **SSH Key:** `~/IdeaProjects/pem/hiddenjobs-key.pem`
- **SSH:** `ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@api.hiddenjobs.me`

---

## Architecture Overview

```
Local Machine                    EC2 Server
─────────────                    ──────────
~/IdeaProjects/scrapper/
    │
    └── rsync ─────────────────► /opt/scraper (production code)
                                        │
                                        ▼ (deploy.sh or docker commands)
                                  Docker Containers:
                                  - scraper_api_prod
                                  - scraper_celery_worker_prod
                                  - scraper_celery_beat_prod
                                  - scraper_postgres_prod
                                  - scraper_redis_prod
                                  - scraper_nginx_prod
```

| Directory | Purpose |
|-----------|---------|
| `/opt/scraper` | Production code (containers built here) |
| `/home/ubuntu/backups` | Database backups |

### Docker Networking

| Term | Example | Used For |
|------|---------|----------|
| Service name | `api` | Docker DNS resolution (nginx config uses `api:8000`) |
| Container name | `scraper_api_prod` | External commands (`docker logs scraper_api_prod`) |
| Network | `scraper_scraper_network` | All containers must be on same network for DNS |

---

## Deployment (FROM LOCAL MACHINE)

### Step 1: Sync Files to EC2

**Always run this first to copy your local changes to the server:**

```bash
rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' \
  --exclude 'data/' --exclude 'logs/' --exclude '.env' --exclude 'backups/' \
  -e "ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem" \
  ~/IdeaProjects/scrapper/ ubuntu@api.hiddenjobs.me:/opt/scraper/
```

### Step 2: Apply Changes

| Change Type | Command | Time |
|-------------|---------|------|
| Code only (Python files) | `./deployment/deploy.sh` | ~5 sec |
| New Python dependency | `./deployment/deploy.sh --build` | ~3 min |
| New system dependency | `./deployment/deploy.sh --full` | ~15 min |
| Migrations only | `./deployment/deploy.sh --migrate` | ~5 sec |

**Run from local via SSH:**
```bash
# Code changes only (restart)
ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@api.hiddenjobs.me \
  "cd /opt/scraper && sudo ./deployment/deploy.sh"

# With rebuild (new Python deps)
ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@api.hiddenjobs.me \
  "cd /opt/scraper && sudo ./deployment/deploy.sh --build"

# Full rebuild (Dockerfile/system changes)
ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@api.hiddenjobs.me \
  "cd /opt/scraper && sudo ./deployment/deploy.sh --full"
```

### One-Liner Deploy Commands

**Quick deploy (code changes only):**
```bash
rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' --exclude 'data/' --exclude 'logs/' --exclude '.env' --exclude 'backups/' -e "ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem" ~/IdeaProjects/scrapper/ ubuntu@api.hiddenjobs.me:/opt/scraper/ && ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@api.hiddenjobs.me "cd /opt/scraper && sudo ./deployment/deploy.sh"
```

**Deploy with rebuild:**
```bash
rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' --exclude 'data/' --exclude 'logs/' --exclude '.env' --exclude 'backups/' -e "ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem" ~/IdeaProjects/scrapper/ ubuntu@api.hiddenjobs.me:/opt/scraper/ && ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@api.hiddenjobs.me "cd /opt/scraper && sudo ./deployment/deploy.sh --build"
```

### Step 3: Verify

```bash
curl -s https://api.hiddenjobs.me/health | jq
```

---

## Docker Operations

### View Running Containers
```bash
cd /opt/scraper
sudo docker compose -f docker-compose.production.yml ps
```

### View Logs
```bash
# All containers
sudo docker compose -f docker-compose.production.yml logs --tail 100

# Specific container
sudo docker logs --tail 100 scraper_api_prod
sudo docker logs --tail 100 scraper_celery_worker_prod
sudo docker logs --tail 100 scraper_celery_beat_prod
```

### Restart Services (without rebuild)
```bash
cd /opt/scraper
sudo docker compose -f docker-compose.production.yml restart
```

### Full Rebuild
```bash
cd /opt/scraper
sudo docker compose -f docker-compose.production.yml build --no-cache
sudo docker compose -f docker-compose.production.yml up -d
```

### Run Database Migrations
```bash
cd /opt/scraper
sudo docker compose -f docker-compose.production.yml exec -T api alembic upgrade head
```

> **Note:** Migrations run after deploy because alembic executes inside the API container.
> For schema changes that could break existing code, consider:
> 1. Deploy migration-only changes first
> 2. Run migration
> 3. Deploy code that uses new schema

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

---

## Troubleshooting

### "No space left on device" during build
```bash
# Clean up Docker resources
sudo docker system prune -af --volumes

# Check disk space
df -h /
```

### Container won't start
```bash
# Check logs
sudo docker compose -f docker-compose.production.yml logs --tail 100

# Check if .env file exists
ls -la /opt/scraper/.env
```

### 502 Bad Gateway

This usually means nginx can't reach the API container. **Most common cause: nginx cached the old container IP after a rebuild.**

**Quick Fix (90% of cases):**
```bash
cd /opt/scraper
sudo docker compose -f docker-compose.production.yml restart nginx
```

**Why this happens:** Nginx caches DNS resolution at startup. When you rebuild containers, the API gets a new IP, but nginx still points to the old cached IP.

**Rule: Always restart nginx after rebuilding any service containers.**

**Full troubleshooting:**
```bash
# 1. Restart nginx (fixes most 502 errors)
sudo docker compose -f docker-compose.production.yml restart nginx

# 2. Verify all containers are on the same network
sudo docker network inspect scraper_scraper_network --format '{{range .Containers}}{{.Name}} {{end}}'

# 3. Test internal connectivity from nginx
sudo docker exec scraper_nginx_prod wget -q -O- http://api:8000/health

# 4. If still failing, restart everything
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d
```

### CORS errors
CORS is handled by FastAPI (not nginx). Check:
```bash
# Verify CORS settings in container
sudo docker exec scraper_api_prod python -c "from config.settings import settings; print(settings.cors_origins_list)"

# Test CORS headers
curl -H "Origin: https://hiddenjobs.me" -I https://api.hiddenjobs.me/health
```

### Git push rejected
```bash
# Check remote is configured
git remote -v | grep ec2

# Re-add remote if needed
git remote add ec2 ubuntu@api.hiddenjobs.me:/home/ubuntu/git-repos/scraper.git
```

### Verify deployment
```bash
# Check git hash matches local
cd /opt/scraper && git log --oneline -1

# Compare with local
cd ~/IdeaProjects/scrapper && git log --oneline -1
```

---

## ⚠️ CRITICAL: Docker Volume Management

### Named Volumes (NEVER CHANGE)
The production database uses **explicit named volumes** to prevent data loss:

| Volume Name | Purpose |
|-------------|---------|
| `hiddenjobs_postgres_data` | PostgreSQL database |
| `hiddenjobs_redis_data` | Redis cache |
| `hiddenjobs_nginx_logs` | Nginx logs |

**Why this matters:** Docker Compose normally prefixes volume names with the directory name (e.g., `scraper_postgres_data` from `/opt/scraper`). If the deployment directory ever changes, Docker would create NEW empty volumes, **wiping all data**.

The explicit `name:` property in `docker-compose.production.yml` prevents this:
```yaml
volumes:
  postgres_data:
    driver: local
    name: hiddenjobs_postgres_data  # <-- CRITICAL: explicit name
```

### Verify Volumes
```bash
# List all volumes
sudo docker volume ls | grep hiddenjobs

# Check volume is being used
sudo docker inspect scraper_postgres_prod | grep -A 5 Mounts
```

### Restore from Backup
If data is lost, restore from daily backups:
```bash
# List backups
ls -la /home/ubuntu/backups/

# Restore latest backup
LATEST=$(ls -t /home/ubuntu/backups/*.sql.gz | head -1)
gunzip -c $LATEST | sudo docker exec -i scraper_postgres_prod psql -U scraper -d scraper_db

# Verify
sudo docker exec scraper_postgres_prod psql -U scraper -d scraper_db -c 'SELECT COUNT(*) FROM users;'
```
