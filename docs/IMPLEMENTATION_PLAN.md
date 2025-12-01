# Implementation Plan
## PostgreSQL Integration for Job Scraping Platform

### Overview
This document provides a step-by-step implementation plan for integrating PostgreSQL database into the existing job scraping platform.

---

## Phase 1: Local PostgreSQL Setup & Schema Creation

### Step 1.1: Install PostgreSQL Locally
```bash
# macOS (using Homebrew)
brew install postgresql@14
brew services start postgresql@14

# Verify installation
psql --version

# Create database
createdb job_scraper_dev

# Connect to database
psql job_scraper_dev
```

### Step 1.2: Install Python Dependencies
```bash
# Add to requirements.txt
pip install sqlalchemy==2.0.23
pip install psycopg2-binary==2.9.9
pip install alembic==1.12.1
pip install asyncpg==0.29.0  # For async support
```

### Step 1.3: Create Database Configuration
**File**: `config/database.py`
```python
import os
from typing import Dict

class DatabaseConfig:
    """Database configuration for different environments."""
    
    ENVIRONMENTS = {
        'local': {
            'host': 'localhost',
            'port': 5432,
            'database': 'job_scraper_dev',
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
        },
        'production': {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
        }
    }
    
    @classmethod
    def get_database_url(cls, env: str = 'local') -> str:
        """Get SQLAlchemy database URL."""
        config = cls.ENVIRONMENTS[env]
        return (
            f"postgresql://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['database']}"
        )
```

### Step 1.4: Create Database Connection Manager
**File**: `src/database/connection.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from config.database import DatabaseConfig

class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, env: str = 'local'):
        self.database_url = DatabaseConfig.get_database_url(env)
        self.engine = None
        self.session_factory = None
        
    def initialize(self):
        """Initialize database engine and session factory."""
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False  # Set to True for SQL logging
        )
        
        self.session_factory = scoped_session(
            sessionmaker(bind=self.engine, expire_on_commit=False)
        )
        
    def get_session(self):
        """Get a new database session."""
        return self.session_factory()
    
    def close(self):
        """Close all connections."""
        if self.session_factory:
            self.session_factory.remove()
        if self.engine:
            self.engine.dispose()

# Global database manager instance
db_manager = DatabaseManager()
```

---

## Phase 2: SQLAlchemy Models Implementation

### Step 2.1: Create Base Model
**File**: `src/models/base.py`
```python
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
```

### Step 2.2: Create Models (in order)

#### 2.2.1 User Model
**File**: `src/models/user.py`
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    last_login_at = Column(DateTime)
    preferences = Column(JSONB, default={})
    
    # Relationships
    alerts = relationship('Alert', back_populates='user', cascade='all, delete-orphan')
    applications = relationship('UserJobApplication', back_populates='user')
    notifications = relationship('AlertNotification', back_populates='user')
```

#### 2.2.2 Company Model
**File**: `src/models/company.py`
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Company(Base, TimestampMixin):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    website = Column(String(500))
    careers_url = Column(String(500))
    industry = Column(String(255))
    size = Column(String(50))
    location = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    scraping_enabled = Column(Boolean, default=True, index=True)
    scraping_frequency = Column(String(50), default='0 0 * * *')
    last_scraped_at = Column(DateTime)
    scraping_config = Column(JSONB)
    location_filter = Column(JSONB)
    metadata = Column(JSONB, default={})
    
    # Relationships
    job_positions = relationship('JobPosition', back_populates='company')
```

#### 2.2.3 JobPosition Model
**File**: `src/models/job_position.py`
```python
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class JobPosition(Base, TimestampMixin):
    __tablename__ = 'job_positions'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Job details
    title = Column(String(500), nullable=False, index=True)
    location = Column(String(255), index=True)
    department = Column(String(255))
    employment_type = Column(String(50))
    job_url = Column(String(1000), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Status & lifecycle
    status = Column(String(50), default='active', index=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    expired_at = Column(DateTime)
    
    # Metadata
    is_remote = Column(Boolean, default=False)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_currency = Column(String(10))
    experience_level = Column(String(50))
    raw_data = Column(JSONB)
    
    # Relationships
    company = relationship('Company', back_populates='job_positions')
    applications = relationship('UserJobApplication', back_populates='job_position')
    notifications = relationship('AlertNotification', back_populates='job_position')
```

#### 2.2.4 Alert Model
**File**: `src/models/alert.py`
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Alert(Base, TimestampMixin):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Alert configuration
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    
    # Matching criteria
    company_ids = Column(ARRAY(Integer), default=[])
    keywords = Column(ARRAY(String), default=[])
    excluded_keywords = Column(ARRAY(String), default=[])
    locations = Column(ARRAY(String), default=[])
    departments = Column(ARRAY(String), default=[])
    employment_types = Column(ARRAY(String), default=[])
    is_remote = Column(Boolean)
    
    # Notification settings
    notification_method = Column(String(50), default='email')
    notification_config = Column(JSONB, default={})
    
    # Tracking
    last_triggered_at = Column(DateTime)
    trigger_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship('User', back_populates='alerts')
    notifications = relationship('AlertNotification', back_populates='alert')
