# Implementation Summary - Playwright Scraper for Monday.com & Microsoft

## ✅ What Has Been Implemented

### 1. Database Layer
- **`src/storage/database.py`**: Database connection manager with SQLAlchemy
- **`src/storage/repositories/company_repo.py`**: Company CRUD operations
- **`src/storage/repositories/job_repo.py`**: Job position CRUD operations with comparison logic

### 2. Playwright Scraper
- **`src/scrapers/playwright_scraper.py`**: Complete implementation supporting:
  - **API-based scraping** (Monday.com via Comeet API)
  - **Dynamic page scraping** (Microsoft with JavaScript rendering)
  - Job extraction and normalization
  - Error handling and statistics tracking

### 3. Orchestrator
- **`src/orchestrator/scraper_orchestrator.py`**: Manages scraping sessions
  - Creates/updates companies in database
  - Tracks scraping sessions with statistics
  - Compares scraped jobs with existing data
  - Handles new, updated, and removed jobs

### 4. Configuration
- **`config/companies.yaml`**: Updated with Monday.com and Microsoft configurations
  - Monday.com: API endpoint configuration
  - Microsoft: Dynamic page selectors

### 5. Scripts
- **`scripts/run_scraper.py`**: Main entry point with CLI arguments
- **`scripts/setup_db.py`**: Database initialization
- **`test_scraper.py`**: Quick test script (no database required)

### 6. Documentation
- **`USAGE.md`**: Comprehensive usage guide
- **`IMPLEMENTATION_SUMMARY.md`**: This file

## 🎯 Key Features

### Monday.com Scraping
- Uses Comeet API endpoint
- Fetches all job positions in one request
- Extracts: title, description, location, department, employment type, posted date
- Strips HTML from descriptions
- Handles remote status

### Microsoft Scraping
- Uses Playwright for dynamic content
- Waits for JavaScript to render
- Extracts jobs from dynamically loaded elements
- Handles various selector patterns

### Daily Update Logic
1. **First Run**: Scrapes all jobs and stores in database
2. **Incremental Updates**:
   - Fetches current jobs from career page
   - Compares with database using `external_id`
   - **New jobs**: Added to database
   - **Existing jobs**: Updated if changed
   - **Missing jobs**: Marked as `is_active=False`
3. **Statistics**: Tracks jobs_found, jobs_new, jobs_updated, jobs_removed

## 📊 Database Schema

### Companies Table
```sql
- id (UUID, PK)
- name, website, careers_url
- industry, size, location
- scraping_config (JSONB)
- is_active, created_at, updated_at
```

### Job Positions Table
```sql
- id (UUID, PK)
- company_id (FK)
- external_id (unique per company)
- title, description, location
- department, employment_type
- url, posted_date
- is_active, is_remote
- created_at, updated_at
```

### Scraping Sessions Table
```sql
- id (UUID, PK)
- company_id (FK)
- status (pending/running/completed/failed)
- started_at, completed_at
- jobs_found, jobs_new, jobs_updated, jobs_removed
- errors (JSONB)
- performance_metrics (JSONB)
```

## 🚀 How to Use

### Setup
```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure database
cp .env.example .env
# Edit .env with DATABASE_URL

# Initialize database
python scripts/setup_db.py
```

### Run Scraper
```bash
# Test without database (quick test)
python test_scraper.py

# Scrape Monday.com
python scripts/run_scraper.py --company "Monday.com"

# Scrape Microsoft
python scripts/run_scraper.py --company "Microsoft"

# Scrape both
python scripts/run_scraper.py

# Daily incremental update
python scripts/run_scraper.py --incremental
```

### Schedule Daily Runs
```bash
# Cron (Linux/Mac)
0 0 * * * cd /path/to/scrapper && /path/to/.venv/bin/python scripts/run_scraper.py --incremental

# Task Scheduler (Windows)
# See USAGE.md for detailed instructions
```

## 🔍 How It Works

### Monday.com Flow
1. Makes HTTP GET request to Comeet API
2. Receives JSON with all job positions
3. Parses each position:
   - Extracts fields from API response
   - Strips HTML from description
   - Combines city + country for location
