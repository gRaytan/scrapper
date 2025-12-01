# Worker-Orchestrator Integration - Technical Design

## Overview

This document describes the technical design for integrating the Celery worker system with the ScraperOrchestrator to enable automated, scheduled job scraping.

## Current State

### What Exists
- ✅ **ScraperOrchestrator** - Manages scraping sessions and coordinates scrapers
- ✅ **Celery Workers** - Background task processing infrastructure
- ✅ **Celery Tasks** - Pre-defined tasks in `src/workers/tasks.py`
- ✅ **Database Models** - Companies, JobPositions, ScrapingSessions

### What's Missing
- ❌ Workers are **NOT running** (Redis, Celery Worker, Celery Beat not started)
- ❌ No active connection between workers and orchestrator (exists but not executing)

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        TRIGGER LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  1. Celery Beat (Scheduler)     - Automatic (7:00 AM UTC daily) │
│  2. Manual Trigger Script        - On-demand (trigger_scraping)  │
│  3. API Endpoint (Future)        - REST API                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        QUEUE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  Redis (Message Broker)                                          │
│  - Database 1: Task Queue (pending tasks)                        │
│  - Database 2: Result Backend (task results)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      WORKER LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  Celery Workers (2 processes)                                    │
│  - Worker 1: Executes tasks from queue                           │
│  - Worker 2: Executes tasks from queue                           │
│                                                                   │
│  Tasks:                                                           │
│  • run_daily_scraping        - Scrape all companies              │
│  • scrape_single_company     - Scrape one company                │
│  • process_new_jobs          - Process new jobs                  │
│  • cleanup_old_sessions      - Database maintenance              │
│  • mark_stale_jobs_inactive  - Mark old jobs inactive            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  ScraperOrchestrator                                             │
│  - scrape_company(name, session, incremental)                    │
│  - scrape_all_companies(incremental)                             │
│  - _create_scraper(company_config)                               │
│  - _process_jobs(scraped_jobs, company, session)                 │
│  - _normalize_job_data(job_data)                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SCRAPER LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  Company-Specific Scrapers                                       │
│  - PlaywrightScraper (API, RSS, Workday, etc.)                   │
│  - StaticScraper (HTML parsing)                                  │
│                                                                   │
│  Parsers:                                                         │
│  - ComeetParser, GreenhouseParser, SmartRecruitersParser, etc.   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL Database                                             │
│  - companies (38 total, 37 active)                               │
│  - job_positions (109 from Monday.com)                           │
│  - scraping_sessions (2 sessions)                                │
│  - users (future)                                                │
│  - alerts (future)                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Integration Points

### 1. Task → Orchestrator Connection

**File:** `src/workers/tasks.py`

**Current Implementation:**
```python
@celery_app.task(bind=True, name='src.workers.tasks.run_daily_scraping')
def run_daily_scraping(self: Task) -> Dict[str, Any]:
    orchestrator = ScraperOrchestrator()
    results = asyncio.run(orchestrator.scrape_all_companies(incremental=False))
    return results
```

**How it works:**
1. Celery task creates an instance of `ScraperOrchestrator`
2. Calls `scrape_all_companies()` using `asyncio.run()` (since orchestrator is async)
3. Orchestrator manages the entire scraping workflow
4. Task returns results to Redis result backend

### 2. Orchestrator → Database Connection

**File:** `src/orchestrator/scraper_orchestrator.py`

**Current Implementation:**
```python
async def scrape_company(self, company_name: str, session: Session, incremental: bool = False):
    # Create scraping session in DB
    scraping_session = ScrapingSession(company_id=company.id, status='running')
    session.add(scraping_session)
    session.commit()
    
    # Scrape jobs
    scraped_jobs = await scraper.scrape()
    
    # Process jobs (create/update in DB)
    stats = await self._process_jobs(scraped_jobs, company, session, scraping_session)
    
    # Update session status
    scraping_session.status = 'completed'
    session.commit()
```

**Database Session Management:**
- Worker task creates DB session using `db.get_session()` context manager
- Passes session to orchestrator methods
- Session is committed/rolled back automatically

### 3. Orchestrator → Scraper Connection

**File:** `src/orchestrator/scraper_orchestrator.py`

**Current Implementation:**
```python
async def _create_scraper(self, company_config: dict):
    scraper_type = scraping_config.get("scraper_type", "static")
    
    if scraper_type in ["playwright", "api", "rss", "workday", ...]:
        return PlaywrightScraper(company_config, scraping_config)
    elif scraper_type == "static":
        return StaticScraper(company_config, scraping_config)
```

**How it works:**
1. Orchestrator reads company config from YAML
2. Creates appropriate scraper based on `scraper_type`
3. Scraper fetches jobs from company website/API
4. Returns normalized job data to orchestrator

## Data Flow

### Daily Scraping Flow

