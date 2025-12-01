# PostgreSQL Setup Complete ✅

## Phase 1 & 2: Database Setup - COMPLETED

### ✅ Step 1: PostgreSQL Installation

**Installed:**
- PostgreSQL 14.20 (Homebrew)
- Dependencies: icu4c@78, krb5

**Service Status:**
- ✅ PostgreSQL service started and running
- ✅ Auto-start on login enabled

**Database Created:**
- Database name: `job_scraper_dev`
- Location: `/opt/homebrew/var/postgresql@14`
- Encoding: UTF-8
- Locale: en_US.UTF-8

**PostgreSQL Commands:**
```bash
# Start service
brew services start postgresql@14

# Stop service
brew services stop postgresql@14

# Restart service
brew services restart postgresql@14

# Connect to database
/opt/homebrew/opt/postgresql@14/bin/psql -d job_scraper_dev

# Create new database
/opt/homebrew/opt/postgresql@14/bin/createdb <database_name>
```

---

### ✅ Step 2: Python Dependencies

**Already Installed (from requirements.txt):**
- ✅ `sqlalchemy==2.0.23` - ORM framework
- ✅ `psycopg2-binary==2.9.9` - PostgreSQL driver
- ✅ `alembic==1.13.1` - Database migrations
- ✅ `asyncpg==0.29.0` - Async PostgreSQL driver

**Verification:**
```bash
python3 -c "import sqlalchemy; print(sqlalchemy.__version__)"
# Output: 2.0.23

python3 -c "import psycopg2; print(psycopg2.__version__)"
# Output: 2.9.9 (dt dec pq3 ext lo64)

python3 -c "import alembic; print(alembic.__version__)"
# Output: 1.13.1

python3 -c "import asyncpg; print(asyncpg.__version__)"
# Output: 0.29.0
```

**Database Connection Test:**
```python
from sqlalchemy import create_engine, text

database_url = "postgresql://localhost:5432/job_scraper_dev"
engine = create_engine(database_url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print(result.fetchone()[0])
```

✅ **Connection test passed successfully!**

---

## Next Steps: Phase 3 - Implementation

### Step 3: Create Directory Structure
```bash
mkdir -p src/models
mkdir -p src/repositories
mkdir -p src/services
mkdir -p src/database
mkdir -p migrations/versions
```

### Step 4: Implement SQLAlchemy Models

**Files to create:**
1. `src/models/base.py` - Base model and mixins
2. `src/models/user.py` - User model
3. `src/models/company.py` - Company model
4. `src/models/job_position.py` - JobPosition model
5. `src/models/alert.py` - Alert model
6. `src/models/user_job_application.py` - UserJobApplication model
7. `src/models/alert_notification.py` - AlertNotification model
8. `src/models/__init__.py` - Export all models

### Step 5: Database Configuration

**Files to create:**
1. `config/database.py` - Database configuration
2. `src/database/connection.py` - Connection manager
3. `src/database/session.py` - Session management
4. `src/database/__init__.py` - Exports

### Step 6: Alembic Setup

**Commands to run:**
```bash
# Initialize Alembic
alembic init alembic

# Configure alembic.ini and env.py
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### Step 7: Data Migration

**Create migration script:**
- `scripts/migrate_companies_to_db.py` - Load companies from YAML to DB

### Step 8: Repository Pattern

**Files to create:**
1. `src/repositories/base_repository.py` - Base CRUD operations
2. `src/repositories/company_repository.py` - Company-specific queries
3. `src/repositories/job_position_repository.py` - Job position queries
4. `src/repositories/user_repository.py` - User queries
5. `src/repositories/alert_repository.py` - Alert queries

### Step 9: Business Logic

**Files to create:**
1. `src/services/position_lifecycle_manager.py` - Handle new/expired positions
2. `src/services/alert_matcher.py` - Match jobs to alerts
3. `src/services/notification_service.py` - Send notifications

### Step 10: Integration

**Update existing scrapers:**
- Modify scraper tasks to use PositionLifecycleManager
- Store scraped jobs in database
- Trigger alert matching for new positions

---

## Database Connection Info

**Local Development:**
- Host: `localhost`
- Port: `5432`
- Database: `job_scraper_dev`
- User: `<your_username>` (default: current user)
- Password: (none required for local)

**Connection String:**
```
postgresql://localhost:5432/job_scraper_dev
```

**SQLAlchemy URL:**
```python
DATABASE_URL = "postgresql://localhost:5432/job_scraper_dev"
```

---

## Useful PostgreSQL Commands

### Database Management
```bash
# List all databases
/opt/homebrew/opt/postgresql@14/bin/psql -l

# Connect to database
/opt/homebrew/opt/postgresql@14/bin/psql -d job_scraper_dev

# Create database
/opt/homebrew/opt/postgresql@14/bin/createdb <name>

# Drop database
/opt/homebrew/opt/postgresql@14/bin/dropdb <name>
```

### Inside psql
```sql
-- List all tables
\dt

-- Describe table
\d table_name

-- List all schemas
\dn

-- List all users
\du

-- Show current database
SELECT current_database();

-- Show all tables with row counts
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Exit psql
\q
```

---

## Environment Variables

**Create `.env` file:**
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=job_scraper_dev
DB_USER=<your_username>
DB_PASSWORD=

# Environment
ENVIRONMENT=local

# For production
# DB_HOST=<production_host>
# DB_NAME=job_scraper_prod
# DB_USER=<prod_user>
# DB_PASSWORD=<prod_password>
```

---

## Troubleshooting

### PostgreSQL not starting
```bash
# Check service status
brew services list | grep postgresql

# View logs
tail -f /opt/homebrew/var/log/postgresql@14.log

# Restart service
brew services restart postgresql@14
```

### Connection refused
```bash
# Check if PostgreSQL is listening
lsof -i :5432

# Check PostgreSQL config
cat /opt/homebrew/var/postgresql@14/postgresql.conf | grep listen_addresses
```

### Permission denied
```bash
# Check database ownership
/opt/homebrew/opt/postgresql@14/bin/psql -d postgres -c "\l"

# Grant permissions
/opt/homebrew/opt/postgresql@14/bin/psql -d job_scraper_dev -c "GRANT ALL PRIVILEGES ON DATABASE job_scraper_dev TO <username>;"
```

---

## Summary

✅ **Completed:**
1. PostgreSQL 14.20 installed via Homebrew
2. PostgreSQL service started and running
3. Database `job_scraper_dev` created
4. Python dependencies verified (SQLAlchemy, psycopg2, Alembic, asyncpg)
5. Database connection tested successfully

🎯 **Ready for:**
- Creating SQLAlchemy models
- Setting up Alembic migrations
- Implementing repository pattern
- Building business logic layer

---

## Quick Reference

**Database URL:**
```
postgresql://localhost:5432/job_scraper_dev
```

**Connect with psql:**
```bash
/opt/homebrew/opt/postgresql@14/bin/psql -d job_scraper_dev
```

**Python connection:**
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://localhost:5432/job_scraper_dev")
```

**Service management:**
```bash
brew services start postgresql@14
brew services stop postgresql@14
brew services restart postgresql@14
```

---

**Status: Phase 1 & 2 Complete! Ready to proceed with Phase 3: Implementation** 🚀

