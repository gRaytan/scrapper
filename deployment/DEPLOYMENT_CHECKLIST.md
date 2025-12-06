# Production Deployment Checklist

Use this checklist to ensure a smooth deployment to AWS EC2.

## Pre-Deployment

### AWS Setup
- [ ] AWS account created and configured
- [ ] EC2 instance launched (t3.medium or larger)
- [ ] Security group configured (ports 22, 80, 443)
- [ ] SSH key pair created and downloaded
- [ ] Elastic IP allocated (optional, for static IP)
- [ ] Domain name configured (optional, for HTTPS)

### Local Preparation
- [ ] Repository cloned locally
- [ ] All code tested locally
- [ ] Database migrations tested
- [ ] Environment variables documented
- [ ] API keys obtained (OpenAI, Anthropic)
- [ ] Companies configured in `config/companies.yaml`

---

## EC2 Instance Setup

### System Configuration
- [ ] Connected to EC2 via SSH
- [ ] Ran `setup_ec2.sh` script
- [ ] Docker installed and running
- [ ] Docker Compose installed
- [ ] User `scraper` created
- [ ] Application directories created (`/opt/scraper`)
- [ ] Firewall (UFW) configured
- [ ] Fail2ban configured
- [ ] Swap file created

### Application Setup
- [ ] Repository cloned to `/opt/scraper`
- [ ] `.env` file created from `.env.production`
- [ ] Strong passwords generated for:
  - [ ] PostgreSQL (`POSTGRES_PASSWORD`)
  - [ ] Redis (`REDIS_PASSWORD`)
  - [ ] JWT (`JWT_SECRET_KEY`)
- [ ] API keys added to `.env`:
  - [ ] `OPENAI_API_KEY`
  - [ ] `ANTHROPIC_API_KEY` (if using)
- [ ] Configuration files reviewed:
  - [ ] `config/companies.yaml`
  - [ ] `config/scraping_rules.yaml`

---

## Deployment

### Initial Deployment
- [ ] Deployment script made executable (`chmod +x deployment/deploy.sh`)
- [ ] Deployment script executed successfully
- [ ] All Docker containers started:
  - [ ] PostgreSQL
  - [ ] Redis
  - [ ] API
  - [ ] Celery Worker
  - [ ] Celery Beat
  - [ ] Nginx
- [ ] Database migrations ran successfully
- [ ] Companies migrated to database

### Verification
- [ ] All services showing as "Up" in `docker compose ps`
- [ ] API health check responds: `curl http://localhost/health`
- [ ] API accessible from external IP: `curl http://YOUR_EC2_IP/health`
- [ ] API documentation accessible: `http://YOUR_EC2_IP/docs`
- [ ] Database contains companies: Check via `monitor.sh`
- [ ] Workers are running: Check logs
- [ ] Beat scheduler is running: Check logs

---

## Post-Deployment

### Security
- [ ] SSL certificate obtained (Let's Encrypt or other)
- [ ] HTTPS configured in nginx
- [ ] HTTP to HTTPS redirect enabled
- [ ] Firewall rules verified
- [ ] SSH key-based authentication only
- [ ] Root login disabled
- [ ] Strong passwords used for all services
- [ ] `.env` file permissions set to 600

### Monitoring & Backups
- [ ] Backup script tested (`./deployment/backup.sh`)
- [ ] Automated backups configured (cron)
- [ ] Monitoring script tested (`./deployment/monitor.sh`)
- [ ] Log rotation configured
- [ ] Disk space monitoring setup
- [ ] CloudWatch alarms configured (optional)
- [ ] Sentry configured for error tracking (optional)

### Testing
- [ ] Manual scraping test successful
- [ ] Scheduled scraping verified (check after 24h)
- [ ] API endpoints tested:
  - [ ] GET `/health`
  - [ ] GET `/`
  - [ ] GET `/api/v1/scraper/jobs`
  - [ ] POST `/api/v1/scraper/scrape/company/{name}`
- [ ] Worker tasks tested:
  - [ ] Daily scraping
  - [ ] Single company scraping
  - [ ] Job processing
- [ ] Database queries working
- [ ] Logs being written correctly

---

## Ongoing Maintenance

### Daily
- [ ] Check service status: `docker compose ps`
- [ ] Review logs for errors
- [ ] Monitor disk space
- [ ] Verify backups are running

### Weekly
- [ ] Review scraping statistics
- [ ] Check for failed jobs
- [ ] Review security logs
- [ ] Update system packages

### Monthly
- [ ] Review and optimize database
- [ ] Clean old logs and backups
- [ ] Review resource usage
- [ ] Update application dependencies
- [ ] Review and update companies list

---

## Rollback Plan

If deployment fails:

1. **Stop services**:
   ```bash
   docker compose -f docker-compose.production.yml down
   ```

2. **Restore from backup** (if needed):
   ```bash
   gunzip < /opt/scraper/backups/scraper_db_TIMESTAMP.sql.gz | \
     docker compose -f docker-compose.production.yml exec -T postgres psql -U scraper -d scraper_db
   ```

3. **Revert code**:
   ```bash
   git checkout PREVIOUS_COMMIT
   ```

4. **Redeploy**:
   ```bash
   ./deployment/deploy.sh
   ```

---

## Emergency Contacts

- **AWS Support**: [AWS Console](https://console.aws.amazon.com/support)
- **Repository**: [GitHub Issues](https://github.com/YOUR_REPO/issues)
- **Documentation**: `/opt/scraper/deployment/README.md`

---

## Notes

Add any deployment-specific notes here:

- Deployment Date: _______________
- Deployed By: _______________
- EC2 Instance ID: _______________
- Public IP: _______________
- Domain: _______________
- Special Configurations: _______________

---

## Sign-off

- [ ] All checklist items completed
- [ ] Deployment verified and tested
- [ ] Documentation updated
- [ ] Team notified
- [ ] Monitoring confirmed

**Deployed by**: _______________  
**Date**: _______________  
**Signature**: _______________

