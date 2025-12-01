# Database Integration - Planning Summary

## 📋 Overview

This document summarizes the planning for integrating PostgreSQL database into the job scraping platform. The system will track job positions, manage user alerts, and automatically notify users when relevant positions become available.

---

## 📚 Documentation Created

### 1. **PRD_Job_Scraping_Platform.md**
   - Product vision and goals
   - Core features and user stories
   - Success metrics
   - Timeline and phases
   - Risk assessment

### 2. **TECHNICAL_DESIGN.md**
   - System architecture
   - Complete database schema (6 tables)
   - SQLAlchemy model structure
   - Business logic design
   - Daily scraping workflow
   - Migration strategy

### 3. **IMPLEMENTATION_PLAN.md**
   - Step-by-step implementation guide
   - Code examples for all models
   - Alembic migration setup
   - Repository pattern implementation
   - Checklist for each phase

### 4. **Visual Diagrams**
   - System Architecture Diagram
   - Database ERD (Entity Relationship Diagram)
   - Daily Scraping Workflow Sequence Diagram

---

## 🗄️ Database Schema

### Tables Overview

| Table | Purpose | Key Fields |
|-------|---------|------------|
| **users** | User accounts | email, preferences |
| **companies** | Company information | name, careers_url, scraping_config |
| **job_positions** | Job listings | title, location, status, job_url |
| **alerts** | User alert rules | keywords, company_ids, locations |
| **user_job_applications** | Application tracking | user_id, job_position_id, status |
| **alert_notifications** | Notification log | alert_id, job_position_id, delivery_status |

### Key Relationships

```
users (1) ----< (many) alerts
users (1) ----< (many) user_job_applications
users (1) ----< (many) alert_notifications

companies (1) ----< (many) job_positions

job_positions (1) ----< (many) user_job_applications
job_positions (1) ----< (many) alert_notifications

alerts (1) ----< (many) alert_notifications
```

---

## 🔄 Core Workflows

### 1. Daily Scraping Workflow

```
1. Celery scheduler triggers daily task
2. For each active company:
   a. Run scraper → get job listings
   b. Compare with database:
      - New jobs → INSERT with status='active'
      - Existing jobs → UPDATE last_seen_at
      - Missing jobs → UPDATE status='expired'
   c. For new jobs:
      - Find matching user alerts
      - Send notifications
      - Log notifications
   d. Update company.last_scraped_at
3. Generate daily summary report
```

### 2. Alert Matching Logic

```python
# A position matches an alert if ALL of these are true:
- If alert.company_ids specified → position.company_id IN alert.company_ids
- If alert.keywords specified → ANY keyword in position.title
- If alert.excluded_keywords specified → NO keyword in position.title
- If alert.locations specified → position.location matches ANY location
- If alert.departments specified → position.department matches ANY department
- If alert.is_remote specified → position.is_remote == alert.is_remote
```

### 3. Position Lifecycle

```
NEW → ACTIVE → EXPIRED
  ↓      ↓         ↓
  |      |         └─> No longer on career page
  |      └─> Still on career page (update last_seen_at)
  └─> First time seen (create record)
```

---

## 🏗️ System Architecture

### Layers

1. **External Sources Layer**
   - Company career pages
   - ATS APIs (Greenhouse, Comeet, Workday)

2. **Scraping Layer**
   - Playwright scraper
   - API scrapers (Greenhouse, Comeet, etc.)

3. **Task Queue Layer**
   - Celery workers
   - Redis queue
   - Scheduled tasks

4. **Business Logic Layer**
   - Position Lifecycle Manager
   - Alert Matcher
   - Notification Service

5. **Data Access Layer**
   - SQLAlchemy ORM
   - Repository pattern

6. **Database Layer**
   - PostgreSQL (local + remote)

---

## 📦 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Database | PostgreSQL | 14+ |
| ORM | SQLAlchemy | 2.0.23 |
| Migrations | Alembic | 1.12.1 |
| DB Driver | psycopg2-binary | 2.9.9 |
| Async DB | asyncpg | 0.29.0 |
| Task Queue | Celery + Redis | (existing) |
| Web Scraping | Playwright | (existing) |

---

## 📅 Implementation Timeline

### Phase 1: Database Setup (Week 1)
- [ ] Install PostgreSQL locally
- [ ] Create database schema
- [ ] Set up Alembic migrations
- [ ] Create SQLAlchemy models
- [ ] Test CRUD operations

### Phase 2: Data Migration (Week 1-2)
- [ ] Migrate companies from YAML to DB
- [ ] Create repositories
- [ ] Update scrapers to use DB config
- [ ] Test scraping with DB

### Phase 3: Position Lifecycle (Week 2)
- [ ] Implement PositionLifecycleManager
- [ ] Integrate with scraping tasks
- [ ] Test new/expired detection
- [ ] Add monitoring

