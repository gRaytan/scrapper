# Celery Workers for Job Scraping

This directory contains the Celery worker infrastructure for background job processing and scheduled scraping tasks.

## Overview

The worker system consists of:
- **Celery App** (`celery_app.py`): Main Celery application configuration
- **Tasks** (`tasks.py`): Background tasks for scraping, processing, and maintenance
- **Scripts**: Helper scripts to start workers and trigger tasks

## Architecture

```
┌─────────────────┐
│  Celery Beat    │  ← Scheduler (triggers tasks at scheduled times)
│  (Scheduler)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Redis Queue    │  ← Message broker (stores task queue)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Celery Workers  │  ← Execute tasks (scraping, processing, etc.)
│  (2 processes)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │  ← Store results (jobs, sessions, etc.)
└─────────────────┘
```

## Tasks

### Scheduled Tasks (Automatic)

These tasks run automatically via Celery Beat:

| Task | Schedule | Description |
|------|----------|-------------|
| `run_daily_scraping` | Daily at 7:00 AM UTC (9-10 AM Israel time) | Scrapes all active companies |
| `cleanup_old_sessions` | Weekly (Sunday 3:00 AM UTC) | Removes scraping sessions older than 90 days |
| `mark_stale_jobs_inactive` | Daily at 4:00 AM UTC | Marks jobs inactive if not updated in 60 days |

### Manual Tasks

These tasks can be triggered manually:

| Task | Description | Usage |
|------|-------------|-------|
| `scrape_single_company` | Scrape a specific company | `python scripts/trigger_scraping.py --task company --company "Meta"` |
| `process_new_jobs` | Process new jobs from last N hours | `python scripts/trigger_scraping.py --task process --hours 24` |
| `get_scraping_stats` | Get scraping statistics | `python scripts/trigger_scraping.py --task stats --days 7` |

## Setup

### 1. Install Dependencies

```bash
pip install celery redis
```

### 2. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or using docker-compose
docker-compose up -d redis
```

### 3. Configure Environment

Make sure your `.env` file has:

```bash
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## Running Workers

### Start Celery Worker

```bash
# Using the helper script
./scripts/start_worker.sh

# Or manually
celery -A src.workers.celery_app worker --loglevel=info
```

### Start Celery Beat (Scheduler)

```bash
# Using the helper script
./scripts/start_beat.sh

# Or manually
celery -A src.workers.celery_app beat --loglevel=info
```

### Run Both Together

```bash
# In separate terminals
Terminal 1: ./scripts/start_worker.sh
Terminal 2: ./scripts/start_beat.sh

# Or in one terminal (not recommended for production)
celery -A src.workers.celery_app worker --beat --loglevel=info
```

## Triggering Tasks Manually

### Daily Scraping

```bash
# Run synchronously (wait for completion)
python scripts/trigger_scraping.py --task daily

# Run asynchronously (queue and return immediately)
python scripts/trigger_scraping.py --task daily --async
```

### Scrape Single Company

```bash
# Full scrape
python scripts/trigger_scraping.py --task company --company "Meta"

# Incremental scrape (last 24 hours only)
python scripts/trigger_scraping.py --task company --company "Amazon" --incremental

# Async
python scripts/trigger_scraping.py --task company --company "Wiz" --async
```

### Process New Jobs

```bash
# Process jobs from last 24 hours
python scripts/trigger_scraping.py --task process

# Process jobs from last 48 hours
python scripts/trigger_scraping.py --task process --hours 48
```

### Database Maintenance

```bash
# Cleanup old sessions (keep last 90 days)
python scripts/trigger_scraping.py --task cleanup

# Cleanup old sessions (keep last 30 days)
python scripts/trigger_scraping.py --task cleanup --days 30

# Mark stale jobs inactive (not updated in 60 days)
python scripts/trigger_scraping.py --task mark-stale

# Mark stale jobs inactive (not updated in 30 days)
python scripts/trigger_scraping.py --task mark-stale --days 30
```

