# Usage Guide - Monday.com & Microsoft Scraper

This guide explains how to use the career page scraper for Monday.com and Microsoft.

## Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python scripts/setup_db.py
```

### 2. Run Scraper

```bash
# Scrape Monday.com
python scripts/run_scraper.py --company "Monday.com"

# Scrape Microsoft
python scripts/run_scraper.py --company "Microsoft"

# Scrape both companies
python scripts/run_scraper.py
```

## How It Works

### Monday.com

- **Method**: API-based scraping
- **Endpoint**: Comeet API (`https://www.comeet.co/careers-api/2.0/company/41.00B/positions`)
- **Data**: Returns JSON with all job positions
- **Fields Extracted**:
  - Job title
  - Description (HTML stripped)
  - Location (city, country)
  - Department
  - Employment type
  - Posted/updated date
  - Remote status

### Microsoft

- **Method**: Playwright browser automation
- **URL**: `https://careers.microsoft.com/`
- **Approach**: Dynamic page rendering with JavaScript
- **Fields Extracted**:
  - Job title
  - Location
  - Job URL
  - Department
  - Employment type

## Daily Update Strategy

### First Run (Full Scrape)

```bash
python scripts/run_scraper.py --company "Monday.com"
```

- Fetches ALL jobs from the career page
- Stores them in the database
- Marks all as `is_active=True`

### Daily Incremental Update

```bash
python scripts/run_scraper.py --company "Monday.com" --incremental
```

- Fetches current jobs from the career page
- Compares with existing database records using `external_id`
- **New jobs**: Added to database
- **Existing jobs**: Updates if any fields changed
- **Missing jobs**: Marks as `is_active=False` (removed from career page)

### Statistics Tracked

Each scraping session records:
- `jobs_found`: Total jobs in current scrape
- `jobs_new`: New jobs added
- `jobs_updated`: Existing jobs updated
- `jobs_removed`: Jobs marked as inactive

## Database Schema

### Companies
```sql
id              UUID PRIMARY KEY
name            VARCHAR
website         VARCHAR
careers_url     VARCHAR
industry        VARCHAR
size            VARCHAR
location        VARCHAR
scraping_config JSONB
is_active       BOOLEAN
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### Job Positions
```sql
id              UUID PRIMARY KEY
company_id      UUID FOREIGN KEY
external_id     VARCHAR (unique per company)
title           VARCHAR
description     TEXT
location        VARCHAR
department      VARCHAR
employment_type VARCHAR
url             VARCHAR
posted_date     TIMESTAMP
is_active       BOOLEAN
is_remote       BOOLEAN
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### Scraping Sessions
```sql
id                  UUID PRIMARY KEY
company_id          UUID FOREIGN KEY
status              VARCHAR (pending/running/completed/failed)
started_at          TIMESTAMP
completed_at        TIMESTAMP
jobs_found          INTEGER
jobs_new            INTEGER
jobs_updated        INTEGER
jobs_removed        INTEGER
errors              JSONB
performance_metrics JSONB
```

## Scheduling Daily Runs

### Linux/Mac (Cron)

```bash
# Edit crontab
crontab -e

# Add daily run at midnight
0 0 * * * cd /path/to/scrapper && /path/to/.venv/bin/python scripts/run_scraper.py --incremental >> logs/cron.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task → "Daily Scraper"
3. Trigger: Daily at 00:00
4. Action: Start a program
   - Program: `C:\path\to\.venv\Scripts\python.exe`
   - Arguments: `scripts/run_scraper.py --incremental`
   - Start in: `C:\path\to\scrapper`

## Monitoring

### View Logs

```bash
# Real-time logs
tail -f logs/scraper.log

# Error logs
tail -f logs/error.log
```

### Check Scraping History

```python
from src.storage.database import db
from src.models.scraping_session import ScrapingSession

with db.get_session() as session:
    sessions = session.query(ScrapingSession).order_by(
        ScrapingSession.started_at.desc()
    ).limit(10).all()
    
    for s in sessions:
        print(f"{s.company.name}: {s.status}")
        print(f"  New: {s.jobs_new}, Updated: {s.jobs_updated}, Removed: {s.jobs_removed}")
```

### Query Jobs

```python
from src.storage.database import db
from src.models.job_position import JobPosition
from src.models.company import Company

with db.get_session() as session:
    # Get all active jobs for Monday.com
    company = session.query(Company).filter(Company.name == "Monday.com").first()
    jobs = session.query(JobPosition).filter(
        JobPosition.company_id == company.id,
        JobPosition.is_active == True
    ).all()
    
    print(f"Active jobs: {len(jobs)}")
    for job in jobs[:5]:
        print(f"  - {job.title} ({job.location})")
```

## Troubleshooting

### No Jobs Found

1. Check company configuration in `config/companies.yaml`
2. Verify API endpoint is accessible
3. Check logs for errors: `tail -f logs/scraper.log`

### Database Connection Error

```bash
# Test PostgreSQL connection
psql -U user -d scraper_db -c "SELECT 1;"

# Verify .env settings
cat .env | grep DATABASE_URL
```

### Playwright Issues

```bash
# Reinstall browsers
playwright install --force chromium

# Test browser
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); print('OK')"
```

## Adding New Companies

1. Edit `config/companies.yaml`:

```yaml
companies:
  - name: "New Company"
    website: "https://newcompany.com"
    careers_url: "https://newcompany.com/careers"
    industry: "Technology"
    size: "1000-5000"
    location: "City, Country"
    is_active: true
    scraping_frequency: "0 0 * * *"
    scraping_config:
      scraper_type: "playwright"
      pagination_type: "dynamic"
      requires_js: true
      wait_time: 3
      selectors:
        job_item: "div.job-card"
        job_title: "h3.title"
        job_location: "span.location"
        job_url: "a.apply-link"
```

2. Run scraper:

```bash
python scripts/run_scraper.py --company "New Company"
```

## Best Practices

1. **First Run**: Always do a full scrape first
2. **Daily Updates**: Use `--incremental` flag for daily runs
3. **Monitoring**: Check logs regularly for errors
4. **Database Backups**: Backup PostgreSQL database regularly
5. **Rate Limiting**: Respect website rate limits (configured in `wait_time`)

## Support

For issues:
1. Check logs in `logs/scraper.log`
2. Verify configuration in `config/companies.yaml`
3. Test database connection
4. Check Playwright installation

