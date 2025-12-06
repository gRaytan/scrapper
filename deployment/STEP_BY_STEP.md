# Step-by-Step Deployment Guide

Follow these exact steps to deploy your Job Scraper to AWS EC2.

---

## Phase 1: AWS Setup (15 minutes)

### Step 1: Launch EC2 Instance

1. **Login to AWS Console**
   - Go to https://console.aws.amazon.com
   - Navigate to EC2 Dashboard

2. **Click "Launch Instance"**

3. **Configure Instance**:
   
   **Name and tags:**
   - Name: `job-scraper-production`
   
   **Application and OS Images:**
   - AMI: `Ubuntu Server 22.04 LTS (HVM), SSD Volume Type`
   - Architecture: `64-bit (x86)`
   
   **Instance type:**
   - Select: `t3.medium` (2 vCPU, 4 GB RAM)
   - Alternative: `t3.small` (2 vCPU, 2 GB RAM) - minimum
   
   **Key pair:**
   - Click "Create new key pair"
   - Name: `job-scraper-key`
   - Type: `RSA`
   - Format: `.pem` (for Mac/Linux) or `.ppk` (for Windows/PuTTY)
   - Click "Create key pair" - **SAVE THIS FILE!**
   
   **Network settings:**
   - Click "Edit"
   - Auto-assign public IP: `Enable`
   - Firewall (security groups): `Create security group`
   - Security group name: `job-scraper-sg`
   - Description: `Security group for job scraper`
   
   **Add these rules:**
   - Rule 1: SSH
     - Type: `SSH`
     - Port: `22`
     - Source: `My IP` (your current IP)
   
   - Rule 2: HTTP
     - Type: `HTTP`
     - Port: `80`
     - Source: `Anywhere (0.0.0.0/0)`
   
   - Rule 3: HTTPS
     - Type: `HTTPS`
     - Port: `443`
     - Source: `Anywhere (0.0.0.0/0)`
   
   **Configure storage:**
   - Size: `30 GB`
   - Volume type: `gp3`
   - Delete on termination: `Yes`

4. **Review and Launch**
   - Click "Launch instance"
   - Wait for instance to start (2-3 minutes)

5. **Note Your Instance Details**
   - Go to EC2 Dashboard → Instances
   - Select your instance
   - Copy the **Public IPv4 address** (e.g., `54.123.45.67`)
   - Save this - you'll need it!

---

## Phase 2: Connect to EC2 (5 minutes)

### Step 2: Prepare SSH Key

**On Mac/Linux:**
```bash
# Move key to .ssh directory
mv ~/Downloads/job-scraper-key.pem ~/.ssh/

# Set correct permissions
chmod 400 ~/.ssh/job-scraper-key.pem
```

**On Windows (using Git Bash or WSL):**
```bash
# Move key to .ssh directory
mv /c/Users/YourName/Downloads/job-scraper-key.pem ~/.ssh/

# Set correct permissions
chmod 400 ~/.ssh/job-scraper-key.pem
```

### Step 3: Connect via SSH

```bash
# Replace YOUR_EC2_IP with your actual IP from Step 1
ssh -i ~/.ssh/job-scraper-key.pem ubuntu@YOUR_EC2_IP
```

**First time connecting:**
- You'll see: "Are you sure you want to continue connecting?"
- Type: `yes` and press Enter

**You should now see:**
```
ubuntu@ip-xxx-xxx-xxx-xxx:~$
```

✅ **You're connected to your EC2 instance!**

---

## Phase 3: Setup EC2 Instance (10 minutes)

### Step 4: Upload Setup Script

**Option A: Direct download (if script is on GitHub)**
```bash
# Download setup script
curl -o setup_ec2.sh https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/deployment/setup_ec2.sh

# Make executable
chmod +x setup_ec2.sh
```

**Option B: Copy from local machine**