### Get Statistics

```bash
# Get stats for last 7 days
python scripts/trigger_scraping.py --task stats

# Get stats for last 30 days
python scripts/trigger_scraping.py --task stats --days 30
```

## Monitoring

### Check Task Status

```bash
# List active tasks
celery -A src.workers.celery_app inspect active

# List scheduled tasks
celery -A src.workers.celery_app inspect scheduled

# List registered tasks
celery -A src.workers.celery_app inspect registered

# Get worker stats
celery -A src.workers.celery_app inspect stats
```

### Check Task Result

```bash
# Get result of a specific task
celery -A src.workers.celery_app result <task-id>
```

### Flower (Web UI)

```bash
# Install Flower
pip install flower

# Start Flower
celery -A src.workers.celery_app flower --port=5555

# Open http://localhost:5555 in browser
```

## Configuration

### Celery Settings

Key configuration in `celery_app.py`:

- **Broker**: Redis database 1 (`redis://localhost:6379/1`)
- **Backend**: Redis database 2 (`redis://localhost:6379/2`)
- **Timezone**: UTC
- **Task time limit**: 1 hour (hard), 55 minutes (soft)
- **Worker concurrency**: 2 processes
- **Max tasks per child**: 50 (prevents memory leaks)

### Modifying Schedule

Edit `celery_app.py` to change task schedules:

```python
beat_schedule={
    'daily-scraping': {
        'task': 'src.workers.tasks.run_daily_scraping',
        'schedule': crontab(hour=7, minute=0),  # Change time here
    },
}
```

Crontab examples:
- `crontab(hour=7, minute=0)` - Daily at 7:00 AM
- `crontab(hour='*/6')` - Every 6 hours
- `crontab(day_of_week=0, hour=3)` - Sunday at 3:00 AM
- `crontab(minute='*/30')` - Every 30 minutes

## Production Deployment

### Using Systemd (Linux)

Create `/etc/systemd/system/celery-worker.service`:

```ini
[Unit]
Description=Celery Worker
After=network.target redis.service postgresql.service

[Service]
Type=forking
User=scraper
Group=scraper
WorkingDirectory=/path/to/scrapper
Environment="PYTHONPATH=/path/to/scrapper"
ExecStart=/path/to/venv/bin/celery -A src.workers.celery_app worker --detach --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/celery-beat.service`:

```ini
[Unit]
Description=Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=scraper
Group=scraper
WorkingDirectory=/path/to/scrapper
Environment="PYTHONPATH=/path/to/scrapper"
ExecStart=/path/to/venv/bin/celery -A src.workers.celery_app beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
sudo systemctl status celery-worker celery-beat
```

### Using Docker Compose

Already configured in `docker-compose.yml`:

```bash
docker-compose up -d celery-worker celery-beat
```

## Troubleshooting

### Worker not picking up tasks

1. Check Redis is running: `redis-cli ping`
2. Check worker is running: `celery -A src.workers.celery_app inspect active`
3. Check task is registered: `celery -A src.workers.celery_app inspect registered`

### Tasks failing

1. Check worker logs: `celery -A src.workers.celery_app events`
2. Check task result: `celery -A src.workers.celery_app result <task-id>`
3. Enable debug logging: `celery -A src.workers.celery_app worker --loglevel=debug`

### Beat not scheduling tasks

1. Check beat is running: `ps aux | grep celery`
2. Check schedule file: `cat /tmp/celerybeat-schedule`
3. Restart beat: `pkill -f "celery.*beat" && ./scripts/start_beat.sh`

## Next Steps

1. **Test the workers** - Run a test scraping task
2. **Monitor performance** - Use Flower to monitor task execution
3. **Add notifications** - Implement email/Slack notifications for task failures
4. **Scale workers** - Add more worker processes for parallel execution
5. **Add user alerts** - Implement job matching and user notification system