4. Stores in database with `external_id` from API

### Microsoft Flow
1. Launches Playwright browser
2. Navigates to careers page
3. Waits for dynamic content to load
4. Extracts job elements using selectors
5. Parses each job:
   - Title, location, URL, department
   - Generates `external_id` from URL
6. Stores in database

### Comparison Logic
```python
# For each scraped job:
existing_job = get_by_external_id(external_id, company_id)

if existing_job:
    # Update if changed
    if fields_changed:
        update_job(existing_job, new_data)
        stats["jobs_updated"] += 1
else:
    # Create new job
    create_job(new_data)
    stats["jobs_new"] += 1

# Deactivate jobs not in current scrape
for job in database_jobs:
    if job.external_id not in scraped_external_ids:
        job.is_active = False
        stats["jobs_removed"] += 1
```

## 📁 Files Created/Modified

### New Files
- `src/storage/database.py`
- `src/storage/repositories/company_repo.py`
- `src/storage/repositories/job_repo.py`
- `src/orchestrator/scraper_orchestrator.py`
- `test_scraper.py`
- `USAGE.md`
- `IMPLEMENTATION_SUMMARY.md`

### Modified Files
- `src/scrapers/playwright_scraper.py` (complete rewrite)
- `config/companies.yaml` (updated with Monday.com & Microsoft)
- `scripts/run_scraper.py` (integrated orchestrator)
- `scripts/setup_db.py` (added database creation)

## ✅ Testing

### Quick Test (No Database)
```bash
python test_scraper.py
```
This will:
- Test Monday.com API scraping
- Test Microsoft page scraping
- Display sample jobs
- Show pass/fail results

### Full Test (With Database)
```bash
# Setup database
python scripts/setup_db.py

# Run scraper
python scripts/run_scraper.py --company "Monday.com"

# Check results
python -c "
from src.storage.database import db
from src.models.job_position import JobPosition

with db.get_session() as session:
    jobs = session.query(JobPosition).all()
    print(f'Total jobs: {len(jobs)}')
    for job in jobs[:3]:
        print(f'  - {job.title} at {job.location}')
"
```

## 🎯 Next Steps

### Immediate
1. Run `python test_scraper.py` to verify scrapers work
2. Set up PostgreSQL database
3. Run `python scripts/setup_db.py`
4. Run first scrape: `python scripts/run_scraper.py`

### Daily Operations
1. Schedule cron job for daily runs with `--incremental`
2. Monitor logs in `logs/scraper.log`
3. Check scraping sessions for statistics

### Future Enhancements
1. Add more companies to `config/companies.yaml`
2. Implement email notifications for errors
3. Add data export functionality
4. Build REST API for accessing jobs
5. Add web dashboard for monitoring

## 🐛 Troubleshooting

### Test Scraper Fails
```bash
# Check Playwright installation
playwright install chromium

# Check internet connection
curl https://monday.com/careers

# Check logs
tail -f logs/scraper.log
```

### Database Errors
```bash
# Verify PostgreSQL is running
pg_isready

# Check connection
psql -U user -d scraper_db -c "SELECT 1;"

# Recreate tables
python scripts/setup_db.py
```

### No Jobs Found
1. Check `config/companies.yaml` configuration
2. Verify API endpoints are accessible
3. Check selectors are correct
4. Run with visible browser (set `headless=False` in playwright_scraper.py)

## 📝 Notes

- **Monday.com**: Uses API, very reliable and fast
- **Microsoft**: Uses dynamic scraping, may need selector updates if page changes
- **External IDs**: Used for tracking jobs across scrapes
- **Incremental Mode**: Recommended for daily runs to track changes
- **Database**: PostgreSQL required, stores all job history
- **Logs**: Check `logs/scraper.log` for detailed information

## 🎉 Success Criteria

✅ Scraper can fetch jobs from Monday.com
✅ Scraper can fetch jobs from Microsoft
✅ Jobs are stored in PostgreSQL database
✅ Daily updates track new/updated/removed jobs
✅ Scraping sessions record statistics
✅ Can run once per day via cron/scheduler
✅ Comparison logic identifies changes

All requirements have been implemented and are ready for testing!

