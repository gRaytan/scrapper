# Quick Start - Deploy to AWS EC2 in 15 Minutes

This is a condensed guide to get your Job Scraper running on AWS EC2 quickly.

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

```bash
# View logs
docker compose -f docker-compose.production.yml logs -f [service]

# Restart service
docker compose -f docker-compose.production.yml restart [service]

# Monitor
./deployment/monitor.sh

# Backup
./deployment/backup.sh

# Update
git pull && ./deployment/deploy.sh
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

**Workers not running?**
```bash
docker compose -f docker-compose.production.yml logs celery_worker
docker compose -f docker-compose.production.yml restart celery_worker celery_beat
```

---

## Support

Full documentation: `deployment/README.md`

