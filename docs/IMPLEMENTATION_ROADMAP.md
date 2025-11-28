# Implementation Roadmap
## Job Scraping & Notification System

**Version:** 1.0  
**Last Updated:** November 19, 2025

---

## Overview

This document provides a detailed, step-by-step implementation plan for building the job notification system. Each phase includes specific tasks, file changes, and acceptance criteria.

---

## Phase 1: Database Models & Migrations (Week 1)

### Goals
- Create new database models for users, alerts, and notifications
- Set up Alembic for database migrations
- Write repository classes for data access

### Tasks

#### 1.1 Set up Alembic
```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic

# Configure alembic.ini and env.py
```

**Files to Create/Modify:**
- `alembic/env.py` - Configure to use existing Base and models
- `alembic.ini` - Set database URL
- `alembic/versions/` - Migration files

#### 1.2 Create User Model
**File:** `src/models/user.py`

```python
from sqlalchemy import Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, UUIDMixin, TimestampMixin

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # ... additional fields
    
    # Relationships
    job_alerts = relationship("JobAlert", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
```

#### 1.3 Create JobAlert Model
**File:** `src/models/job_alert.py`

```python
from sqlalchemy import String, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, UUIDMixin, TimestampMixin

class JobAlert(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "job_alerts"
    
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    filters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    notification_frequency: Mapped[str] = mapped_column(String(50), default="daily")
    # ... additional fields
    
    # Relationships
    user = relationship("User", back_populates="job_alerts")
```

#### 1.4 Create Notification Model
**File:** `src/models/notification.py`

#### 1.5 Create UserJobInteraction Model
**File:** `src/models/user_job_interaction.py`

#### 1.6 Create Repository Classes
**Files:**
- `src/storage/repositories/user_repo.py`
- `src/storage/repositories/alert_repo.py`
- `src/storage/repositories/notification_repo.py`

#### 1.7 Create Initial Migration
```bash
alembic revision --autogenerate -m "Add user, job_alert, notification tables"
alembic upgrade head
```

### Acceptance Criteria
- [ ] All models created with proper relationships
- [ ] Migration runs successfully
- [ ] Repository classes implement CRUD operations
- [ ] Unit tests pass (>80% coverage)

### Estimated Time: 5 days

---

## Phase 2: User Management & Authentication (Week 2)

### Goals
- Implement user registration and login
- Add JWT authentication
- Create password reset flow

### Tasks

#### 2.1 Install Dependencies
```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

#### 2.2 Create Authentication Utilities
**File:** `src/auth/security.py`

```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    # JWT token creation logic
    pass
```

#### 2.3 Create Pydantic Schemas
**File:** `src/api/schemas/user.py`

```python
from pydantic import BaseModel, EmailStr, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        # Add more validation
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    is_verified: bool
    created_at: datetime
```

#### 2.4 Create Authentication Routes
**File:** `src/api/routes/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Registration logic
    pass

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Login logic
    pass

@router.post("/forgot-password")
async def forgot_password(email: EmailStr, db: Session = Depends(get_db)):
    # Password reset logic
    pass
```

#### 2.5 Create User Routes
**File:** `src/api/routes/users.py`

#### 2.6 Add Authentication Middleware
**File:** `src/api/dependencies.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    # Verify JWT and return user
    pass

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

#### 2.7 Update FastAPI App
**File:** `src/api/app.py`

```python
from src.api.routes import auth, users

app.include_router(auth.router)
app.include_router(users.router)
```

### Acceptance Criteria
- [ ] Users can register with email/password
- [ ] Users can login and receive JWT token
- [ ] Password reset flow works end-to-end
- [ ] Protected endpoints require authentication
- [ ] API tests pass (>80% coverage)

### Estimated Time: 5 days

---

## Phase 3: Job Alert Management (Week 3)

### Goals
- Create CRUD API for job alerts
- Implement filter validation
- Build alert preview/testing feature

### Tasks

#### 3.1 Create Alert Schemas
**File:** `src/api/schemas/alert.py`

