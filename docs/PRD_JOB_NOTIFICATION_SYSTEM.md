# Product Requirements Document (PRD)
## Job Scraping & Notification System

**Version:** 1.0  
**Date:** November 19, 2025  
**Status:** Draft  
**Author:** Product Team

---

## 1. Executive Summary

### 1.1 Overview
Build a comprehensive job scraping and notification system that:
- Scrapes job postings from 100+ companies daily
- Stores all jobs in a PostgreSQL database (Neon)
- Allows users to configure custom job alerts
- Sends personalized notifications to users when new jobs match their criteria

### 1.2 Goals
- **Primary Goal:** Enable users to receive timely notifications about relevant job opportunities
- **Secondary Goals:**
  - Maintain a comprehensive, up-to-date job database
  - Provide flexible alert configuration
  - Ensure scalability for 10,000+ users
  - Minimize notification fatigue through smart filtering

### 1.3 Success Metrics
- **System Performance:**
  - Daily scraping completion rate: >95%
  - Job data freshness: <24 hours
  - Database uptime: >99.9%
  
- **User Engagement:**
  - Alert open rate: >40%
  - Alert click-through rate: >15%
  - User retention (30-day): >60%

---

## 2. Current State Analysis

### 2.1 Existing Infrastructure
✅ **Already Implemented:**
- PostgreSQL database with SQLAlchemy ORM
- Database models: `Company`, `JobPosition`, `ScrapingSession`
- 13 working scrapers (Monday.com, Wiz, Island, EON, Palo Alto, Amazon, Meta, Nvidia, Wix, Salesforce, Datadog, Unity, AppsFlyer)
- Scraper orchestrator for managing scraping sessions
- Location filtering (Israel-focused)
- FastAPI application skeleton
- Redis infrastructure for caching/queuing
- Celery configuration for background tasks

### 2.2 What's Missing
❌ **Needs to be Built:**
- User management system
- Job alert configuration system
- Notification delivery system
- Daily scraping scheduler
- New job detection logic
- User-job matching engine
- Email/push notification infrastructure

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Daily Scheduler                          │
│                    (Celery Beat / Cron)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Scraping Workers                             │
│              (Celery Workers / Async Tasks)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Company 1 │  │Company 2 │  │Company 3 │  │Company N │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database (Neon)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Companies │  │   Jobs   │  │  Users   │  │  Alerts  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Notification Engine                            │
│              (Celery Worker / Background Task)                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  1. Detect new jobs                                  │      │
│  │  2. Match jobs with user alerts                      │      │
│  │  3. Generate personalized notifications              │      │
│  │  4. Send via email/push/webhook                      │      │
│  └──────────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Notification Delivery                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Email   │  │   Push   │  │ Webhook  │  │   SMS    │       │
│  │(SendGrid)│  │(Firebase)│  │ (Slack)  │  │(Twilio)  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Database Schema

#### 3.2.1 Existing Tables (Already Implemented)

**`companies`**
- `id` (UUID, PK)
- `name` (VARCHAR, unique)
- `website` (VARCHAR)
- `careers_url` (VARCHAR)
- `industry` (VARCHAR)
- `scraping_config` (JSON)
- `scraping_frequency` (VARCHAR) - cron expression
- `last_scraped_at` (TIMESTAMP)
- `is_active` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMP)

**`job_positions`**
- `id` (UUID, PK)
- `company_id` (UUID, FK → companies)
- `external_id` (VARCHAR, unique per company)
- `title` (VARCHAR)
- `description` (TEXT)
- `location` (VARCHAR)
- `job_url` (VARCHAR)
- `department` (VARCHAR)
- `employment_type` (VARCHAR)
- `posted_date` (TIMESTAMP)
- `is_remote` (BOOLEAN)
- `is_active` (BOOLEAN)
- `raw_html` (TEXT)
- `metadata` (JSON)
- `created_at`, `updated_at` (TIMESTAMP)

**`scraping_sessions`**
- `id` (UUID, PK)
- `company_id` (UUID, FK → companies)
- `status` (VARCHAR) - pending/running/completed/failed
- `started_at`, `completed_at` (TIMESTAMP)
- `jobs_found`, `jobs_new`, `jobs_updated`, `jobs_removed` (INTEGER)
- `errors` (JSON)
- `performance_metrics` (JSON)
- `created_at`, `updated_at` (TIMESTAMP)

#### 3.2.2 New Tables (To Be Implemented)

**`users`**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    reset_token VARCHAR(255),
    reset_token_expires_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
