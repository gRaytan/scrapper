# Step 3: Database Configuration - Detailed Explanation

## Overview

Step 3 is about setting up the **database configuration layer** that connects your SQLAlchemy models to PostgreSQL. This layer handles:

1. **Database connection management** (connection pooling, timeouts, retries)
2. **Session management** (creating, committing, rolling back transactions)
3. **Environment-specific configuration** (local vs production databases)
4. **Connection lifecycle** (opening, closing, cleanup)

---

## Good News! 🎉

**You already have most of Step 3 implemented!** Let me explain what exists and what (if anything) needs to be updated.

---

## What You Already Have

### ✅ 1. Database Connection Manager (`src/storage/database.py`)

**Location:** `src/storage/database.py`

**What it does:**
```python
class Database:
    def __init__(self):
        # Creates SQLAlchemy engine with connection pooling
        self.engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,      # Verify connections before using
            pool_size=10,             # Keep 10 connections in pool
            max_overflow=20,          # Allow 20 extra connections if needed
            echo=False,               # Don't log SQL queries (unless debug=True)
        )
        
        # Creates session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,         # Manual transaction control
            autoflush=False,          # Manual flush control
            bind=self.engine
        )
```

**Key Features:**
- ✅ **Connection pooling** - Reuses database connections for performance
- ✅ **Pool pre-ping** - Tests connections before use (handles stale connections)
- ✅ **Session factory** - Creates new sessions for each request/task
- ✅ **Context manager** - `with db.get_session()` for automatic cleanup
- ✅ **Dependency injection** - `get_db()` for FastAPI endpoints

