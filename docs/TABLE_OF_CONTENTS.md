# Documentation Table of Contents

> **⚠️ IMPORTANT:** Always check this file before making decisions or looking for documentation.
> Each topic has ONE source of truth document - use that document, not others.

---

## Quick Reference

| Topic | Source of Truth |
|-------|-----------------|
| **EC2 Deployment & Operations** | [docs/EC2_OPERATIONS.md](./EC2_OPERATIONS.md) |
| **API Usage & Endpoints** | [docs/API_USAGE.md](./API_USAGE.md) |
| **Architecture Overview** | [docs/ARCHITECTURE.md](./ARCHITECTURE.md) |
| **Database Models** | [docs/MODELS_CREATED.md](./MODELS_CREATED.md) |
| **Adding New Companies** | [docs/ADDING_NEW_COMPANIES.md](./ADDING_NEW_COMPANIES.md) |
| **Creating Alerts** | [docs/CREATE_ALERT_GUIDE.md](./CREATE_ALERT_GUIDE.md) |
| **Initial EC2 Setup** | [deployment/README.md](../deployment/README.md) |

---

## Operations & Deployment

### EC2 Server Operations (Daily Use)
**Source of Truth:** [`docs/EC2_OPERATIONS.md`](./EC2_OPERATIONS.md)

Covers:
- Deploying code changes (rsync + deploy.sh)
- Docker container management
- Viewing logs
- Database backups and restores
- Troubleshooting

### Initial EC2 Setup (One-Time)
**Source of Truth:** [`deployment/README.md`](../deployment/README.md)

Covers:
- Launching EC2 instance
- Installing Docker
- Initial configuration
- SSL setup

### Deployment Scripts
| Script | Purpose |
|--------|---------|
| `deployment/deploy.sh` | Deploy code on EC2 (restart/build/full) |
| `deployment/backup.sh` | Database backup |
| `deployment/monitor.sh` | System monitoring |
| `deployment/setup_ec2.sh` | Initial EC2 setup |
| `deployment/setup_ssl.sh` | SSL certificate setup |

---

## API & Development

### API Endpoints
**Source of Truth:** [`docs/API_USAGE.md`](./API_USAGE.md)

### Architecture
**Source of Truth:** [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md)

### Database Models
**Source of Truth:** [`docs/MODELS_CREATED.md`](./MODELS_CREATED.md)

### Technical Design
**Source of Truth:** [`docs/TECHNICAL_DESIGN.md`](./TECHNICAL_DESIGN.md)

---

## Features

### Job Alerts
**Source of Truth:** [`docs/CREATE_ALERT_GUIDE.md`](./CREATE_ALERT_GUIDE.md)

Related: [`docs/RETRIEVE_ALERT_JOBS_GUIDE.md`](./RETRIEVE_ALERT_JOBS_GUIDE.md)

### Adding New Companies
**Source of Truth:** [`docs/ADDING_NEW_COMPANIES.md`](./ADDING_NEW_COMPANIES.md)

Related: [`docs/RECOMMENDED_COMPANIES_TO_ADD.md`](./RECOMMENDED_COMPANIES_TO_ADD.md)

### Location Filtering
**Source of Truth:** [`docs/LOCATION_FILTERING.md`](./LOCATION_FILTERING.md)

### Workers & Background Jobs
**Source of Truth:** [`docs/WORKER_ORCHESTRATOR_INTEGRATION.md`](./WORKER_ORCHESTRATOR_INTEGRATION.md)

---

## Product Requirements (PRDs)

| Document | Description |
|----------|-------------|
| [`docs/PRD_Job_Scraping_Platform.md`](./PRD_Job_Scraping_Platform.md) | Main platform PRD |
| [`docs/PRD_JOB_NOTIFICATION_SYSTEM.md`](./PRD_JOB_NOTIFICATION_SYSTEM.md) | Notification system PRD |
| [`docs/API_PRD.md`](./API_PRD.md) | API requirements |

---

## Historical / Reference Only

These documents are for reference but may be outdated. Check source of truth docs above first.

| Document | Notes |
|----------|-------|
| `deployment/DEPLOYMENT_SUMMARY.md` | Overview only, not actionable |
| `docs/IMPLEMENTATION_ROADMAP.md` | Historical implementation notes |
| `docs/GETTING_STARTED.md` | May be outdated |
| `docs/*_SUMMARY.md` | Historical summaries |
| `docs/*_COMPLETE.md` | Historical completion notes |

---

## Configuration Files

| File | Purpose |
|------|---------|
| `config/companies.yaml` | Company scraping configuration |
| `config/linkedin_only_companies.yaml` | LinkedIn-only companies |
| `config/settings.py` | Application settings |
| `.env` | Environment variables (on EC2 only) |
| `docker-compose.production.yml` | Production Docker config |

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/run_scraper.py` | Manual scraper execution |
| `scripts/query_db.py` | Database queries |
| `scripts/migrate_companies_to_db.py` | Migrate companies from YAML to DB |

---

*Last updated: 2026-02-27*

