# Quick Start Guide
## Job Notification System Implementation

**Last Updated:** November 19, 2025

---

## 📋 Overview

This guide provides a quick overview of the job notification system and how to get started with implementation.

### What We're Building

A comprehensive job scraping and notification platform that:
1. **Scrapes** 100+ company career pages daily
2. **Stores** all jobs in PostgreSQL (Neon)
3. **Matches** new jobs with user-configured alerts
4. **Notifies** users via email when relevant jobs are posted

---

## 🎯 Key Features

### For Users
- ✅ Create custom job alerts with flexible filters
- ✅ Receive daily/weekly email digests of matching jobs
- ✅ Save and track job applications
- ✅ Get instant notifications for high-priority matches

### For Admins
- ✅ Monitor scraping health and performance
- ✅ View user engagement metrics
- ✅ Manage companies and scraping schedules
- ✅ Track notification delivery rates

---

## 🏗️ System Architecture

```
Daily Scheduler (Celery Beat)
    ↓
Scraping Workers (Parallel)
    ↓
PostgreSQL Database (Neon)
    ↓
Job Matching Engine
    ↓
Notification Service
    ↓
Email Delivery (SendGrid)
```

---

## 📊 Database Schema Summary

### Existing Tables (Already Implemented)
- **companies** - Company information and scraping config
- **job_positions** - Job postings with full details
- **scraping_sessions** - Scraping run history and stats

### New Tables (To Be Implemented)
- **users** - User accounts and authentication
- **job_alerts** - User-configured job alerts with filters
- **notifications** - Notification history and delivery status
- **user_job_interactions** - User actions (viewed, saved, applied)

---

## 🚀 Implementation Phases

### Phase 1: Database & Models (Week 1)
**Goal:** Set up new database tables and models

**Key Tasks:**
- Create User, JobAlert, Notification models
- Set up Alembic migrations
- Write repository classes
- Add database indexes

**Deliverables:**
- `src/models/user.py`
- `src/models/job_alert.py`
- `src/models/notification.py`
- `src/storage/repositories/user_repo.py`
- `src/storage/repositories/alert_repo.py`

---

### Phase 2: User Management (Week 2)
**Goal:** Implement authentication and user management

**Key Tasks:**
- User registration/login with JWT
- Password reset flow
- Email verification
- User profile management

**Deliverables:**
- `src/auth/security.py`
- `src/api/routes/auth.py`
- `src/api/routes/users.py`
- `src/api/schemas/user.py`

---

### Phase 3: Alert Management (Week 3)
**Goal:** Build job alert configuration system

**Key Tasks:**
- CRUD API for alerts
- Filter validation
- Alert preview/testing
- Alert pause/resume

**Deliverables:**
- `src/api/routes/alerts.py`
- `src/api/schemas/alert.py`
- `src/services/alert_service.py`

---

### Phase 4: Job Matching (Week 4)
**Goal:** Build efficient job-to-alert matching engine

**Key Tasks:**
- Implement matching algorithm
- Optimize with database indexes
- Add Redis caching
- Performance testing

**Deliverables:**
- `src/services/matching_service.py`
- `src/services/cache_service.py`
- Database migration with indexes

---

### Phase 5: Notifications (Week 5-6)
**Goal:** Implement notification delivery system

**Key Tasks:**
- Integrate SendGrid for email
- Build email templates
- Implement batching logic
- Add webhook support

**Deliverables:**
- `src/services/email_service.py`
- `src/services/notification_service.py`
- `src/templates/email/job_alert.html`

---

### Phase 6: Scheduler & Workers (Week 7)
**Goal:** Set up background task processing

**Key Tasks:**
- Configure Celery workers
- Set up Celery Beat scheduler
- Create daily scraping task
- Create notification task

**Deliverables:**
- `src/workers/celery_app.py`
- `src/workers/tasks.py`

---

## 🔧 Technology Stack

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.10+
- **ORM:** SQLAlchemy 2.0
- **Database:** PostgreSQL (Neon)
- **Task Queue:** Celery + Redis
- **Authentication:** JWT (PyJWT)

### Scraping
- **Browser Automation:** Playwright
- **HTTP Client:** httpx
- **HTML Parsing:** BeautifulSoup4

### Notifications
- **Email:** SendGrid / AWS SES
- **Templates:** Jinja2
- **Push (Future):** Firebase Cloud Messaging

### Infrastructure
- **Caching:** Redis
- **Monitoring:** Sentry, Prometheus
- **Deployment:** Docker, AWS/GCP

---

## 📝 Example: Creating a Job Alert

### User Flow
1. User logs in to web dashboard
2. Clicks "Create Alert"
3. Configures filters:
   - Companies: Monday.com, Wiz, Meta
   - Keywords: "backend", "python", "senior"
   - Locations: Tel Aviv, Herzliya
   - Notification: Daily digest via email
4. Saves alert
5. System starts matching new jobs daily