**Methods:**
1. `create_tables()` - Creates all tables (useful for testing, but we'll use Alembic for production)
2. `drop_tables()` - Drops all tables (dangerous! only for testing)
3. `get_session()` - Context manager for transactions
4. `get_db()` - Generator for FastAPI dependency injection

---

### ✅ 2. Settings Configuration (`config/settings.py`)

**Location:** `config/settings.py`

**What it does:**
```python
class Settings(BaseSettings):
    # Database configuration
    database_url: str = "postgresql://scraper:password@localhost:5432/scraper_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Environment
    environment: str = "development"
    debug: bool = True
```

**Key Features:**
- ✅ **Environment variables** - Reads from `.env` file
- ✅ **Type validation** - Uses Pydantic for type checking
- ✅ **Default values** - Sensible defaults for development
- ✅ **Properties** - Helper methods like `is_production`, `db_echo`

---

## What Needs to Be Updated

### 🔧 Update 1: Database URL for Local Development

**Current setting:**
```python
database_url: str = "postgresql://scraper:password@localhost:5432/scraper_db"
```

**Should be:**
```python
database_url: str = "postgresql://localhost:5432/job_scraper_dev"
```

**Why?** 
- We created `job_scraper_dev` database in Step 1
- Local PostgreSQL doesn't require username/password by default
- Matches our setup from Phase 1 & 2

---

### 🔧 Update 2: Create `.env` File (if it doesn't exist)

**Location:** `.env` (in project root)

**Purpose:** Store environment-specific configuration without hardcoding

**Example `.env` file:**
```bash
# Environment
ENVIRONMENT=development
DEBUG=true

# Database - Local Development
DATABASE_URL=postgresql://localhost:5432/job_scraper_dev
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Database - Production (commented out for now)
# DATABASE_URL=postgresql://user:password@production-host:5432/job_scraper_prod
# DATABASE_POOL_SIZE=20
# DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
```

---

## How Database Configuration Works

### 1. **Application Startup**

```python
# When your app starts
from src.storage.database import db

# Database engine is created automatically
# Connection pool is initialized
# Ready to accept connections
```

### 2. **Using Sessions in Code**

**Option A: Context Manager (Recommended for scripts/workers)**
```python
from src.storage.database import db

# Automatic commit/rollback
with db.get_session() as session:
    # Create a new user
    user = User(email="john@example.com", full_name="John Doe")
    session.add(user)
    # Automatically commits when exiting context
    # Automatically rolls back if exception occurs
```

**Option B: Dependency Injection (For FastAPI endpoints)**
```python
from fastapi import Depends
from sqlalchemy.orm import Session
from src.storage.database import get_db_session

@app.get("/users")
def get_users(db: Session = Depends(get_db_session)):
    users = db.query(User).all()
    return users
```

**Option C: Manual Session (For Celery tasks)**
```python
from src.storage.database import db

@celery_app.task
def scrape_company(company_id: str):
    session = db.SessionLocal()
    try:
        company = session.query(Company).filter_by(id=company_id).first()
        # Do scraping work
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
```

---

## Connection Pooling Explained

### What is Connection Pooling?

Instead of creating a new database connection for every request (slow!), we maintain a **pool of reusable connections**.

```
┌─────────────────────────────────────────────────────────────┐
│                    Connection Pool                          │
│                                                              │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐         │
│  │ Conn │  │ Conn │  │ Conn │  │ Conn │  │ Conn │  ...    │
│  │  1   │  │  2   │  │  3   │  │  4   │  │  5   │         │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘         │
│     ↓         ↓         ↓         ↓         ↓              │
│  [idle]   [in use]  [idle]   [in use]  [idle]             │
└─────────────────────────────────────────────────────────────┘
```

**Settings:**
- `pool_size=10` - Keep 10 connections ready
- `max_overflow=20` - Can create 20 more if needed (total: 30)
- `pool_pre_ping=True` - Test connection before using (handles disconnects)

**Benefits:**
- ⚡ **Fast** - Reuse existing connections
- 🔒 **Safe** - Handles connection failures gracefully
- 📊 **Scalable** - Supports concurrent requests

---

## Environment-Specific Configuration

### Local Development
```python
DATABASE_URL=postgresql://localhost:5432/job_scraper_dev
DEBUG=true
DB_ECHO=true  # Log all SQL queries for debugging
```

### Production
```python
DATABASE_URL=postgresql://user:password@prod-host.rds.amazonaws.com:5432/job_scraper_prod
DEBUG=false
DB_ECHO=false  # Don't log SQL queries (performance)
DATABASE_POOL_SIZE=20  # More connections for production
DATABASE_MAX_OVERFLOW=40
```

---

## Step 3 Checklist

### ✅ Already Complete
- [x] Database connection manager (`src/storage/database.py`)
- [x] Settings configuration (`config/settings.py`)
- [x] Connection pooling setup
- [x] Session management
- [x] Context managers
- [x] Dependency injection support

### 🔧 Needs Update
- [ ] Update `database_url` in `config/settings.py` to `postgresql://localhost:5432/job_scraper_dev`
- [ ] Create `.env` file with local configuration
- [ ] Test database connection with new models

### 📝 Optional Enhancements
- [ ] Add async session support (for async/await code)
- [ ] Add connection retry logic
- [ ] Add database health check endpoint
- [ ] Add connection pool monitoring

---

## Testing the Configuration

### Test 1: Verify Connection
```python
from src.storage.database import db
from sqlalchemy import text

with db.get_session() as session:
    result = session.execute(text("SELECT version();"))
    print(result.fetchone()[0])
    # Should print PostgreSQL version
```

### Test 2: Create Tables
```python
from src.storage.database import db

# Create all tables from models
db.create_tables()

# Verify tables exist
from sqlalchemy import inspect
inspector = inspect(db.engine)
tables = inspector.get_table_names()
print(f"Tables created: {tables}")
# Should print: ['users', 'companies', 'job_positions', 'alerts', ...]
```

### Test 3: CRUD Operations
```python
from src.storage.database import db
from src.models import User

# Create
with db.get_session() as session:
    user = User(email="test@example.com", full_name="Test User")
    session.add(user)
    # Auto-commits when exiting context

# Read
with db.get_session() as session:
    user = session.query(User).filter_by(email="test@example.com").first()
    print(f"Found user: {user.full_name}")

# Update
with db.get_session() as session:
    user = session.query(User).filter_by(email="test@example.com").first()
    user.full_name = "Updated Name"
    # Auto-commits

# Delete
with db.get_session() as session:
    user = session.query(User).filter_by(email="test@example.com").first()
    session.delete(user)
    # Auto-commits
```

---

## Summary

**Step 3 is about:** Setting up the database configuration layer that manages connections, sessions, and environment-specific settings.

**Good news:** You already have a solid implementation in `src/storage/database.py`!

**What you need to do:**
1. ✅ Update `database_url` in settings to match your local database
2. ✅ Create `.env` file with configuration
3. ✅ Test the connection

**After Step 3, you'll be ready for:**
- **Step 4:** Initialize Alembic for database migrations
- **Step 5:** Create initial migration from your models
- **Step 6:** Apply migration to create tables in PostgreSQL

---

## Next: Step 4 Preview

Step 4 will set up **Alembic** - a database migration tool that:
- Tracks schema changes over time
- Generates migration scripts automatically
- Allows rolling back changes
- Keeps development and production databases in sync

Think of it like "Git for your database schema"! 🚀