Open a **NEW terminal** on your local machine (keep SSH session open):
```bash
# From your project directory
cd /Users/gilr/IdeaProjects/scrapper

# Copy setup script to EC2
scp -i ~/.ssh/job-scraper-key.pem deployment/setup_ec2.sh ubuntu@YOUR_EC2_IP:~
```

### Step 5: Run Setup Script

**Back in your SSH session:**
```bash
# Switch to root
sudo su -

# Run setup script
bash /home/ubuntu/setup_ec2.sh
```

**This will take 5-10 minutes and will:**
- Update system packages
- Install Docker and Docker Compose
- Create `scraper` user
- Setup firewall
- Configure security
- Create application directories

**When complete, you'll see:**
```
✓ EC2 Instance Setup Complete!
```

---

## Phase 4: Deploy Application (15 minutes)

### Step 6: Switch to Application User

```bash
# Switch to scraper user
sudo su - scraper

# Verify you're in the right directory
pwd
# Should show: /home/scraper

# Go to application directory
cd /opt/scraper
```

### Step 7: Upload Application Code

**Option A: Clone from Git (Recommended)**
```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .

# Note the dot (.) at the end - it clones into current directory
```

**Option B: Copy from local machine**

Open a **NEW terminal** on your local machine:
```bash
# From your project directory
cd /Users/gilr/IdeaProjects/scrapper

# Copy entire project to EC2 (this may take a few minutes)
scp -i ~/.ssh/job-scraper-key.pem -r \
  .env.production \
  docker-compose.production.yml \
  Dockerfile \
  requirements.txt \
  src/ \
  config/ \
  scripts/ \
  deployment/ \
  alembic/ \
  alembic.ini \
  ubuntu@YOUR_EC2_IP:/tmp/scraper/

# Then in SSH session, move files
sudo mv /tmp/scraper/* /opt/scraper/
sudo chown -R scraper:scraper /opt/scraper
```

### Step 8: Configure Environment Variables

```bash
# Copy production template
cp .env.production .env

# Generate secure passwords
echo "Generating secure passwords..."
POSTGRES_PASS=$(openssl rand -base64 32)
REDIS_PASS=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -hex 32)

echo "POSTGRES_PASSWORD=$POSTGRES_PASS"
echo "REDIS_PASSWORD=$REDIS_PASS"
echo "JWT_SECRET_KEY=$JWT_SECRET"

# Edit .env file
vim .env
# Or use nano if you prefer: nano .env
```

**In the editor, update these values:**
```bash
# Required - use the generated passwords above
POSTGRES_PASSWORD=<paste POSTGRES_PASS here>
REDIS_PASSWORD=<paste REDIS_PASS here>
JWT_SECRET_KEY=<paste JWT_SECRET here>

# Required - add your API keys
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here  # Optional

# Optional - update if needed
POSTGRES_USER=scraper
POSTGRES_DB=scraper_db
```

**Save and exit:**
- In vim: Press `Esc`, type `:wq`, press Enter
- In nano: Press `Ctrl+X`, then `Y`, then Enter

### Step 9: Deploy Application

```bash
# Make deploy script executable
chmod +x deployment/deploy.sh

# Run deployment
./deployment/deploy.sh
```

**This will:**
1. Build Docker images (5-10 minutes first time)
2. Start all services
3. Run database migrations
4. Show service status

**Watch for:**
```
✓ Docker images built
✓ Services started
✓ Database migrations completed
✓ Deployment Complete!
```

---

## Phase 5: Verify Deployment (5 minutes)

### Step 10: Check Services

```bash
# Check all services are running
docker compose -f docker-compose.production.yml ps
```

**You should see 6 services with "Up" status:**
- scraper_postgres_prod
- scraper_redis_prod
- scraper_api_prod
- scraper_celery_worker_prod
- scraper_celery_beat_prod
- scraper_nginx_prod

### Step 11: Test API

**From EC2:**
```bash
# Test health endpoint
curl http://localhost/health

# Should return: {"status":"healthy"}
```