```python
from pydantic import BaseModel, validator
from typing import List, Optional

class AlertFilters(BaseModel):
    companies: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    employment_types: Optional[List[str]] = None
    is_remote: Optional[bool] = None
    min_posted_days_ago: Optional[int] = None

class AlertCreate(BaseModel):
    name: str
    filters: AlertFilters
    notification_frequency: str = "daily"
    notification_channels: List[str] = ["email"]

class AlertResponse(BaseModel):
    id: UUID
    name: str
    filters: AlertFilters
    is_active: bool
    notification_frequency: str
    last_notified_at: Optional[datetime]
    created_at: datetime
```

#### 3.2 Create Alert Routes
**File:** `src/api/routes/alerts.py`

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])

@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # List user's alerts
    pass

@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Create alert
    pass

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: UUID, ...):
    pass

@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(alert_id: UUID, alert_data: AlertUpdate, ...):
    pass

@router.delete("/{alert_id}")
async def delete_alert(alert_id: UUID, ...):
    pass

@router.post("/{alert_id}/test", response_model=List[JobResponse])
async def test_alert(alert_id: UUID, ...):
    # Preview matching jobs
    pass
```

#### 3.3 Implement Filter Validation
**File:** `src/services/alert_service.py`

```python
class AlertService:
    def validate_filters(self, filters: AlertFilters) -> bool:
        # Validate filter criteria
        pass
    
    def preview_matches(self, filters: AlertFilters, db: Session) -> List[JobPosition]:
        # Apply filters to current jobs and return matches
        pass
```

### Acceptance Criteria
- [ ] Users can create/edit/delete alerts
- [ ] Filter validation works correctly
- [ ] Alert preview shows matching jobs
- [ ] API tests pass

### Estimated Time: 5 days

---

## Phase 4: Job Matching Engine (Week 4)

### Goals
- Build efficient job matching algorithm
- Optimize with database indexes
- Add caching layer

### Tasks

#### 4.1 Create Matching Service
**File:** `src/services/matching_service.py`

```python
from typing import List, Dict
from sqlalchemy import and_, or_
from src.models import JobPosition, JobAlert

class JobMatchingService:
    def __init__(self, db: Session):
        self.db = db
    
    def find_matches_for_alert(self, alert: JobAlert, new_jobs: List[JobPosition]) -> List[JobPosition]:
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
        if filters.get('companies') and job.company.name not in filters['companies']:
            return False
        
        # Keyword filter
        if filters.get('keywords'):
            job_text = f"{job.title} {job.description}".lower()
            if not any(kw.lower() in job_text for kw in filters['keywords']):
                return False
        
        # Exclude keywords
        if filters.get('exclude_keywords'):
            job_text = f"{job.title} {job.description}".lower()
            if any(kw.lower() in job_text for kw in filters['exclude_keywords']):
                return False
        
        # Location filter
        if filters.get('locations') and job.location not in filters['locations']:
            return False
        
        # Department filter
        if filters.get('departments') and job.department not in filters['departments']:
            return False
        
        # Employment type filter
        if filters.get('employment_types') and job.employment_type not in filters['employment_types']:
            return False
        
        # Remote filter
        if filters.get('is_remote') is not None and job.is_remote != filters['is_remote']:
            return False
        
        # Posted date filter
        if filters.get('min_posted_days_ago'):
            cutoff = datetime.utcnow() - timedelta(days=filters['min_posted_days_ago'])
            if job.posted_date and job.posted_date < cutoff:
                return False
        
        return True
    
    def match_all_alerts(self, new_jobs: List[JobPosition]) -> Dict[UUID, List[JobPosition]]:
        """Match new jobs against all active alerts.
        
        Returns:
            Dict mapping user_id to list of matching jobs
        """
        user_matches = {}
        
        # Get all active alerts
        alerts = self.db.query(JobAlert).filter(JobAlert.is_active == True).all()
        
        for alert in alerts:
            matches = self.find_matches_for_alert(alert, new_jobs)
            if matches:
                if alert.user_id not in user_matches:
                    user_matches[alert.user_id] = []
                user_matches[alert.user_id].extend(matches)
        
        return user_matches
