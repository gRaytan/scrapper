# AWS EC2 Initial Setup Guide

This guide covers **first-time setup** of a new EC2 instance for the Job Scraper.

> **For daily operations** (deploying code, viewing logs, backups, troubleshooting), see: **[docs/EC2_OPERATIONS.md](../docs/EC2_OPERATIONS.md)**

## Table of Contents
- [Prerequisites](#prerequisites)
- [EC2 Instance Setup](#ec2-instance-setup)
- [Initial Configuration](#initial-configuration)
- [First Deployment](#first-deployment)
- [Post-Setup](#post-setup)

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

## First Deployment

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

## Post-Setup

### Configure SSL (Optional but Recommended)

```bash
# Run SSL setup script
sudo /opt/scraper/deployment/setup_ssl.sh
```

Or manually with Let's Encrypt - see `deployment/setup_ssl.sh` for details.

### Setup Automated Backups

```bash
# Add to crontab (daily at 3 AM)
crontab -e

# Add this line:
0 3 * * * /home/ubuntu/backup.sh >> /home/ubuntu/logs/backup.log 2>&1
```

### Setup Git Remote for Deployments

```bash
# One-time setup on local machine
git remote add ec2 ubuntu@api.hiddenjobs.me:/home/ubuntu/git-repos/scraper.git
```

---

## Next Steps

Your EC2 instance is now set up. For daily operations, see:

📖 **[docs/EC2_OPERATIONS.md](../docs/EC2_OPERATIONS.md)** - Covers:
- Deploying code changes
- Viewing logs
- Docker operations
- Backups & restore
- Troubleshooting
- Volume management

