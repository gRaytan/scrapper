# Deployment Guide

## Backend API Deployment (EC2)

### Prerequisites
- SSH key: `~/IdeaProjects/pem/hiddenjobs-key.pem`
- Production server: `ubuntu@api.hiddenjobs.me`
- Deployment directory: `/opt/scraper`

### Deployment Process

**IMPORTANT: You MUST rebuild containers after code changes. Restarting is NOT enough!**

#### Step 1: Commit and Push Changes
```bash
# Commit your changes locally
git add .
git commit -m "Your commit message"

# Push to GitHub (optional but recommended)
git push origin main

# Push to EC2 production
GIT_SSH_COMMAND="ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem" git push ec2 main
```

#### Step 2: SSH to Production and Sync Files
```bash
ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@api.hiddenjobs.me

# Once connected, sync files from git repo to deployment directory
sudo rsync -av --delete /home/ubuntu/scraper-upload/ /opt/scraper/ \
  --exclude='.git' --exclude='__pycache__' --exclude='*.pyc'
```

#### Step 3: Rebuild and Restart Containers
```bash
cd /opt/scraper

# CRITICAL: Build with --no-cache to ensure code changes are picked up
sudo docker compose -f docker-compose.production.yml build --no-cache

# Restart all services
sudo docker compose -f docker-compose.production.yml up -d
```

**Alternative: Rebuild specific service only**
```bash
# If only API code changed
sudo docker compose -f docker-compose.production.yml build --no-cache api
sudo docker compose -f docker-compose.production.yml up -d api

# If only worker code changed
sudo docker compose -f docker-compose.production.yml build --no-cache celery_worker celery_beat
sudo docker compose -f docker-compose.production.yml up -d celery_worker celery_beat
```

#### Step 4: Verify Deployment
```bash
# Check container status
sudo docker compose -f docker-compose.production.yml ps

# Check API logs
sudo docker compose -f docker-compose.production.yml logs --tail=50 api

# Test API endpoint
curl https://api.hiddenjobs.me/health
```

### Why Restart Alone Doesn't Work

**Docker containers copy code during build, not at runtime:**
- Code is `COPY`'d into the image during `docker build`
- Restarting just restarts the existing container with old code
- You MUST rebuild to pick up code changes

### Common Mistakes to Avoid

❌ **DON'T**: Just restart containers after code changes
```bash
# This WON'T pick up code changes!
sudo docker compose -f docker-compose.production.yml restart api
```

✅ **DO**: Rebuild then restart
```bash
# This WILL pick up code changes
sudo docker compose -f docker-compose.production.yml build --no-cache api
sudo docker compose -f docker-compose.production.yml up -d api
```

### Quick Reference Commands

```bash
# Full deployment (from local machine)
GIT_SSH_COMMAND="ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem" git push ec2 main && \
ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@api.hiddenjobs.me \
  "sudo rsync -av --delete /home/ubuntu/scraper-upload/ /opt/scraper/ --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' && \
   cd /opt/scraper && \
   sudo docker compose -f docker-compose.production.yml build --no-cache && \
   sudo docker compose -f docker-compose.production.yml up -d"
```

---

## Frontend Deployment (Vercel)

### Deployment Process

```bash
cd ~/IdeaProjects/HiddenJobs/hiddenjobs-portal

# Commit changes
git add .
git commit -m "Your commit message"

# Deploy to production
vercel --prod
```

### Verify Deployment
- Live URL: https://hiddenjobs.me
- Check browser console for errors
- Test authentication flow

---

## Database Migrations

### Running Migrations on Production

```bash
ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@api.hiddenjobs.me

cd /opt/scraper

# Run migrations
sudo docker compose -f docker-compose.production.yml exec api alembic upgrade head

# Check current version
sudo docker compose -f docker-compose.production.yml exec api alembic current
```

---

## Troubleshooting

### Issue: Code changes not reflected after restart
**Solution**: You forgot to rebuild. Run:
```bash
sudo docker compose -f docker-compose.production.yml build --no-cache
sudo docker compose -f docker-compose.production.yml up -d
```

### Issue: Git push says "Everything up-to-date" but production has old code
**Solution**: The git push worked, but you need to sync and rebuild:
```bash
ssh -i ~/IdeaProjects/pem/hiddenjobs-key.pem ubuntu@api.hiddenjobs.me
sudo rsync -av --delete /home/ubuntu/scraper-upload/ /opt/scraper/ --exclude='.git'
cd /opt/scraper
sudo docker compose -f docker-compose.production.yml build --no-cache
sudo docker compose -f docker-compose.production.yml up -d
```

### Issue: Container won't start after rebuild
**Solution**: Check logs for errors:
```bash
sudo docker compose -f docker-compose.production.yml logs --tail=100 api
```

