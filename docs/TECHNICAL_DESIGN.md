# Technical Design Document
## Job Scraping & Alert Platform - Database Integration

### 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  Celery Workers (Scraping)  │  Alert Engine  │  API/CLI Tools   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  Scraper Manager  │  Position Lifecycle  │  Alert Matcher       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Data Access Layer (ORM)                     │
├─────────────────────────────────────────────────────────────────┤
│              SQLAlchemy Models & Repository Pattern              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
├─────────────────────────────────────────────────────────────────┤
│  users  │  companies  │  job_positions  │  alerts  │  mappings  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2. Database Schema Design

#### 2.1 Core Tables

##### **users**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    preferences JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_users_email (email),
    INDEX idx_users_is_active (is_active)
);
```

**Fields**:
- `id`: Primary key
- `email`: Unique user email (used for alerts)
- `full_name`: User's display name
- `is_active`: Soft delete flag
- `preferences`: JSON field for user settings (timezone, notification frequency, etc.)

---

##### **companies**
```sql
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    website VARCHAR(500),
    careers_url VARCHAR(500),
    industry VARCHAR(255),
    size VARCHAR(50),
    location VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    scraping_enabled BOOLEAN DEFAULT TRUE,
    scraping_frequency VARCHAR(50) DEFAULT '0 0 * * *',
    last_scraped_at TIMESTAMP,
    scraping_config JSONB,
    location_filter JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_companies_name (name),
    INDEX idx_companies_is_active (is_active),
    INDEX idx_companies_scraping_enabled (scraping_enabled)
);
```

**Fields**:
- `scraping_config`: JSON from companies.yaml (selectors, scraper_type, etc.)
- `location_filter`: JSON for location filtering rules
- `metadata`: Additional company info (employee count, funding, etc.)

---

##### **job_positions**
```sql
CREATE TABLE job_positions (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Job Details
    title VARCHAR(500) NOT NULL,
    location VARCHAR(255),
    department VARCHAR(255),
    employment_type VARCHAR(50),
    job_url VARCHAR(1000) UNIQUE NOT NULL,
    description TEXT,
    
    -- Status & Lifecycle
    status VARCHAR(50) DEFAULT 'active',  -- active, expired, filled
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expired_at TIMESTAMP,
    
    -- Metadata
    is_remote BOOLEAN DEFAULT FALSE,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency VARCHAR(10),
    experience_level VARCHAR(50),
    raw_data JSONB,
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_job_positions_company_id (company_id),
    INDEX idx_job_positions_status (status),
    INDEX idx_job_positions_location (location),
    INDEX idx_job_positions_title (title),
    INDEX idx_job_positions_first_seen_at (first_seen_at),
    INDEX idx_job_positions_job_url (job_url),
    
    -- Composite indexes for common queries
    INDEX idx_job_positions_company_status (company_id, status),
    INDEX idx_job_positions_status_first_seen (status, first_seen_at DESC)
);
```

**Status Values**:
- `active`: Currently on company career page
- `expired`: No longer on career page (likely filled or cancelled)
- `filled`: Explicitly marked as filled

**Lifecycle**:
- `first_seen_at`: When position was first discovered
- `last_seen_at`: Last time position was seen during scraping
- `expired_at`: When position was marked as expired

---

##### **alerts**
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Alert Configuration
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Matching Criteria (all are optional, combined with AND logic)
    company_ids INTEGER[] DEFAULT '{}',  -- Array of company IDs
    keywords TEXT[] DEFAULT '{}',        -- Keywords to match in title
    excluded_keywords TEXT[] DEFAULT '{}',  -- Keywords to exclude
    locations TEXT[] DEFAULT '{}',       -- Locations to match
    departments TEXT[] DEFAULT '{}',     -- Departments to match
    employment_types TEXT[] DEFAULT '{}',  -- full-time, part-time, contract
    is_remote BOOLEAN,                   -- NULL = don't care, TRUE/FALSE = filter
    
    -- Notification Settings
    notification_method VARCHAR(50) DEFAULT 'email',  -- email, webhook, slack
    notification_config JSONB DEFAULT '{}'::jsonb,
    
    -- Tracking
    last_triggered_at TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_alerts_user_id (user_id),
    INDEX idx_alerts_is_active (is_active),
    INDEX idx_alerts_company_ids USING GIN (company_ids)
);
```