**From your local machine:**
```bash
# Test from external
curl http://YOUR_EC2_IP/health

# Test API docs
open http://YOUR_EC2_IP/docs  # Mac
# Or visit in browser: http://YOUR_EC2_IP/docs
```

### Step 12: Initialize Database

```bash
# Migrate companies to database
docker compose -f docker-compose.production.yml exec api python scripts/migrate_companies_to_db.py

# Verify companies were loaded
docker compose -f docker-compose.production.yml exec api python -c "
from src.database.session import get_db
from src.models.company import Company
db = next(get_db())
print(f'Companies in database: {db.query(Company).count()}')
"
```

---

## Phase 6: Monitor & Verify (5 minutes)

### Step 13: Check Logs

```bash
# View all logs
docker compose -f docker-compose.production.yml logs --tail=50

# View specific service logs
docker compose -f docker-compose.production.yml logs -f api
docker compose -f docker-compose.production.yml logs -f celery_worker
docker compose -f docker-compose.production.yml logs -f celery_beat

# Press Ctrl+C to stop following logs
```

### Step 14: Run Monitor Script

```bash
# Make monitor script executable
chmod +x deployment/monitor.sh

# Run monitoring
./deployment/monitor.sh
```

**This shows:**
- Service status
- Health checks
- Resource usage
- Database statistics
- Recent errors

---

## Phase 7: Setup Backups (5 minutes)

### Step 15: Test Backup

```bash
# Make backup script executable
chmod +x deployment/backup.sh

# Test backup
./deployment/backup.sh

# Verify backup was created
ls -lh backups/
```

### Step 16: Schedule Automated Backups

```bash
# Edit crontab
crontab -e

# Add this line (daily backup at 2 AM):
0 2 * * * /opt/scraper/deployment/backup.sh >> /opt/scraper/logs/backup.log 2>&1

# Save and exit
```

---

## 🎉 Deployment Complete!

Your Job Scraper is now running at:
- **API**: `http://YOUR_EC2_IP/`
- **Health**: `http://YOUR_EC2_IP/health`
- **Docs**: `http://YOUR_EC2_IP/docs`

---

## Next Steps (Optional)

### Setup SSL/HTTPS (Recommended)

If you have a domain name:
```bash
# Run SSL setup script
sudo /opt/scraper/deployment/setup_ssl.sh
```

### Test Scraping

```bash
# Run a test scrape
docker compose -f docker-compose.production.yml exec api python scripts/run_scraper.py
```

---

## Common Issues & Solutions

**Issue: Can't connect via SSH**
- Check security group allows your IP on port 22
- Verify key file permissions: `chmod 400 ~/.ssh/job-scraper-key.pem`
- Check you're using correct IP address

**Issue: Can't access API from browser**
- Check security group allows port 80 from 0.0.0.0/0
- Verify nginx is running: `docker compose -f docker-compose.production.yml ps nginx`
- Check firewall: `sudo ufw status`

**Issue: Services won't start**
- Check logs: `docker compose -f docker-compose.production.yml logs`
- Verify .env file has all required values
- Check disk space: `df -h`

**Issue: Database migrations fail**
- Check PostgreSQL is running: `docker compose -f docker-compose.production.yml ps postgres`
- Check database logs: `docker compose -f docker-compose.production.yml logs postgres`

---

## Useful Commands

```bash
# Restart all services
docker compose -f docker-compose.production.yml restart

# Restart specific service
docker compose -f docker-compose.production.yml restart api

# View logs
docker compose -f docker-compose.production.yml logs -f [service]

# Stop all services
docker compose -f docker-compose.production.yml down

# Start all services
docker compose -f docker-compose.production.yml up -d

# Shell access to container
docker compose -f docker-compose.production.yml exec api /bin/bash

# Database access
docker compose -f docker-compose.production.yml exec postgres psql -U scraper -d scraper_db
```

---

## Support

- Full documentation: `deployment/README.md`
- Monitoring: `./deployment/monitor.sh`
- Checklist: `deployment/DEPLOYMENT_CHECKLIST.md`

