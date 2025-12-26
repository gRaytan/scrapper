# Quick Start - Deploy to AWS EC2 in 15 Minutes

This is a condensed guide to get your Job Scraper running on AWS EC2 quickly.

## ⚠️ CRITICAL: Deployment Location

**Production deployment MUST be from `/opt/scraper`**

```
EC2 Server: 51.17.250.130 (api.hiddenjobs.me)
SSH Key: /Users/gilr/IdeaProjects/pem/hidden-jobs-key.pem
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
ssh -i /Users/gilr/IdeaProjects/pem/hidden-jobs-key.pem ubuntu@51.17.250.130

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
scp -i /Users/gilr/IdeaProjects/pem/hidden-jobs-key.pem \
  /Users/gilr/IdeaProjects/scrapper/src/path/to/file.py \
  ubuntu@51.17.250.130:/tmp/

# SSH to server and move files
ssh -i /Users/gilr/IdeaProjects/pem/hidden-jobs-key.pem ubuntu@51.17.250.130
sudo cp /tmp/file.py /opt/scraper/src/path/to/file.py
sudo chown scraper:scraper /opt/scraper/src/path/to/file.py

# Rebuild and restart
cd /opt/scraper
sudo docker compose -f docker-compose.production.yml up -d --build api
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

This usually means nginx can't reach the API container. Check:

```bash
# 1. Verify all containers are on the same network
sudo docker network inspect scraper_scraper_network --format '{{range .Containers}}{{.Name}} {{end}}'
# Should show: scraper_api_prod scraper_nginx_prod scraper_postgres_prod scraper_redis_prod ...

# 2. Test DNS resolution from nginx
sudo docker exec scraper_nginx_prod ping -c 1 api
# Should resolve to an IP like 172.18.0.x

# 3. If containers are on different networks, restart everything:
cd /opt/scraper
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d

# 4. Check nginx config uses service name 'api', not container name 'scraper_api_prod'
grep 'server.*8000' /opt/scraper/deployment/nginx.conf
# Should show: server api:8000
```

**Workers not running?**
```bash
docker compose -f docker-compose.production.yml logs celery_worker
docker compose -f docker-compose.production.yml restart celery_worker celery_beat
```

---

## Support

Full documentation: `deployment/README.md`

