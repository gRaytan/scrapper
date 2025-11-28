# Code Examples & SQL Queries
## Job Notification System

**Last Updated:** November 20, 2025

---

## 📋 Table of Contents

1. [Database Queries](#database-queries)
2. [API Examples](#api-examples)
3. [Matching Algorithm Examples](#matching-algorithm-examples)
4. [Email Template Examples](#email-template-examples)
5. [Celery Task Examples](#celery-task-examples)

---

## 🗄️ Database Queries

### Get New Jobs from Last 24 Hours

```sql
-- Get all new jobs created in the last 24 hours
SELECT 
    jp.id,
    jp.title,
    jp.location,
    jp.department,
    jp.posted_date,
    c.name as company_name,
    jp.job_url
FROM job_positions jp
JOIN companies c ON jp.company_id = c.id
WHERE 
    jp.created_at >= NOW() - INTERVAL '24 hours'
    AND jp.is_active = true
ORDER BY jp.created_at DESC;
```

### Get Active Alerts for a User

```sql
-- Get all active alerts for a specific user
SELECT 
    ja.id,
    ja.name,
    ja.filters,
    ja.notification_frequency,
    ja.last_notified_at,
    COUNT(n.id) as notification_count
FROM job_alerts ja
LEFT JOIN notifications n ON ja.id = n.alert_id
WHERE 
    ja.user_id = '123e4567-e89b-12d3-a456-426614174000'
    AND ja.is_active = true
GROUP BY ja.id
ORDER BY ja.created_at DESC;
```

### Get Matching Jobs for Alert Filters

```sql
-- Find jobs matching specific criteria
SELECT 
    jp.id,
    jp.title,
    c.name as company_name,
    jp.location,
    jp.department,
    jp.posted_date
FROM job_positions jp
JOIN companies c ON jp.company_id = c.id
WHERE 
    jp.is_active = true
    AND c.name IN ('Monday.com', 'Wiz', 'Meta')  -- Company filter
    AND jp.location IN ('Tel Aviv', 'Herzliya')  -- Location filter
    AND (
        jp.title ILIKE '%backend%' 
        OR jp.title ILIKE '%python%'
        OR jp.description ILIKE '%backend%'
        OR jp.description ILIKE '%python%'
    )  -- Keyword filter
    AND jp.posted_date >= NOW() - INTERVAL '7 days'  -- Recent jobs
ORDER BY jp.posted_date DESC;
```

### Get User Notification History

```sql
-- Get notification history for a user
SELECT 
    n.id,
    n.type,
    n.title,
    n.created_at,
    n.is_read,
    n.read_at,
    ja.name as alert_name,
    jsonb_array_length(n.data->'job_ids') as job_count
FROM notifications n
LEFT JOIN job_alerts ja ON n.alert_id = ja.id
WHERE 
    n.user_id = '123e4567-e89b-12d3-a456-426614174000'
ORDER BY n.created_at DESC
LIMIT 50;
```

### Get Scraping Statistics

```sql
-- Get scraping statistics for the last 7 days
SELECT 
    c.name as company_name,
    COUNT(ss.id) as scraping_runs,
    SUM(ss.jobs_new) as total_new_jobs,
    SUM(ss.jobs_updated) as total_updated_jobs,
    AVG(EXTRACT(EPOCH FROM (ss.completed_at - ss.started_at))) as avg_duration_seconds,
    COUNT(CASE WHEN ss.status = 'failed' THEN 1 END) as failed_runs
FROM scraping_sessions ss
JOIN companies c ON ss.company_id = c.id
WHERE 
    ss.created_at >= NOW() - INTERVAL '7 days'
GROUP BY c.id, c.name
ORDER BY total_new_jobs DESC;
```

### Full-Text Search on Jobs

```sql
-- Full-text search using PostgreSQL's tsvector
SELECT 
    jp.id,
    jp.title,
    c.name as company_name,
    jp.location,
    ts_rank(
        to_tsvector('english', jp.title || ' ' || jp.description),
        to_tsquery('english', 'backend & python & senior')
    ) as relevance_score
FROM job_positions jp
JOIN companies c ON jp.company_id = c.id
WHERE 
    to_tsvector('english', jp.title || ' ' || jp.description) @@ 
    to_tsquery('english', 'backend & python & senior')
    AND jp.is_active = true
ORDER BY relevance_score DESC
LIMIT 20;
```

---

## 🌐 API Examples

### User Registration

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'

# Response
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_verified": false,
  "created_at": "2025-11-20T10:00:00Z"
}
```

### User Login

```bash
# Login and get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=SecurePass123!"

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Create Job Alert

```bash
# Create a new job alert
curl -X POST http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Senior Backend Python Jobs",
    "filters": {
      "companies": ["Monday.com", "Wiz", "Meta"],
      "keywords": ["backend", "python", "senior"],
      "exclude_keywords": ["junior", "intern"],
      "locations": ["Tel Aviv", "Herzliya"],
      "departments": ["Engineering"],
      "employment_types": ["Full-time"],
      "is_remote": null,
      "min_posted_days_ago": 7
    },
    "notification_frequency": "daily",
    "notification_channels": ["email"]
  }'

# Response
{
  "id": "456e7890-e89b-12d3-a456-426614174111",
  "name": "Senior Backend Python Jobs",
  "filters": { ... },
  "is_active": true,
  "notification_frequency": "daily",
  "last_notified_at": null,
  "created_at": "2025-11-20T10:05:00Z"
}
```

### List User's Alerts

```bash
# Get all alerts for the current user
curl -X GET http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Response
[
  {
    "id": "456e7890-e89b-12d3-a456-426614174111",
    "name": "Senior Backend Python Jobs",
    "is_active": true,
    "notification_frequency": "daily",
    "last_notified_at": "2025-11-20T08:00:00Z",
    "created_at": "2025-11-20T10:05:00Z"
  },
  {
    "id": "789e0123-e89b-12d3-a456-426614174222",
    "name": "Frontend React Jobs",
    "is_active": true,
    "notification_frequency": "weekly",
    "last_notified_at": null,
    "created_at": "2025-11-19T15:30:00Z"
  }
]
```

### Test Alert (Preview Matches)

```bash
# Preview jobs that match an alert
curl -X POST http://localhost:8000/api/v1/alerts/456e7890-e89b-12d3-a456-426614174111/test \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Response
{
  "alert_id": "456e7890-e89b-12d3-a456-426614174111",
  "matching_jobs_count": 15,
  "jobs": [
    {
      "id": "abc123...",
      "title": "Senior Backend Engineer",
      "company": "Monday.com",
      "location": "Tel Aviv",
      "posted_date": "2025-11-19T00:00:00Z",
      "job_url": "https://..."
    },
    // ... more jobs
  ]
}
```

### Search Jobs

```bash
# Search for jobs with filters
curl -X GET "http://localhost:8000/api/v1/jobs?company=Monday.com&location=Tel%20Aviv&keyword=backend&limit=20" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Response
{
  "total": 45,
  "page": 1,
  "page_size": 20,
  "jobs": [
    {
      "id": "abc123...",
      "title": "Senior Backend Engineer",
      "company": {
        "id": "company123...",
        "name": "Monday.com"
      },
      "location": "Tel Aviv",
      "department": "Engineering",
      "employment_type": "Full-time",
      "is_remote": false,
      "posted_date": "2025-11-19T00:00:00Z",
      "job_url": "https://...",
      "description": "We're looking for..."
    },
    // ... more jobs
  ]
}
```

---

## 🎯 Matching Algorithm Examples

### Python Implementation

```python
from typing import List, Dict
from src.models import JobPosition, JobAlert

class JobMatchingService:
    def find_matches_for_alert(
        self, 
        alert: JobAlert, 
        new_jobs: List[JobPosition]
    ) -> List[JobPosition]:
        """Find jobs matching a specific alert."""
        matches = []
        filters = alert.filters
        
        for job in new_jobs:
            if self._job_matches_filters(job, filters):
                matches.append(job)
        
        return matches
    
    def _job_matches_filters(self, job: JobPosition, filters: dict) -> bool:
        """Check if a job matches filter criteria."""
        
        # Company filter
        if filters.get('companies'):
            if job.company.name not in filters['companies']:
                return False
        
        # Keyword filter (must contain at least one keyword)
        if filters.get('keywords'):
            job_text = f"{job.title} {job.description}".lower()
            has_keyword = any(
                kw.lower() in job_text 
                for kw in filters['keywords']
            )
            if not has_keyword:
                return False
        
        # Exclude keywords (must not contain any)
        if filters.get('exclude_keywords'):
            job_text = f"{job.title} {job.description}".lower()
            has_excluded = any(
                kw.lower() in job_text 
                for kw in filters['exclude_keywords']
            )
            if has_excluded:
                return False
        
        # Location filter
        if filters.get('locations'):
            if job.location not in filters['locations']:
                return False
        
        # Department filter
        if filters.get('departments'):
            if job.department not in filters['departments']:
                return False
        
        # Employment type filter
        if filters.get('employment_types'):
            if job.employment_type not in filters['employment_types']:
                return False
        
        # Remote filter
        if filters.get('is_remote') is not None:
            if job.is_remote != filters['is_remote']:
                return False
        
        # Posted date filter
        if filters.get('min_posted_days_ago'):
            from datetime import datetime, timedelta
            cutoff = datetime.utcnow() - timedelta(
                days=filters['min_posted_days_ago']
            )
            if job.posted_date and job.posted_date < cutoff:
                return False
        
        # All filters passed!
        return True
```

### Example Usage

```python
# Example: Match jobs against an alert
from src.services.matching_service import JobMatchingService
from src.storage.repositories.job_repo import JobPositionRepository
from src.storage.repositories.alert_repo import JobAlertRepository

# Get new jobs from last 24 hours
job_repo = JobPositionRepository(db)
new_jobs = job_repo.get_recent_jobs(hours=24)

# Get a specific alert
alert_repo = JobAlertRepository(db)
alert = alert_repo.get_by_id("456e7890-e89b-12d3-a456-426614174111")

# Find matches
matching_service = JobMatchingService(db)
matches = matching_service.find_matches_for_alert(alert, new_jobs)

print(f"Found {len(matches)} matching jobs for alert '{alert.name}'")
for job in matches:
    print(f"  - {job.title} at {job.company.name}")
```

---

## 📧 Email Template Examples

### Job Alert Email (HTML)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }
        .job-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            background: #fff;
        }
        .job-title {
            font-size: 18px;
            font-weight: 600;
            color: #667eea;
            margin: 0 0 10px 0;
        }
        .job-company {
            font-size: 16px;
            font-weight: 500;
            color: #333;
            margin: 0 0 5px 0;
        }
        .job-meta {
            font-size: 14px;
            color: #666;
            margin: 5px 0;
        }
        .job-description {
            font-size: 14px;
            color: #555;
            margin: 10px 0;
        }
        .apply-button {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 10px;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 {{ jobs|length }} New Jobs Match Your Alert!</h1>
        <p>{{ alert.name }}</p>
    </div>
    
    <div style="padding: 20px;">
        <p>Hi {{ user.full_name or 'there' }}! 👋</p>
        <p>We found {{ jobs|length }} new jobs that match your alert criteria:</p>
        
        {% for job in jobs %}
        <div class="job-card">
            <h2 class="job-title">{{ job.title }}</h2>
            <p class="job-company">{{ job.company.name }}</p>
            <p class="job-meta">
                📍 {{ job.location }}
                {% if job.department %} | 🏢 {{ job.department }}{% endif %}
                {% if job.employment_type %} | 💼 {{ job.employment_type }}{% endif %}
                {% if job.is_remote %} | 🏠 Remote{% endif %}
            </p>
            <p class="job-meta">📅 Posted: {{ job.posted_date.strftime('%B %d, %Y') }}</p>
            <p class="job-description">{{ job.description[:200] }}...</p>
            <a href="{{ job.job_url }}" class="apply-button">Apply Now →</a>
        </div>
        {% endfor %}
        
        <p style="margin-top: 30px;">
            <a href="{{ app_url }}/alerts/{{ alert.id }}">Manage this alert</a> | 
            <a href="{{ app_url }}/jobs">View all jobs</a>
        </p>
    </div>
    
    <div class="footer">
        <p>You're receiving this because you created the alert "{{ alert.name }}"</p>
        <p><a href="{{ app_url }}/unsubscribe/{{ alert.id }}">Unsubscribe from this alert</a></p>
        <p>© 2025 Job Scraper. All rights reserved.</p>
    </div>
</body>
</html>
```

---

## ⚙️ Celery Task Examples

### Daily Scraping Task

```python
from celery import Task
from src.workers.celery_app import celery_app
from src.orchestrator.scraper_orchestrator import ScraperOrchestrator
import asyncio

@celery_app.task(bind=True, max_retries=3)
def run_daily_scraping(self: Task):
    """Daily scraping task - runs at 2:00 AM UTC."""
    try:
        logger.info("Starting daily scraping job...")
        
        orchestrator = ScraperOrchestrator()
        
        # Run scraping for all active companies
        results = asyncio.run(
            orchestrator.scrape_all_companies(incremental=True)
        )
        
        # Log results
        total_new = sum(r['jobs_new'] for r in results.values())
        total_updated = sum(r['jobs_updated'] for r in results.values())
        
        logger.success(
            f"Daily scraping complete: {total_new} new jobs, "
            f"{total_updated} updated jobs"
        )
        
        # Trigger notification processing
        process_new_jobs.delay()
        
        return {
            'status': 'success',
            'companies_scraped': len(results),
            'total_new_jobs': total_new,
            'total_updated_jobs': total_updated
        }
        
    except Exception as exc:
        logger.error(f"Daily scraping failed: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes
```

### Notification Processing Task

```python
@celery_app.task(bind=True, max_retries=3)
def process_new_jobs(self: Task):
    """Process new jobs and send notifications."""
    try:
        from src.storage.database import Database
        from src.services.matching_service import JobMatchingService
        from src.services.notification_service import NotificationService
        from datetime import datetime, timedelta
        
        db = Database()
        
        with db.get_session() as session:
            # Get jobs created in last 24 hours
            cutoff = datetime.utcnow() - timedelta(hours=24)
            new_jobs = session.query(JobPosition).filter(
                JobPosition.created_at >= cutoff,
                JobPosition.is_active == True
            ).all()
            
            if not new_jobs:
                logger.info("No new jobs to process")
                return {'status': 'success', 'new_jobs': 0}
            
            logger.info(f"Processing {len(new_jobs)} new jobs...")
            
            # Match jobs with alerts
            matching_service = JobMatchingService(session)
            user_matches = matching_service.match_all_alerts(new_jobs)
            
            # Send notifications
            notification_service = NotificationService(session)
            notification_service.create_and_send_notifications(user_matches)
            
            logger.success(
                f"Processed {len(new_jobs)} jobs, "
                f"sent notifications to {len(user_matches)} users"
            )
            
            return {
                'status': 'success',
                'new_jobs': len(new_jobs),
                'users_notified': len(user_matches)
            }
            
    except Exception as exc:
        logger.error(f"Notification processing failed: {exc}")
        raise self.retry(exc=exc, countdown=600)  # Retry after 10 minutes
```

---

**More examples coming soon!** 🚀