```

#### 4.2 Optimize Database Queries
**File:** `alembic/versions/xxx_add_indexes_for_matching.py`

```python
def upgrade():
    # Add indexes for efficient filtering
    op.create_index('idx_job_positions_company_active', 'job_positions', ['company_id', 'is_active'])
    op.create_index('idx_job_positions_posted_date', 'job_positions', ['posted_date'])
    op.create_index('idx_job_positions_location', 'job_positions', ['location'])
    op.create_index('idx_job_positions_department', 'job_positions', ['department'])
    
    # GIN index for full-text search on title and description
    op.execute("""
        CREATE INDEX idx_job_positions_search 
        ON job_positions 
        USING GIN(to_tsvector('english', title || ' ' || description))
    """)
```

#### 4.3 Add Redis Caching
**File:** `src/services/cache_service.py`

```python
import redis
import json
from typing import Optional, List

class CacheService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)
    
    def cache_alert_matches(self, alert_id: UUID, job_ids: List[UUID], ttl: int = 3600):
        """Cache matching job IDs for an alert."""
        key = f"alert_matches:{alert_id}"
        self.redis_client.setex(key, ttl, json.dumps([str(jid) for jid in job_ids]))
    
    def get_cached_matches(self, alert_id: UUID) -> Optional[List[UUID]]:
        """Get cached matches for an alert."""
        key = f"alert_matches:{alert_id}"
        data = self.redis_client.get(key)
        if data:
            return [UUID(jid) for jid in json.loads(data)]
        return None
```

### Acceptance Criteria
- [ ] Matching algorithm correctly filters jobs
- [ ] Can process 10K jobs against 10K alerts in <10 minutes
- [ ] Database indexes improve query performance
- [ ] Caching reduces redundant computations
- [ ] Unit tests pass (>90% coverage)

### Estimated Time: 5 days

---

## Phase 5: Notification System (Week 5-6)

### Goals
- Integrate email service
- Build notification templates
- Implement batching and delivery

### Tasks

#### 5.1 Install Email Dependencies
```bash
pip install sendgrid python-dotenv jinja2
```

#### 5.2 Create Email Service
**File:** `src/services/email_service.py`

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from jinja2 import Environment, FileSystemLoader

class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(settings.sendgrid_api_key)
        self.template_env = Environment(loader=FileSystemLoader('src/templates/email'))
    
    def send_job_alert_email(self, user: User, alert: JobAlert, jobs: List[JobPosition]):
        """Send job alert email to user."""
        template = self.template_env.get_template('job_alert.html')
        html_content = template.render(
            user=user,
            alert=alert,
            jobs=jobs,
            unsubscribe_url=f"{settings.app_url}/unsubscribe/{alert.id}"
        )
        
        message = Mail(
            from_email=settings.from_email,
            to_emails=user.email,
            subject=f"[{len(jobs)} New Jobs] Your Job Alert: {alert.name}",
            html_content=html_content
        )
        
        try:
            response = self.sg.send(message)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
```

#### 5.3 Create Email Templates
**File:** `src/templates/email/job_alert.html`

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* Email styles */
    </style>
</head>
<body>
    <h1>Hi {{ user.full_name or 'there' }}!</h1>
    <p>We found {{ jobs|length }} new jobs matching your alert "{{ alert.name }}":</p>
    
    {% for job in jobs %}
    <div class="job-card">
        <h2>{{ job.title }}</h2>
        <p><strong>{{ job.company.name }}</strong> - {{ job.location }}</p>
        <p>{{ job.description[:200] }}...</p>
        <a href="{{ job.job_url }}">Apply Now</a>
    </div>
    {% endfor %}
    
    <p><a href="{{ unsubscribe_url }}">Unsubscribe from this alert</a></p>
</body>
</html>
```

#### 5.4 Create Notification Service
**File:** `src/services/notification_service.py`

```python
from typing import List, Dict
from src.models import User, JobAlert, JobPosition, Notification

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    def create_and_send_notifications(self, user_matches: Dict[UUID, List[JobPosition]]):
        """Create notification records and send emails."""
        for user_id, jobs in user_matches.items():
            user = self.db.query(User).get(user_id)
            alerts = self.db.query(JobAlert).filter(
                JobAlert.user_id == user_id,
                JobAlert.is_active == True
            ).all()
            
            for alert in alerts:
                # Filter jobs for this specific alert
                alert_jobs = self._filter_jobs_for_alert(jobs, alert)
                
                if alert_jobs:
                    # Create notification record
                    notification = Notification(
                        user_id=user_id,
                        alert_id=alert.id,
                        type="job_match",
                        title=f"{len(alert_jobs)} new jobs match your alert",
                        data={"job_ids": [str(j.id) for j in alert_jobs]}
                    )
                    self.db.add(notification)
                    
                    # Send email
                    if "email" in alert.notification_channels:
                        success = self.email_service.send_job_alert_email(user, alert, alert_jobs)
                        notification.delivery_status = {"email": "sent" if success else "failed"}
                    
                    # Update alert last_notified_at
                    alert.last_notified_at = datetime.utcnow()
            
            self.db.commit()