**Matching Logic**:
- If `company_ids` is not empty, position must be from one of these companies
- If `keywords` is not empty, position title must contain at least one keyword
- If `excluded_keywords` is not empty, position title must NOT contain any
- All filters are combined with AND logic

---

##### **user_job_applications** (Many-to-Many)
```sql
CREATE TABLE user_job_applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_position_id INTEGER NOT NULL REFERENCES job_positions(id) ON DELETE CASCADE,
    
    -- Application Status
    status VARCHAR(50) DEFAULT 'interested',  -- interested, applied, interviewing, offered, rejected, accepted
    applied_at TIMESTAMP,
    
    -- Tracking
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(user_id, job_position_id),
    
    -- Indexes
    INDEX idx_user_job_applications_user_id (user_id),
    INDEX idx_user_job_applications_job_position_id (job_position_id),
    INDEX idx_user_job_applications_status (status)
);
```

---

##### **alert_notifications** (Audit Log)
```sql
CREATE TABLE alert_notifications (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    job_position_id INTEGER NOT NULL REFERENCES job_positions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification Details
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_status VARCHAR(50) DEFAULT 'pending',  -- pending, sent, failed
    delivery_method VARCHAR(50),
    error_message TEXT,
    
    -- Indexes
    INDEX idx_alert_notifications_alert_id (alert_id),
    INDEX idx_alert_notifications_user_id (user_id),
    INDEX idx_alert_notifications_sent_at (sent_at DESC)
);
```

---

### 3. SQLAlchemy Models

#### 3.1 Base Model
```python
# src/models/base.py
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

#### 3.2 Model Structure
```
src/models/
├── __init__.py
├── base.py              # Base model and mixins
├── user.py              # User model
├── company.py           # Company model
├── job_position.py      # JobPosition model
├── alert.py             # Alert model
├── user_job_application.py  # UserJobApplication model
└── alert_notification.py    # AlertNotification model
```

---

### 4. Database Configuration

#### 4.1 Local Development (PostgreSQL)
```python
# config/database.py
DATABASE_CONFIG = {
    'local': {
        'host': 'localhost',
        'port': 5432,
        'database': 'job_scraper_dev',
        'user': 'postgres',
        'password': 'postgres',
    },
    'remote': {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
    }
}
```

#### 4.2 Connection Pooling
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)
```

---

### 5. Core Business Logic

#### 5.1 Position Lifecycle Manager
```python
class PositionLifecycleManager:
    """Manages job position lifecycle: new, active, expired."""
    
    async def process_scraped_jobs(self, company_id: int, scraped_jobs: List[Dict]):
        """
        Process scraped jobs and update database.
        
        Logic:
        1. Get all active positions for this company from DB
        2. For each scraped job:
           - If job_url exists in DB: update last_seen_at
           - If job_url is new: create new position (status=active)
        3. For positions in DB but not in scraped_jobs:
           - Mark as expired (status=expired, expired_at=now)
        """
```



