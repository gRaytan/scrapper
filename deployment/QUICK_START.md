# Quick Start - Deploy to AWS EC2 in 15 Minutes

This is a condensed guide to get your Job Scraper running on AWS EC2 quickly.

## ⚠️ CRITICAL: Deployment Location

**Production deployment MUST be from `/opt/scraper`**

```
EC2 Server: 16.171.142.30 (api.hiddenjobs.me)
SSH Key: /Users/gilr/IdeaProjects/pem/hiddenjobs-key.pem
Deployment Path: /opt/scraper
Compose File: docker-compose.production.yml
```

**NEVER deploy from any other directory!**

## Production Configuration Summary

| Component | Value | Notes |
|-----------|-------|-------|
| Deployment Directory | `/opt/scraper` | Always use this path |
| Compose File | `docker-compose.production.yml` | Not `docker-compose.yml` |
| Network | `scraper_scraper_network` | Single network for all containers |
| Nginx upstream | `server api:8000` | Uses Docker service name, not container name |
| Container names | `scraper_*_prod` | e.g., `scraper_api_prod`, `scraper_nginx_prod` |

### Docker Networking Explained

- **Service name** (`api`) - Defined in docker-compose.production.yml, used for Docker DNS resolution
- **Container name** (`scraper_api_prod`) - Used for external commands like `docker logs scraper_api_prod`
- Nginx config uses `api:8000` because Docker DNS resolves service names within the same network
- All containers MUST be on the same network (`scraper_scraper_network`) for DNS to work

## Prerequisites
- AWS account
- SSH key pair
- Domain name (optional, for HTTPS)

---

## Step 1: Launch EC2 Instance (5 minutes)

1. **AWS Console** → EC2 → Launch Instance
2. **Settings**:
   - Name: `job-scraper-prod`
   - AMI: Ubuntu 22.04 LTS
   - Type: t3.medium (2 vCPU, 4GB RAM)
   - Storage: 30GB
   - Security Group: Allow ports 22, 80, 443

3. **Launch** and note the public IP

---

## Step 2: Setup EC2 (5 minutes)

```bash
# SSH to instance
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Run setup (as root)
sudo su -
curl -o setup.sh https://raw.githubusercontent.com/YOUR_REPO/main/deployment/setup_ec2.sh
chmod +x setup.sh
./setup.sh

# Switch to scraper user
sudo su - scraper
cd /opt/scraper
```

---

## Step 3: Deploy Application (5 minutes)

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .

# Configure environment
cp .env.production .env

# Generate secrets
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "REDIS_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env

# Edit .env and add your API keys
vim .env
# Add: OPENAI_API_KEY=sk-...

# Deploy
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

---

## Step 4: Verify (2 minutes)

```bash
# Check services
docker compose -f docker-compose.production.yml ps

# Test API
curl http://YOUR_EC2_IP/health

# View logs
docker compose -f docker-compose.production.yml logs -f
```

---

## Done! 🎉

Your API is now running at: `http://YOUR_EC2_IP`

### Next Steps:
1. Configure SSL (see main README.md)
2. Setup automated backups
3. Configure monitoring
4. Test scraping: `docker compose -f docker-compose.production.yml exec api python scripts/run_scraper.py`

---

## Common Commands

**Always run from `/opt/scraper` on the EC2 server:**

```bash
# SSH to server
ssh -i /Users/gilr/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@16.171.142.30

# Go to deployment directory (ALWAYS use this path!)
cd /opt/scraper

# View logs
sudo docker compose -f docker-compose.production.yml logs -f [service]

# Restart service
sudo docker compose -f docker-compose.production.yml restart [service]

# Rebuild and restart API only
sudo docker compose -f docker-compose.production.yml up -d --build api

# Monitor
./deployment/monitor.sh

# Backup
./deployment/backup.sh

# Full redeploy
sudo ./deployment/deploy.sh
```

## Quick Deploy (Copy Files from Local)

```bash
# From your local machine - copy updated files to EC2
scp -i /Users/gilr/IdeaProjects/pem/hiddenjobs-key.pem \
  /Users/gilr/IdeaProjects/scrapper/src/path/to/file.py \
  ubuntu@16.171.142.30:/tmp/

# SSH to server and move files
ssh -i /Users/gilr/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@16.171.142.30
sudo cp /tmp/file.py /opt/scraper/src/path/to/file.py
sudo chown scraper:scraper /opt/scraper/src/path/to/file.py

# Rebuild and restart (IMPORTANT: also restart nginx to refresh DNS cache!)
cd /opt/scraper
sudo docker compose -f docker-compose.production.yml up -d --build api
sudo docker compose -f docker-compose.production.yml restart nginx
```

---

## Troubleshooting

**Services won't start?**
```bash
docker compose -f docker-compose.production.yml logs
```

**Can't connect to API?**
- Check security group allows port 80
- Check firewall: `sudo ufw status`
- Check nginx: `docker compose -f docker-compose.production.yml logs nginx`

**502 Bad Gateway?**

This usually means nginx can't reach the API container. **Most common cause: nginx cached the old container IP after a rebuild.**

### Quick Fix (90% of cases):
```bash
# Just restart nginx to refresh DNS cache
cd /opt/scraper
sudo docker compose -f docker-compose.production.yml restart nginx
```

### Why This Happens:
Nginx caches DNS resolution at startup. When you rebuild/recreate containers (e.g., `docker compose up -d --build api`), the API container gets a new IP address, but nginx still points to the old cached IP → 502 error.

**Rule: Always restart nginx after rebuilding any service containers.**

### Full Troubleshooting:
```bash
# 1. Restart nginx (fixes most 502 errors)
sudo docker compose -f docker-compose.production.yml restart nginx

# 2. Verify all containers are on the same network
sudo docker network inspect scraper_scraper_network --format '{{range .Containers}}{{.Name}} {{end}}'
# Should show: scraper_api_prod scraper_nginx_prod scraper_postgres_prod scraper_redis_prod ...

# 3. Test internal connectivity from nginx
sudo docker exec scraper_nginx_prod wget -q -O- http://api:8000/health
# Should return: {"status":"healthy"}

# 4. If still failing, restart everything:
cd /opt/scraper
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d
```

**Workers not running?**
```bash
docker compose -f docker-compose.production.yml logs celery_worker
docker compose -f docker-compose.production.yml restart celery_worker celery_beat
```

---

## Support

Full documentation: `deployment/README.md`