```
1. Celery Beat (7:00 AM UTC)
   ↓
2. Queue "run_daily_scraping" task → Redis
   ↓
3. Celery Worker picks up task
   ↓
4. Task creates ScraperOrchestrator instance
   ↓
5. Orchestrator.scrape_all_companies()
   ↓
6. For each active company:
   a. Create DB session
   b. Orchestrator.scrape_company(company_name, session)
   c. Create ScrapingSession (status=running)
   d. Create appropriate scraper (Playwright/Static)
   e. Scraper.scrape() → fetch jobs
   f. Orchestrator._process_jobs()
      - Normalize job data
      - Check if job exists (by external_id)
      - Create new job OR update existing job
      - Deactivate missing jobs
   g. Update ScrapingSession (status=completed)
   h. Commit DB session
   ↓
7. Task returns statistics
   ↓
8. Queue "process_new_jobs" task → Redis
   ↓
9. Worker processes new jobs (future: send notifications)
```

### Single Company Scraping Flow

```
1. Manual trigger: python scripts/trigger_scraping.py --task company --company "Monday.com"
   ↓
2. Queue "scrape_single_company" task → Redis
   ↓
3. Celery Worker picks up task
   ↓
4. Task creates ScraperOrchestrator instance
   ↓
5. Orchestrator.scrape_company("Monday.com", session, incremental=False)
   ↓
6. [Same as steps 6c-6h above]
   ↓
7. Task returns statistics
```

## Key Design Decisions

### 1. Async/Sync Boundary

**Problem:** Orchestrator is async, but Celery tasks are sync.

**Solution:** Use `asyncio.run()` in Celery tasks to bridge the gap.

```python
# In Celery task (sync)
def run_daily_scraping(self):
    orchestrator = ScraperOrchestrator()
    results = asyncio.run(orchestrator.scrape_all_companies())  # Bridge to async
    return results
```

### 2. Database Session Management

**Problem:** Who manages the database session lifecycle?

**Solution:** Worker task creates session, passes to orchestrator.

```python
# In Celery task
with db.get_session() as session:
    scraping_session = asyncio.run(
        orchestrator.scrape_company(company_name, session, incremental)
    )
```

**Benefits:**
- Clear ownership (task owns session)
- Automatic commit/rollback via context manager
- Orchestrator doesn't need to know about session lifecycle

### 3. Error Handling & Retries

**Problem:** What happens if scraping fails?

**Solution:** Multi-layer error handling.

**Layer 1: Orchestrator Level**
```python
try:
    scraped_jobs = await scraper.scrape()
except Exception as e:
    scraping_session.add_error("scraping_error", str(e))
    scraping_session.status = 'failed'
```

**Layer 2: Task Level**
```python
try:
    results = asyncio.run(orchestrator.scrape_all_companies())
except Exception as exc:
    logger.error(f"Daily scraping failed: {exc}")
    raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))
```

**Retry Strategy:**
- Max retries: 3
- Exponential backoff: 5 min, 10 min, 20 min
- After 3 failures, task is marked as failed

### 4. Deduplication Strategy

**Problem:** How to avoid duplicate jobs?

**Solution:** Database unique constraint + application logic.

**Database Level:**
```sql
CREATE UNIQUE INDEX ix_job_positions_external_id_company 
ON job_positions (external_id, company_id);
```

**Application Level:**
```python
existing_job = job_repo.get_by_external_id(external_id, company.id)
if existing_job:
    # Update existing job
    for key, value in job_data.items():
        setattr(existing_job, key, value)
else:
    # Create new job
    job_repo.create(job_data)
```

## Configuration

### Celery Beat Schedule

**File:** `src/workers/celery_app.py`

```python
beat_schedule={
    'daily-scraping': {
        'task': 'src.workers.tasks.run_daily_scraping',
        'schedule': crontab(hour=7, minute=0),  # 7:00 AM UTC daily
    },
    'weekly-cleanup': {
        'task': 'src.workers.tasks.cleanup_old_sessions',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
    },
    'daily-mark-stale-jobs': {
        'task': 'src.workers.tasks.mark_stale_jobs_inactive',
        'schedule': crontab(hour=4, minute=0),  # 4:00 AM UTC daily
    },
}
```

### Environment Variables

**File:** `.env`

```bash
# Database
DATABASE_URL=postgresql://scraper:password@localhost:5432/job_scraper_dev

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## Current Status

### ✅ What's Working
- ScraperOrchestrator can scrape companies
- Database integration works (jobs saved, sessions tracked)
- Deduplication works (no duplicate jobs)
- Field normalization works (is_remote → remote_type)
- Celery tasks are defined and registered

### ❌ What's NOT Working
- Redis is not running
- Celery workers are not running
- Celery Beat is not running
- No automatic scheduled scraping

### 🔄 What Needs to Happen

**To activate the worker system:**

1. Start Redis
2. Start Celery Worker
3. Start Celery Beat
4. (Optional) Start Flower for monitoring

**Commands:**
```bash
# Terminal 1: Redis
docker run -d -p 6379:6379 --name scraper-redis redis:7-alpine

# Terminal 2: Celery Worker
./scripts/start_worker.sh

# Terminal 3: Celery Beat
./scripts/start_beat.sh

# Terminal 4: Flower (optional)
celery -A src.workers.celery_app flower --port=5555
```

## Next Steps

See [WORKER_ORCHESTRATOR_SETUP.md](./WORKER_ORCHESTRATOR_SETUP.md) for step-by-step setup instructions.