```

**`job_alerts`**
```sql
CREATE TABLE job_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Filter criteria (stored as JSONB for flexibility)
    filters JSONB NOT NULL DEFAULT '{}',
    -- Example filters structure:
    -- {
    --   "companies": ["Monday.com", "Wiz"],
    --   "keywords": ["backend", "python", "senior"],
    --   "exclude_keywords": ["junior", "intern"],
    --   "locations": ["Tel Aviv", "Herzliya"],
    --   "departments": ["Engineering", "Product"],
    --   "employment_types": ["Full-time"],
    --   "is_remote": true,
    --   "min_posted_days_ago": 7
    -- }
    
    -- Notification settings
    notification_frequency VARCHAR(50) DEFAULT 'daily',  -- instant, daily, weekly
    notification_channels JSONB DEFAULT '["email"]',  -- ["email", "push", "webhook"]
    last_notified_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_job_alerts_user_id ON job_alerts(user_id);
CREATE INDEX idx_job_alerts_is_active ON job_alerts(is_active);
CREATE INDEX idx_job_alerts_filters ON job_alerts USING GIN(filters);
```

**`notifications`**
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_id UUID REFERENCES job_alerts(id) ON DELETE SET NULL,
    
    type VARCHAR(50) NOT NULL,  -- job_match, system, alert
    title VARCHAR(255) NOT NULL,
    message TEXT,
    
    -- Notification data
    data JSONB DEFAULT '{}',  -- Contains job IDs, links, etc.
    
    -- Delivery status
    channels JSONB DEFAULT '[]',  -- ["email", "push"]
    delivery_status JSONB DEFAULT '{}',  -- {"email": "sent", "push": "failed"}
    
    -- User interaction
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_alert_id ON notifications(alert_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```

**`user_job_interactions`**
```sql
CREATE TABLE user_job_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES job_positions(id) ON DELETE CASCADE,
    
    interaction_type VARCHAR(50) NOT NULL,  -- viewed, saved, applied, dismissed
    source VARCHAR(50),  -- email, web, push
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, job_id, interaction_type)
);

CREATE INDEX idx_user_job_interactions_user_id ON user_job_interactions(user_id);
CREATE INDEX idx_user_job_interactions_job_id ON user_job_interactions(job_id);
CREATE INDEX idx_user_job_interactions_type ON user_job_interactions(interaction_type);
```

---

## 4. Functional Requirements

### 4.1 Daily Scraping System

#### FR-1.1: Scheduled Scraping
- **Description:** System must scrape all active companies daily
- **Trigger:** Cron job / Celery Beat at configurable time (default: 2:00 AM UTC)
- **Process:**
  1. Load all active companies from database
  2. Create scraping tasks for each company
  3. Distribute tasks to worker pool
  4. Track progress and errors
  5. Generate daily scraping report

#### FR-1.2: New Job Detection
- **Description:** System must identify new jobs added since last scrape
- **Logic:**
  - Compare `external_id` with existing jobs
  - Mark new jobs with `created_at` timestamp
  - Track in `scraping_sessions.jobs_new`

#### FR-1.3: Job Updates Detection
- **Description:** System must detect changes to existing jobs
- **Logic:**
  - Compare job fields (title, description, location, etc.)
  - Update `updated_at` timestamp if changes detected
  - Track in `scraping_sessions.jobs_updated`

#### FR-1.4: Job Removal Detection
- **Description:** System must detect jobs that are no longer posted
- **Logic:**
  - Mark jobs as `is_active=false` if not found in latest scrape
  - Track in `scraping_sessions.jobs_removed`

### 4.2 User Management

#### FR-2.1: User Registration
- Email + password authentication
- Email verification required
- Password strength requirements (min 8 chars, uppercase, lowercase, number)

#### FR-2.2: User Login
- Email + password
- JWT token-based authentication
- Refresh token support
- "Remember me" functionality

#### FR-2.3: Password Reset
- Email-based password reset flow
- Secure token generation (expires in 1 hour)
- Rate limiting (max 3 requests per hour)

#### FR-2.4: User Profile
- Update email, name, preferences
- Manage notification settings
- View alert history

### 4.3 Job Alert Configuration

#### FR-3.1: Create Alert
- **Required Fields:**
  - Alert name
  - At least one filter criterion
  
- **Optional Filters:**
  - Companies (multi-select)
  - Keywords (text, comma-separated)
  - Exclude keywords (text, comma-separated)
  - Locations (multi-select)
  - Departments (multi-select)
  - Employment types (multi-select)
  - Remote only (boolean)
  - Posted within last N days