#### 5.2 Alert Matching Engine
```python
class AlertMatcher:
    """Matches new job positions against user alerts."""
    
    async def match_position_to_alerts(self, position: JobPosition) -> List[Alert]:
        """
        Find all alerts that match this position.
        
        Matching Logic:
        - Company filter: position.company_id IN alert.company_ids (if specified)
        - Keywords: any keyword in alert.keywords appears in position.title (if specified)
        - Excluded keywords: no keyword in alert.excluded_keywords appears in title
        - Location: position.location matches any in alert.locations (if specified)
        - Department: position.department matches any in alert.departments (if specified)
        - Remote: position.is_remote == alert.is_remote (if alert.is_remote is not NULL)
        """
        
    async def trigger_alerts(self, new_positions: List[JobPosition]):
        """
        Trigger alerts for new positions.
        
        For each new position:
        1. Find matching alerts
        2. For each matching alert:
           - Create notification record
           - Send notification (email/webhook)
           - Update alert.last_triggered_at and trigger_count
        """
```

---

### 6. Daily Scraping Workflow

```python
# Celery task
@celery.task
async def daily_scraping_task():
    """
    Daily scraping workflow.
    
    Steps:
    1. Get all active companies with scraping_enabled=True
    2. For each company:
       a. Run scraper
       b. Process scraped jobs (PositionLifecycleManager)
       c. Trigger alerts for new positions (AlertMatcher)
       d. Update company.last_scraped_at
       e. Log results
    3. Generate daily summary report
    """
    companies = await Company.get_active_companies()
    
    summary = {
        'total_companies': len(companies),
        'successful_scrapes': 0,
        'failed_scrapes': 0,
        'new_positions': 0,
        'expired_positions': 0,
        'alerts_triggered': 0
    }
    
    for company in companies:
        try:
            # Run scraper
            scraper = create_scraper(company)
            jobs = await scraper.scrape()
            
            # Process positions
            lifecycle_manager = PositionLifecycleManager()
            result = await lifecycle_manager.process_scraped_jobs(company.id, jobs)
            
            # Trigger alerts
            alert_matcher = AlertMatcher()
            await alert_matcher.trigger_alerts(result['new_positions'])
            
            # Update stats
            summary['successful_scrapes'] += 1
            summary['new_positions'] += len(result['new_positions'])
            summary['expired_positions'] += len(result['expired_positions'])
            
            # Update company
            company.last_scraped_at = datetime.utcnow()
            await company.save()
            
        except Exception as e:
            logger.error(f"Failed to scrape {company.name}: {e}")
            summary['failed_scrapes'] += 1
    
    # Send summary report
    await send_daily_summary(summary)
```

---

### 7. Migration Strategy

#### 7.1 Database Setup
```bash
# Local PostgreSQL setup
createdb job_scraper_dev
psql job_scraper_dev < migrations/001_initial_schema.sql

# Remote PostgreSQL (production)
# Use managed service: AWS RDS, Google Cloud SQL, or DigitalOcean
```

#### 7.2 Migration Tools
- **Alembic**: SQLAlchemy migration tool
- Version-controlled migrations
- Rollback capability

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

#### 7.3 Data Migration from YAML
```python
async def migrate_companies_from_yaml():
    """Migrate companies from companies.yaml to database."""
    with open('config/companies.yaml') as f:
        config = yaml.safe_load(f)
    
    for company_data in config['companies']:
        company = Company(
            name=company_data['name'],
            website=company_data['website'],
            careers_url=company_data['careers_url'],
            industry=company_data.get('industry'),
            size=company_data.get('size'),
            location=company_data.get('location'),
            is_active=company_data.get('is_active', True),
            scraping_enabled=True,
            scraping_frequency=company_data.get('scraping_frequency', '0 0 * * *'),
            scraping_config=company_data.get('scraping_config'),
            location_filter=company_data.get('location_filter')
        )
        await company.save()
```

---

### 8. API Endpoints (Future)

```python
# REST API for future web interface
GET    /api/companies                    # List all companies
GET    /api/companies/{id}/positions     # Get positions for company
GET    /api/positions                    # List positions (with filters)
GET    /api/positions/{id}               # Get position details

POST   /api/users                        # Create user
GET    /api/users/{id}/alerts            # Get user's alerts
POST   /api/users/{id}/alerts            # Create alert
PUT    /api/users/{id}/alerts/{alert_id} # Update alert
DELETE /api/users/{id}/alerts/{alert_id} # Delete alert

GET    /api/users/{id}/applications      # Get user's applications
POST   /api/users/{id}/applications      # Track application
```