### Phase 4: User & Alert System (Week 3)
- [ ] Implement User/Alert models
- [ ] Create AlertMatcher engine
- [ ] Implement email notifications
- [ ] Test end-to-end flow

### Phase 5: Production Deployment (Week 4)
- [ ] Set up remote PostgreSQL
- [ ] Run production migrations
- [ ] Deploy workers
- [ ] Set up monitoring
- [ ] Create backup strategy

---

## 🎯 Key Features

### For Users
✅ **Personalized Alerts**: Set up alerts for specific companies, roles, and locations  
✅ **New Position Notifications**: Get notified immediately when matching jobs are posted  
✅ **Expiration Tracking**: Know when positions are removed (likely filled)  
✅ **Application Tracking**: Track which positions you've applied to  
✅ **Multi-company Monitoring**: Monitor 35+ tech companies simultaneously  

### For System
✅ **Automated Scraping**: Daily scraping of all active companies  
✅ **Smart Detection**: Automatically detect new and expired positions  
✅ **Reliable Notifications**: Email delivery with retry logic  
✅ **Audit Trail**: Complete history of all notifications sent  
✅ **Scalable Architecture**: Support for 1000+ users and 3000+ positions  

---

## 🔐 Security & Best Practices

### Database Security
- SSL/TLS connections
- Credential rotation
- Connection pooling
- Query optimization with indexes

### Data Privacy
- Minimal user data collection
- GDPR compliance ready
- Secure password hashing (if auth added)
- API rate limiting

### Scraping Ethics
- Respect robots.txt
- Rate limiting per company
- Appropriate user agents
- No server overload

---

## 📊 Success Metrics

### Technical Metrics
- **Scraping Success Rate**: >95%
- **Data Freshness**: <24 hours
- **System Uptime**: >99.5%
- **Alert Delivery Time**: <5 minutes

### User Metrics
- **Alert Accuracy**: >98% relevant
- **Position Detection**: >99% within 24h
- **Notification Delivery**: >99% success rate

---

## 🚀 Next Steps

### Immediate Actions
1. **Review** all planning documents
2. **Answer** open questions (database hosting, email service, etc.)
3. **Set up** local PostgreSQL
4. **Create** initial database schema
5. **Implement** SQLAlchemy models

### Questions to Answer
1. Where to host production database? (AWS RDS / Cloud SQL / DigitalOcean)
2. Which email service for notifications? (SendGrid / AWS SES / Mailgun)
3. Do we need user authentication in v1? (Yes/No)
4. Data retention policy for expired positions? (30/90 days / forever)
5. Alert frequency preference? (Immediate / Daily digest / Configurable)

---

## 📁 File Structure (After Implementation)

```
scrapper/
├── src/
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── job_position.py
│   │   ├── alert.py
│   │   ├── user_job_application.py
│   │   └── alert_notification.py
│   ├── repositories/              # Data access layer
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── company_repository.py
│   │   ├── job_position_repository.py
│   │   ├── user_repository.py
│   │   └── alert_repository.py
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── position_lifecycle_manager.py
│   │   ├── alert_matcher.py
│   │   └── notification_service.py
│   └── database/                  # Database utilities
│       ├── __init__.py
│       ├── connection.py
│       └── session.py
├── migrations/                    # Alembic migrations
│   └── versions/
├── config/
│   ├── database.py               # Database configuration
│   └── companies.yaml            # (will migrate to DB)
├── docs/                         # Documentation
│   ├── PRD_Job_Scraping_Platform.md
│   ├── TECHNICAL_DESIGN.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── DATABASE_INTEGRATION_SUMMARY.md
└── alembic.ini                   # Alembic config
```

---

## 💡 Design Decisions

### Why PostgreSQL?
- ✅ Robust ACID compliance
- ✅ Excellent JSON support (JSONB)
- ✅ Array data types for alert filters
- ✅ Full-text search capabilities
- ✅ Mature ecosystem and tooling

### Why SQLAlchemy?
- ✅ Industry-standard Python ORM
- ✅ Excellent migration support (Alembic)
- ✅ Type safety and IDE support
- ✅ Async support for scalability
- ✅ Repository pattern compatibility

### Why Repository Pattern?
- ✅ Separation of concerns
- ✅ Easier testing (mock repositories)
- ✅ Consistent data access interface
- ✅ Business logic isolation
- ✅ Future-proof for API layer

---

## 🎓 Learning Resources

### PostgreSQL
- [PostgreSQL Official Docs](https://www.postgresql.org/docs/)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)

### SQLAlchemy
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/tutorial.html)

### Alembic
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

---

## ✅ Planning Complete!

All planning documents have been created and are ready for review. The next step is to begin implementation starting with Phase 1: Database Setup.

**Ready to proceed?** Start with:
```bash
# Install PostgreSQL
brew install postgresql@14

# Create database
createdb job_scraper_dev

# Install Python dependencies
pip install sqlalchemy psycopg2-binary alembic asyncpg
```