```

#### 2.2.5 UserJobApplication Model
**File**: `src/models/user_job_application.py`
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class UserJobApplication(Base, TimestampMixin):
    __tablename__ = 'user_job_applications'
    __table_args__ = (
        UniqueConstraint('user_id', 'job_position_id', name='uq_user_job'),
    )
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    job_position_id = Column(Integer, ForeignKey('job_positions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Application status
    status = Column(String(50), default='interested', index=True)
    applied_at = Column(DateTime)
    notes = Column(Text)
    
    # Relationships
    user = relationship('User', back_populates='applications')
    job_position = relationship('JobPosition', back_populates='applications')
```

#### 2.2.6 AlertNotification Model
**File**: `src/models/alert_notification.py`
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class AlertNotification(Base):
    __tablename__ = 'alert_notifications'
    
    id = Column(Integer, primary_key=True)
    alert_id = Column(Integer, ForeignKey('alerts.id', ondelete='CASCADE'), nullable=False, index=True)
    job_position_id = Column(Integer, ForeignKey('job_positions.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Notification details
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    delivery_status = Column(String(50), default='pending')
    delivery_method = Column(String(50))
    error_message = Column(Text)
    
    # Relationships
    alert = relationship('Alert', back_populates='notifications')
    job_position = relationship('JobPosition', back_populates='notifications')
    user = relationship('User', back_populates='notifications')
```

---

## Phase 3: Database Migrations with Alembic

### Step 3.1: Initialize Alembic
```bash
# Initialize Alembic
alembic init alembic

# This creates:
# - alembic/ directory
# - alembic.ini configuration file
```

### Step 3.2: Configure Alembic
**File**: `alembic/env.py` (modify)
```python
from src.models.base import Base
from src.models.user import User
from src.models.company import Company
from src.models.job_position import JobPosition
from src.models.alert import Alert
from src.models.user_job_application import UserJobApplication
from src.models.alert_notification import AlertNotification

target_metadata = Base.metadata
```

**File**: `alembic.ini` (modify)
```ini
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/job_scraper_dev
```

### Step 3.3: Create Initial Migration
```bash
# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Review the generated migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

### Step 3.4: Verify Schema
```bash
# Connect to database
psql job_scraper_dev

# List tables
\dt

# Describe a table
\d job_positions
```

---

## Phase 4: Repository Pattern Implementation

### Step 4.1: Base Repository
**File**: `src/repositories/base_repository.py`
```python
from typing import TypeVar, Generic, List, Optional
from sqlalchemy.orm import Session

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model_class: type, session: Session):
        self.model_class = model_class
        self.session = session
    
    def create(self, **kwargs) -> T:
        """Create a new record."""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get record by ID."""
        return self.session.query(self.model_class).filter_by(id=id).first()
    
    def get_all(self) -> List[T]:
        """Get all records."""
        return self.session.query(self.model_class).all()
    
    def update(self, id: int, **kwargs) -> Optional[T]:
        """Update a record."""
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            self.session.commit()
            self.session.refresh(instance)
        return instance
    
    def delete(self, id: int) -> bool:
        """Delete a record."""
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.commit()
            return True
        return False
```

---

## Next Steps Summary

1. ✅ **Review PRD and Technical Design** documents
2. ⏳ **Set up local PostgreSQL** (Step 1.1-1.4)
3. ⏳ **Implement SQLAlchemy models** (Step 2.1-2.2)
4. ⏳ **Create and run migrations** (Step 3.1-3.4)
5. ⏳ **Implement repositories** (Step 4.1+)
6. ⏳ **Migrate companies from YAML to DB**
7. ⏳ **Implement Position Lifecycle Manager**
8. ⏳ **Implement Alert Matcher**
9. ⏳ **Test end-to-end workflow**
10. ⏳ **Deploy to production**

---

## Questions to Answer Before Starting

1. **Database Hosting**: Where will production database be hosted?
   - AWS RDS PostgreSQL?
   - Google Cloud SQL?
   - DigitalOcean Managed Database?
   - Self-hosted?

2. **Email Service**: Which email service for notifications?
   - SendGrid?
   - AWS SES?
   - Mailgun?
   - SMTP?

3. **User Authentication**: Do we need user authentication in v1?
   - Yes: Implement JWT/OAuth
   - No: Simple email-based identification

4. **Data Retention**: How long to keep expired positions?
   - 30 days?
   - 90 days?
   - Forever?

5. **Alert Frequency**: How often should alerts be sent?
   - Immediately when new job found?
   - Daily digest?
   - User configurable?