- **Notification Settings:**
  - Frequency: instant, daily, weekly
  - Channels: email, push, webhook

#### FR-3.2: Edit Alert
- Modify any alert settings
- Changes take effect immediately
- Reset `last_notified_at` if filters change significantly

#### FR-3.3: Delete Alert
- Soft delete (mark as inactive)
- Stop all notifications
- Retain historical data

#### FR-3.4: Pause/Resume Alert
- Temporarily disable without deleting
- Resume from last state

### 4.4 Notification System

#### FR-4.1: Job Matching Engine
- **Trigger:** After each scraping session completes
- **Process:**
  1. Get all new jobs from session
  2. Load all active alerts
  3. For each alert:
     - Apply filters to new jobs
     - Group matching jobs by user
     - Create notification records

#### FR-4.2: Notification Delivery
- **Email Notifications:**
  - Subject: "[X New Jobs] Your Job Alert: {alert_name}"
  - Body: HTML template with job listings
  - Include: job title, company, location, posted date, apply link
  - Unsubscribe link
  - Rate limit: max 1 email per alert per frequency setting

- **Push Notifications:**
  - Title: "X new jobs match your alert"
  - Body: Top 3 job titles
  - Deep link to app/web

- **Webhook Notifications:**
  - POST JSON payload to user-configured URL
  - Include full job details
  - Retry logic (3 attempts with exponential backoff)

#### FR-4.3: Notification Frequency Control
- **Instant:** Send immediately when new matching jobs found
- **Daily:** Batch all matches from last 24 hours, send once per day
- **Weekly:** Batch all matches from last 7 days, send once per week

#### FR-4.4: Notification Deduplication
- Don't send same job to same user multiple times
- Track in `user_job_interactions` or notification metadata

---

## 5. Non-Functional Requirements

### 5.1 Performance
- **Scraping:**
  - Complete all 100 companies within 2 hours
  - Support concurrent scraping (5-10 workers)
  - Handle rate limiting gracefully

- **Matching:**
  - Process 10,000 jobs against 10,000 alerts within 10 minutes
  - Use database indexes for efficient filtering

- **Notifications:**
  - Send 10,000 emails within 30 minutes
  - Email delivery rate >98%

### 5.2 Scalability
- Support 10,000+ users
- Support 100,000+ active jobs
- Support 50,000+ active alerts
- Horizontal scaling for workers

### 5.3 Reliability
- Database uptime: 99.9%
- Scraping success rate: >95%
- Notification delivery rate: >98%
- Automatic retry for failed tasks

### 5.4 Security
- Password hashing (bcrypt, cost factor 12)
- JWT tokens with expiration
- Rate limiting on API endpoints
- SQL injection prevention (parameterized queries)
- XSS prevention (input sanitization)
- HTTPS only in production

### 5.5 Data Privacy
- GDPR compliance
- User data deletion on request
- Email unsubscribe functionality
- Clear privacy policy

---

## 6. Technical Implementation Plan

### Phase 1: Database & Models (Week 1)
- [ ] Create new database models (User, JobAlert, Notification, UserJobInteraction)
- [ ] Write Alembic migrations
- [ ] Create repository classes for new models
- [ ] Write unit tests for models

### Phase 2: User Management (Week 2)
- [ ] Implement user registration/login API
- [ ] Add JWT authentication
- [ ] Create password reset flow
- [ ] Build user profile management
- [ ] Write API tests

### Phase 3: Alert Management (Week 3)
- [ ] Create alert CRUD API endpoints
- [ ] Implement filter validation
- [ ] Build alert testing/preview feature
- [ ] Write API tests

### Phase 4: Job Matching Engine (Week 4)
- [ ] Implement matching algorithm
- [ ] Optimize with database indexes
- [ ] Add caching layer (Redis)
- [ ] Performance testing
- [ ] Write unit tests

### Phase 5: Notification System (Week 5-6)
- [ ] Integrate email service (SendGrid/AWS SES)
- [ ] Build email templates
- [ ] Implement notification batching
- [ ] Add webhook support
- [ ] Implement push notifications (optional)
- [ ] Write integration tests

### Phase 6: Scheduler & Workers (Week 7)
- [ ] Configure Celery Beat for daily scraping
- [ ] Create notification worker tasks
- [ ] Implement retry logic
- [ ] Add monitoring and alerting
- [ ] Load testing

### Phase 7: API & Frontend (Week 8-10)
- [ ] Build REST API endpoints
- [ ] Create API documentation (OpenAPI/Swagger)
- [ ] Build admin dashboard
- [ ] Build user dashboard
- [ ] Integration testing