```

### Acceptance Criteria
- [ ] Email service integration works
- [ ] Email templates render correctly
- [ ] Notifications are created in database
- [ ] Emails are sent successfully
- [ ] Unsubscribe links work
- [ ] Integration tests pass

### Estimated Time: 7-10 days

---

## Phase 6: Scheduler & Workers (Week 7)

### Goals
- Configure Celery for background tasks
- Set up daily scraping schedule
- Implement notification workers

### Tasks

#### 6.1 Create Celery App
**File:** `src/workers/celery_app.py`

```python
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    'job_scraper',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Schedule daily scraping
celery_app.conf.beat_schedule = {
    'daily-scraping': {
        'task': 'src.workers.tasks.run_daily_scraping',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM UTC
    },
}
```

#### 6.2 Create Worker Tasks
**File:** `src/workers/tasks.py`

```python
from src.workers.celery_app import celery_app
from src.orchestrator.scraper_orchestrator import ScraperOrchestrator
from src.services.matching_service import JobMatchingService
from src.services.notification_service import NotificationService

@celery_app.task
def run_daily_scraping():
    """Daily scraping task."""
    logger.info("Starting daily scraping...")
    orchestrator = ScraperOrchestrator()
    
    # Run scraping for all companies
    asyncio.run(orchestrator.scrape_all_companies(incremental=True))
    
    # Trigger notification matching
    process_new_jobs.delay()

@celery_app.task
def process_new_jobs():
    """Process new jobs and send notifications."""
    with db.get_session() as session:
        # Get jobs created in last 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)
        new_jobs = session.query(JobPosition).filter(
            JobPosition.created_at >= cutoff
        ).all()
        
        if not new_jobs:
            logger.info("No new jobs found")
            return
        
        # Match jobs with alerts
        matching_service = JobMatchingService(session)
        user_matches = matching_service.match_all_alerts(new_jobs)
        
        # Send notifications
        notification_service = NotificationService(session)
        notification_service.create_and_send_notifications(user_matches)
        
        logger.success(f"Processed {len(new_jobs)} new jobs, sent notifications to {len(user_matches)} users")
```

### Acceptance Criteria
- [ ] Celery workers start successfully
- [ ] Daily scraping runs on schedule
- [ ] Notifications are sent after scraping
- [ ] Failed tasks are retried
- [ ] Monitoring shows task status

### Estimated Time: 5 days

---

## Phase 7-8: API, Frontend & Deployment (Week 8-12)

See separate implementation documents for:
- REST API completion
- Admin dashboard
- User dashboard
- Production deployment to Neon + hosting

---

## Testing Strategy

### Unit Tests
- Models: Test relationships, validations
- Repositories: Test CRUD operations
- Services: Test business logic
- Utilities: Test helper functions

### Integration Tests
- API endpoints: Test request/response
- Database: Test migrations, queries
- Email: Test template rendering, sending
- Matching: Test end-to-end matching flow

### Performance Tests
- Load test: 10K users, 100K jobs
- Scraping: 100 companies in <2 hours
- Matching: 10K jobs × 10K alerts in <10 minutes

---

## Deployment Checklist

- [ ] Set up Neon PostgreSQL database
- [ ] Configure environment variables
- [ ] Run database migrations
- [ ] Deploy API server
- [ ] Deploy Celery workers
- [ ] Configure Celery Beat scheduler
- [ ] Set up monitoring (Sentry, Prometheus)
- [ ] Configure email service (SendGrid)
- [ ] Set up SSL certificates
- [ ] Configure domain and DNS
- [ ] Load test in staging
- [ ] Security audit
- [ ] Documentation complete
- [ ] Beta testing complete

---

**Next Steps:** Begin Phase 1 implementation