---

### 9. Monitoring & Observability

#### 9.1 Metrics to Track
- Scraping success rate per company
- New positions detected per day
- Expired positions per day
- Alert trigger rate
- Notification delivery rate
- Database query performance

#### 9.2 Logging
```python
# Structured logging
logger.info("scraping_completed", extra={
    'company_id': company.id,
    'company_name': company.name,
    'jobs_found': len(jobs),
    'new_positions': len(new_positions),
    'duration_seconds': duration
})
```

---

### 10. Implementation Checklist

#### Phase 1: Database Setup (Week 1)
- [ ] Install PostgreSQL locally
- [ ] Create database schema
- [ ] Set up Alembic migrations
- [ ] Create SQLAlchemy models
- [ ] Write database connection manager
- [ ] Test CRUD operations

#### Phase 2: Data Migration (Week 1-2)
- [ ] Migrate companies from YAML to DB
- [ ] Create Company repository
- [ ] Update scrapers to use DB config
- [ ] Test scraping with DB integration

#### Phase 3: Position Lifecycle (Week 2)
- [ ] Implement PositionLifecycleManager
- [ ] Integrate with daily scraping task
- [ ] Test new position detection
- [ ] Test expired position detection
- [ ] Add logging and monitoring

#### Phase 4: User & Alert System (Week 3)
- [ ] Implement User model and repository
- [ ] Implement Alert model and repository
- [ ] Create AlertMatcher engine
- [ ] Implement email notification system
- [ ] Test end-to-end alert flow

#### Phase 5: Production Deployment (Week 4)
- [ ] Set up remote PostgreSQL (AWS RDS / Cloud SQL)
- [ ] Configure production environment variables
- [ ] Run migrations on production DB
- [ ] Deploy Celery workers
- [ ] Set up monitoring and alerts
- [ ] Create backup strategy

---

### 11. Technology Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Database | PostgreSQL 14+ | Primary data store |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Migrations | Alembic | Schema versioning |
| Task Queue | Celery + Redis | Background job processing |
| Web Scraping | Playwright | Browser automation |
| Notifications | SendGrid / AWS SES | Email delivery |
| Logging | Loguru | Structured logging |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |

---

### 12. Security Considerations

1. **Database Security**
   - Use SSL/TLS for database connections
   - Rotate database credentials regularly
   - Implement row-level security if needed

2. **User Data**
   - Hash sensitive data
   - Implement GDPR compliance (data export, deletion)
   - Secure API endpoints with authentication

3. **Scraping Ethics**
   - Respect robots.txt
   - Implement rate limiting
   - Use appropriate user agents
   - Don't overload target servers

---

### 13. File Structure

```
scrapper/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── job_position.py
│   │   ├── alert.py
│   │   ├── user_job_application.py
│   │   └── alert_notification.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── company_repository.py
│   │   ├── job_position_repository.py
│   │   ├── user_repository.py
│   │   └── alert_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── position_lifecycle_manager.py
│   │   ├── alert_matcher.py
│   │   └── notification_service.py
│   └── database/
│       ├── __init__.py
│       ├── connection.py
│       └── session.py
├── migrations/
│   ├── versions/
│   └── env.py
├── config/
│   ├── database.py
│   └── companies.yaml
└── alembic.ini
```

---

### 14. Next Steps

1. **Review and approve** this technical design
2. **Set up local PostgreSQL** and create initial schema
3. **Implement SQLAlchemy models** with proper relationships
4. **Create migration scripts** using Alembic
5. **Test database operations** with sample data
6. **Integrate scrapers** with database
7. **Implement position lifecycle** management
8. **Build alert system** and notification engine