### Phase 8: Production Deployment (Week 11-12)
- [ ] Set up Neon PostgreSQL database
- [ ] Configure production environment
- [ ] Set up monitoring (Sentry, Prometheus)
- [ ] Deploy to production
- [ ] User acceptance testing

---

## 7. API Endpoints (High-Level)

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update profile
- `DELETE /api/v1/users/me` - Delete account

### Job Alerts
- `GET /api/v1/alerts` - List user's alerts
- `POST /api/v1/alerts` - Create alert
- `GET /api/v1/alerts/{id}` - Get alert details
- `PATCH /api/v1/alerts/{id}` - Update alert
- `DELETE /api/v1/alerts/{id}` - Delete alert
- `POST /api/v1/alerts/{id}/pause` - Pause alert
- `POST /api/v1/alerts/{id}/resume` - Resume alert
- `POST /api/v1/alerts/{id}/test` - Test alert (preview matching jobs)

### Jobs
- `GET /api/v1/jobs` - List jobs (with filters)
- `GET /api/v1/jobs/{id}` - Get job details
- `POST /api/v1/jobs/{id}/save` - Save job
- `POST /api/v1/jobs/{id}/dismiss` - Dismiss job
- `GET /api/v1/jobs/saved` - Get saved jobs

### Notifications
- `GET /api/v1/notifications` - List notifications
- `PATCH /api/v1/notifications/{id}/read` - Mark as read
- `DELETE /api/v1/notifications/{id}` - Delete notification

### Companies
- `GET /api/v1/companies` - List companies
- `GET /api/v1/companies/{id}` - Get company details
- `GET /api/v1/companies/{id}/jobs` - Get company jobs

---

## 8. Success Criteria

### 8.1 Launch Criteria
- [ ] All Phase 1-8 tasks completed
- [ ] 100% test coverage for critical paths
- [ ] Load testing passed (10K users, 100K jobs)
- [ ] Security audit passed
- [ ] Documentation complete
- [ ] Beta testing with 50 users successful

### 8.2 Post-Launch Metrics (30 days)
- Daily active users: >1,000
- Alert creation rate: >50%
- Email open rate: >40%
- Click-through rate: >15%
- User retention: >60%
- System uptime: >99.9%

---

## 9. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Email deliverability issues | High | Medium | Use reputable ESP (SendGrid), implement SPF/DKIM/DMARC |
| Database performance degradation | High | Medium | Implement proper indexes, use connection pooling, monitor query performance |
| Scraping failures | Medium | High | Implement robust retry logic, monitor scraping health, have fallback strategies |
| User notification fatigue | Medium | Medium | Smart batching, frequency controls, easy unsubscribe |
| Neon database costs | Medium | Low | Monitor usage, implement data retention policies, optimize queries |

---

## 10. Future Enhancements (Post-MVP)

- AI-powered job recommendations
- Resume parsing and matching
- Salary insights and trends
- Company reviews integration
- Mobile apps (iOS/Android)
- Browser extension
- Slack/Discord bot integration
- Advanced analytics dashboard
- Job application tracking
- Interview preparation resources

---

## 11. Appendix

### 11.1 Technology Stack
- **Backend:** Python 3.10+, FastAPI
- **Database:** PostgreSQL (Neon)
- **ORM:** SQLAlchemy 2.0
- **Task Queue:** Celery + Redis
- **Email:** SendGrid / AWS SES
- **Authentication:** JWT (PyJWT)
- **Scraping:** Playwright, httpx, BeautifulSoup
- **Monitoring:** Sentry, Prometheus
- **Deployment:** Docker, AWS/GCP

### 11.2 Database Sizing Estimates
- **Users:** 10,000 users × 1 KB = 10 MB
- **Job Alerts:** 50,000 alerts × 2 KB = 100 MB
- **Jobs:** 100,000 jobs × 10 KB = 1 GB
- **Notifications:** 1M notifications × 1 KB = 1 GB
- **Total:** ~2.5 GB (with indexes: ~5 GB)

### 11.3 Cost Estimates (Monthly)
- **Neon Database:** $20-50 (Pro plan)
- **SendGrid:** $15-50 (40K-100K emails)
- **Redis:** $10-20 (managed service)
- **Hosting:** $50-100 (compute resources)
- **Total:** $95-220/month

---

**Document Status:** Ready for Review  
**Next Steps:** Review with engineering team, refine estimates, begin Phase 1 implementation