### API Request
```json
POST /api/v1/alerts
Authorization: Bearer <jwt_token>

{
  "name": "Senior Backend Python Jobs",
  "filters": {
    "companies": ["Monday.com", "Wiz", "Meta"],
    "keywords": ["backend", "python", "senior"],
    "locations": ["Tel Aviv", "Herzliya"],
    "employment_types": ["Full-time"]
  },
  "notification_frequency": "daily",
  "notification_channels": ["email"]
}
```

### Database Record
```sql
INSERT INTO job_alerts (
  id, user_id, name, filters, notification_frequency, is_active
) VALUES (
  gen_random_uuid(),
  '123e4567-e89b-12d3-a456-426614174000',
  'Senior Backend Python Jobs',
  '{"companies": ["Monday.com", "Wiz", "Meta"], "keywords": ["backend", "python", "senior"]}',
  'daily',
  true
);
```

---

## 📧 Example: Email Notification

### Trigger
- Daily scraping completes at 2:00 AM
- 5 new jobs match user's alert
- Notification service sends email at 8:00 AM

### Email Content
```
Subject: [5 New Jobs] Your Job Alert: Senior Backend Python Jobs

Hi John!

We found 5 new jobs matching your alert "Senior Backend Python Jobs":

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔹 Senior Backend Engineer
   Monday.com - Tel Aviv, Israel
   Posted: Today
   
   We're looking for a Senior Backend Engineer to join our Core Platform team...
   
   [Apply Now →]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔹 Backend Tech Lead - Python
   Wiz - Tel Aviv, Israel
   Posted: Today
   
   Join our Security Platform team as a Backend Tech Lead...
   
   [Apply Now →]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[View All 5 Jobs →]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Manage your alerts | Unsubscribe
```

---

## 🔍 Example: Matching Algorithm

### Pseudocode
```python
def match_jobs_to_alerts(new_jobs, active_alerts):
    user_matches = {}
    
    for alert in active_alerts:
        matching_jobs = []
        
        for job in new_jobs:
            # Check company filter
            if alert.filters.companies and job.company not in alert.filters.companies:
                continue
            
            # Check keyword filter
            if alert.filters.keywords:
                job_text = f"{job.title} {job.description}".lower()
                if not any(kw in job_text for kw in alert.filters.keywords):
                    continue
            
            # Check location filter
            if alert.filters.locations and job.location not in alert.filters.locations:
                continue
            
            # All filters passed - it's a match!
            matching_jobs.append(job)
        
        if matching_jobs:
            user_matches[alert.user_id] = matching_jobs
    
    return user_matches
```

---

## 📈 Performance Targets

### Scraping
- **Companies:** 100+ companies
- **Duration:** <2 hours for full scrape
- **Success Rate:** >95%
- **Jobs per Day:** ~500-1000 new jobs

### Matching
- **Jobs:** 100,000 active jobs
- **Alerts:** 50,000 active alerts
- **Processing Time:** <10 minutes
- **Accuracy:** 100% (no false positives)

### Notifications
- **Users:** 10,000+ users
- **Emails per Day:** ~5,000-10,000
- **Delivery Rate:** >98%
- **Open Rate:** >40%
- **Click Rate:** >15%

---

## 🛠️ Development Setup

### Prerequisites
```bash
# Install Python 3.10+
python --version

# Install PostgreSQL
brew install postgresql  # macOS
# or use Neon cloud database

# Install Redis
brew install redis  # macOS
```

### Installation
```bash
# Clone repository
git clone <repo-url>
cd scrapper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Initialize database
alembic upgrade head

# Run tests
pytest
```

### Running Locally
```bash
# Terminal 1: Start API server
uvicorn src.api.app:app --reload --port 8000

# Terminal 2: Start Celery worker
celery -A src.workers.celery_app worker --loglevel=info

# Terminal 3: Start Celery Beat scheduler
celery -A src.workers.celery_app beat --loglevel=info

# Terminal 4: Start Redis
redis-server
```

---

## 📚 Documentation

### Main Documents
1. **PRD_JOB_NOTIFICATION_SYSTEM.md** - Complete product requirements
2. **IMPLEMENTATION_ROADMAP.md** - Detailed implementation plan
3. **QUICK_START_GUIDE.md** - This document

### Existing Documentation
- **README.md** - Project overview
- **ARCHITECTURE.md** - System architecture
- **USAGE.md** - Usage examples
- **GETTING_STARTED.md** - Getting started guide

---

## ✅ Next Steps

### Immediate Actions
1. **Review PRD** - Read and understand requirements
2. **Set up Neon** - Create PostgreSQL database
3. **Start Phase 1** - Begin database model implementation
4. **Set up monitoring** - Configure Sentry for error tracking

### Week 1 Goals
- [ ] Create all new database models
- [ ] Write and run Alembic migrations
- [ ] Implement repository classes
- [ ] Write unit tests (>80% coverage)
- [ ] Review and merge to main branch

---

## 🤝 Support

### Questions?
- Check existing documentation
- Review code examples in `/tests`
- Ask in team Slack channel

### Issues?
- Check logs in `/logs`
- Review Sentry error reports
- Run tests: `pytest -v`

---

**Ready to start?** Begin with Phase 1 in the Implementation Roadmap! 🚀

