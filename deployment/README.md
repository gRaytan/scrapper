# AWS EC2 Docker Deployment Guide

This guide will help you deploy the Job Scraper application on AWS EC2 using Docker.

## Table of Contents
- [Prerequisites](#prerequisites)
- [EC2 Instance Setup](#ec2-instance-setup)
- [Initial Configuration](#initial-configuration)
- [Deployment](#deployment)
- [Post-Deployment](#post-deployment)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### AWS Requirements
- AWS account with EC2 access
- SSH key pair for EC2 access
- Security group configured with the following ports:
  - **22** (SSH) - Your IP only
  - **80** (HTTP) - 0.0.0.0/0
  - **443** (HTTPS) - 0.0.0.0/0

### Recommended EC2 Instance
- **Instance Type**: t3.medium or larger (2 vCPU, 4GB RAM minimum)
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 30GB+ EBS volume
- **Region**: Choose based on your location

### Local Requirements
- SSH client
- Git (to clone repository)
- Text editor

---

## EC2 Instance Setup

### Step 1: Launch EC2 Instance

1. **Go to AWS Console** → EC2 → Launch Instance

2. **Configure Instance**:
   - Name: `job-scraper-production`
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: t3.medium
   - Key pair: Select or create new
   - Storage: 30GB gp3

3. **Configure Security Group**:
   ```
   Type        Protocol    Port    Source
   SSH         TCP         22      Your IP
   HTTP        TCP         80      0.0.0.0/0
   HTTPS       TCP         443     0.0.0.0/0
   ```

4. **Launch Instance**

### Step 2: Connect to Instance

```bash
# Get your instance public IP from AWS Console
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Step 3: Run Setup Script

```bash
# Switch to root
sudo su -

# Download and run setup script
curl -o setup_ec2.sh https://raw.githubusercontent.com/YOUR_REPO/main/deployment/setup_ec2.sh
chmod +x setup_ec2.sh
./setup_ec2.sh
```

Or if you have the repository locally:

```bash
# Copy setup script to EC2
scp -i /path/to/your-key.pem deployment/setup_ec2.sh ubuntu@YOUR_EC2_PUBLIC_IP:~

# SSH to EC2 and run
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
sudo bash setup_ec2.sh
```

---

## Initial Configuration

### Step 1: Clone Repository

```bash
# Switch to scraper user
sudo su - scraper

# Navigate to application directory
cd /opt/scraper

# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .

# Or copy files via SCP from your local machine
```

### Step 2: Configure Environment Variables

```bash
# Copy production environment template
cp .env.production .env

# Edit environment file
vim .env
```

**Required Configuration**:

```bash
# Generate strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Update .env file with these values
# Also add your API keys:
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY (if using)
```

### Step 3: Update Configuration Files

```bash
# Ensure companies.yaml is configured
vim config/companies.yaml

# Check scraping rules
vim config/scraping_rules.yaml
```

---

## Deployment

### Step 1: Deploy Application

```bash
# Make deploy script executable
chmod +x deployment/deploy.sh

# Run deployment
./deployment/deploy.sh
```

This script will:
1. Build Docker images
2. Start all services (PostgreSQL, Redis, API, Workers, Nginx)
3. Run database migrations
4. Show service status

### Step 2: Initialize Database

```bash
# Create database tables (if not done by migrations)
docker compose -f docker-compose.production.yml exec api python scripts/setup_db.py

# Migrate companies to database
docker compose -f docker-compose.production.yml exec api python scripts/migrate_companies_to_db.py
```

### Step 3: Verify Deployment

```bash
# Check all services are running
docker compose -f docker-compose.production.yml ps

# Check API health
curl http://localhost/health

# Check from external
curl http://YOUR_EC2_PUBLIC_IP/health
```

---

## Post-Deployment

### Configure SSL (Optional but Recommended)

#### Using Let's Encrypt (Free)

```bash
# Install certbot
sudo apt-get install -y certbot

# Stop nginx temporarily
docker compose -f docker-compose.production.yml stop nginx

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo mkdir -p /opt/scraper/deployment/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/scraper/deployment/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/scraper/deployment/ssl/
sudo chown -R scraper:scraper /opt/scraper/deployment/ssl

# Update nginx.conf to enable HTTPS (uncomment HTTPS server block)
vim deployment/nginx.conf

# Restart nginx
docker compose -f docker-compose.production.yml up -d nginx
```

### Setup Automated Backups

```bash
# Make backup script executable
chmod +x deployment/backup.sh

# Test backup
./deployment/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * /opt/scraper/deployment/backup.sh >> /opt/scraper/logs/backup.log 2>&1
```

### Configure Monitoring

```bash
# View logs
docker compose -f docker-compose.production.yml logs -f

# View specific service logs
docker compose -f docker-compose.production.yml logs -f api
docker compose -f docker-compose.production.yml logs -f celery_worker
docker compose -f docker-compose.production.yml logs -f celery_beat
```

---

## Maintenance

### Common Commands

```bash
# View running containers
docker compose -f docker-compose.production.yml ps

# View logs
docker compose -f docker-compose.production.yml logs -f [service_name]

# Restart a service
docker compose -f docker-compose.production.yml restart [service_name]

# Stop all services
docker compose -f docker-compose.production.yml down

# Start all services
docker compose -f docker-compose.production.yml up -d

# Rebuild and restart
docker compose -f docker-compose.production.yml up -d --build

# Execute command in container
docker compose -f docker-compose.production.yml exec api /bin/bash
```

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
./deployment/deploy.sh
```

### Database Operations

```bash
# Access PostgreSQL
docker compose -f docker-compose.production.yml exec postgres psql -U scraper -d scraper_db

# Run migrations
docker compose -f docker-compose.production.yml exec api alembic upgrade head

# Backup database
./deployment/backup.sh

# Restore database
gunzip < /opt/scraper/backups/scraper_db_TIMESTAMP.sql.gz | \
  docker compose -f docker-compose.production.yml exec -T postgres psql -U scraper -d scraper_db
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker compose -f docker-compose.production.yml logs

# Check specific service
docker compose -f docker-compose.production.yml logs api

# Verify environment variables
docker compose -f docker-compose.production.yml config
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker compose -f docker-compose.production.yml ps postgres

# Check database logs
docker compose -f docker-compose.production.yml logs postgres

# Test connection
docker compose -f docker-compose.production.yml exec postgres psql -U scraper -d scraper_db -c "SELECT 1;"
```

### Worker Not Processing Tasks

```bash
# Check worker logs
docker compose -f docker-compose.production.yml logs celery_worker

# Check beat scheduler
docker compose -f docker-compose.production.yml logs celery_beat

# Restart workers
docker compose -f docker-compose.production.yml restart celery_worker celery_beat
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Reduce worker concurrency in docker-compose.production.yml
# Change: --concurrency=2 to --concurrency=1
```

### Disk Space Issues

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a

# Clean old logs
find /opt/scraper/logs -name "*.log" -mtime +7 -delete
```

---

## Security Best Practices

1. **Change Default Passwords**: Update all passwords in `.env`
2. **Enable Firewall**: Use UFW to restrict access
3. **Use HTTPS**: Configure SSL certificates
4. **Regular Updates**: Keep system and Docker updated
5. **Backup Regularly**: Automate database backups
6. **Monitor Logs**: Check for suspicious activity
7. **Restrict SSH**: Use key-based authentication only
8. **Use Secrets Management**: Consider AWS Secrets Manager for production

---

## Support

For issues or questions:
- Check logs: `docker compose -f docker-compose.production.yml logs`
- Review documentation in `/docs`
- Check GitHub issues

---

## Quick Reference

### Service URLs
- API: `http://YOUR_EC2_IP/`
- Health Check: `http://YOUR_EC2_IP/health`
- API Docs: `http://YOUR_EC2_IP/docs`

### Important Paths
- Application: `/opt/scraper`
- Logs: `/opt/scraper/logs`
- Backups: `/opt/scraper/backups`
- Config: `/opt/scraper/config`

### Key Files
- Environment: `.env`
- Docker Compose: `docker-compose.production.yml`
- Nginx Config: `deployment/nginx.conf`

