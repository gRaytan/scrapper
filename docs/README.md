# Job Notification System - Documentation

**Version:** 1.0  
**Last Updated:** November 20, 2025  
**Status:** Planning Phase

---

## 📚 Documentation Index

This directory contains comprehensive documentation for the Job Notification System project.

### Core Documents

#### 1. [PRD_JOB_NOTIFICATION_SYSTEM.md](./PRD_JOB_NOTIFICATION_SYSTEM.md)
**Product Requirements Document**

The complete product specification including:
- Executive summary and goals
- Current state analysis
- System architecture diagrams
- Database schema (existing + new tables)
- Functional requirements (scraping, users, alerts, notifications)
- Non-functional requirements (performance, scalability, security)
- API endpoints specification
- Success criteria and metrics
- Risk analysis and mitigation
- Future enhancements
- Cost estimates

**Read this first** to understand the full scope and requirements.

---

#### 2. [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)
**Detailed Implementation Plan**

Step-by-step implementation guide with:
- 8 implementation phases (12 weeks total)
- Specific tasks for each phase
- Code examples and file structures
- Database migration scripts
- Testing strategy
- Deployment checklist
- Acceptance criteria for each phase

**Use this** as your implementation guide when building the system.

---

#### 3. [QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md)
**Quick Reference Guide**

Quick overview including:
- System architecture summary
- Database schema summary
- Example workflows (creating alerts, sending notifications)
- Performance targets
- Development setup instructions
- Next steps

**Use this** for quick reference and onboarding new team members.

---

## 🎯 Project Overview

### What We're Building

A job scraping and notification platform that:

1. **Scrapes** 100+ company career pages daily using Playwright
2. **Stores** all job postings in PostgreSQL (Neon)
3. **Matches** new jobs against user-configured alerts
4. **Notifies** users via email when relevant jobs are posted

### Current Status

✅ **Completed:**
- 13 working company scrapers (Monday.com, Wiz, Island, EON, Palo Alto, Amazon, Meta, Nvidia, Wix, Salesforce, Datadog, Unity, AppsFlyer)
- Database models for companies, jobs, and scraping sessions
- Scraper orchestrator for managing scraping sessions
- FastAPI application skeleton
- Redis and Celery infrastructure

❌ **To Be Built:**
- User management and authentication
- Job alert configuration system
- Job matching engine
- Notification delivery system
- Daily scraping scheduler
- Email integration

---

## 🏗️ System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. Daily Scheduler (Celery Beat)                           │
│     Triggers at 2:00 AM UTC                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Scraping Workers (Celery)                               │
│     - Scrape 100+ companies in parallel                     │
│     - Detect new/updated/removed jobs                       │
│     - Store in PostgreSQL                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Job Matching Engine                                     │
│     - Get jobs created in last 24 hours                     │
│     - Match against all active alerts                       │
│     - Group matches by user                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Notification Service                                    │
│     - Create notification records                           │
│     - Batch by frequency (instant/daily/weekly)             │
│     - Send via email/push/webhook                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Users Receive Notifications                             │
│     - Email with matching jobs                              │
│     - Click to view/apply                                   │
│     - Track interactions                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema

### New Tables (To Be Implemented)

#### users
- User accounts and authentication
- Email, password, verification status
- Preferences and settings

#### job_alerts
- User-configured job alerts
- Filter criteria (companies, keywords, locations, etc.)
- Notification settings (frequency, channels)

#### notifications
- Notification history
- Delivery status per channel
- User interaction tracking (read, clicked)

#### user_job_interactions
- Track user actions (viewed, saved, applied, dismissed)
- Analytics and recommendations

### Existing Tables

#### companies
- Company information
- Scraping configuration
- Last scraped timestamp

#### job_positions
- Job postings with full details
- External ID for deduplication
- Active/inactive status

#### scraping_sessions
- Scraping run history
- Statistics (new, updated, removed jobs)
- Performance metrics

---

## 🚀 Implementation Timeline

### Phase 1: Database & Models (Week 1)
- Create new models (User, JobAlert, Notification)
- Write Alembic migrations
- Implement repository classes

### Phase 2: User Management (Week 2)
- User registration/login with JWT
- Password reset flow
- Email verification

### Phase 3: Alert Management (Week 3)
- CRUD API for job alerts
- Filter validation
- Alert preview/testing

### Phase 4: Job Matching (Week 4)
- Matching algorithm
- Database optimization
- Redis caching

### Phase 5: Notifications (Week 5-6)
- Email service integration (SendGrid)
- Email templates
- Notification batching

### Phase 6: Scheduler & Workers (Week 7)
- Celery configuration
- Daily scraping task
- Notification task

### Phase 7-8: API & Deployment (Week 8-12)
- Complete REST API
- Admin dashboard
- Production deployment

**Total Duration:** 12 weeks

---

## 📈 Success Metrics

### System Performance
- Daily scraping completion rate: **>95%**
- Job data freshness: **<24 hours**
- Database uptime: **>99.9%**
- Notification delivery rate: **>98%**

### User Engagement
- Alert open rate: **>40%**
- Alert click-through rate: **>15%**
- User retention (30-day): **>60%**
- Daily active users: **>1,000**

### Scale Targets
- **Users:** 10,000+
- **Active Jobs:** 100,000+
- **Active Alerts:** 50,000+
- **Daily Notifications:** 5,000-10,000

---

## 💰 Cost Estimates

### Monthly Operating Costs
- **Neon PostgreSQL:** $20-50 (Pro plan)
- **SendGrid Email:** $15-50 (40K-100K emails)
- **Redis:** $10-20 (managed service)
- **Hosting:** $50-100 (compute resources)

**Total:** $95-220/month

### Database Storage
- Users: ~10 MB
- Job Alerts: ~100 MB
- Jobs: ~1 GB
- Notifications: ~1 GB
- **Total:** ~2.5 GB (with indexes: ~5 GB)

---

## 🔧 Technology Stack

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.10+
- **ORM:** SQLAlchemy 2.0
- **Database:** PostgreSQL (Neon)
- **Task Queue:** Celery + Redis
- **Authentication:** JWT

### Scraping
- **Browser:** Playwright
- **HTTP:** httpx
- **Parsing:** BeautifulSoup4

### Notifications
- **Email:** SendGrid / AWS SES
- **Templates:** Jinja2
- **Push:** Firebase (future)

### Infrastructure
- **Caching:** Redis
- **Monitoring:** Sentry, Prometheus
- **Deployment:** Docker, AWS/GCP

---

## 📖 How to Use This Documentation

### For Product Managers
1. Read **PRD_JOB_NOTIFICATION_SYSTEM.md** for complete requirements
2. Review success metrics and timeline
3. Track progress against implementation phases

### For Engineers
1. Start with **QUICK_START_GUIDE.md** for overview
2. Follow **IMPLEMENTATION_ROADMAP.md** for step-by-step tasks
3. Reference **PRD** for detailed specifications
4. Check existing codebase in `/src` and `/tests`

### For New Team Members
1. Read **QUICK_START_GUIDE.md** first
2. Set up development environment
3. Review existing scrapers in `/src/scrapers`
4. Run tests to understand current functionality

---

## ✅ Next Steps

### Immediate Actions (This Week)
1. **Review all documentation** - Ensure team alignment
2. **Set up Neon database** - Create PostgreSQL instance
3. **Configure development environment** - Install dependencies
4. **Start Phase 1** - Begin database model implementation

### Week 1 Deliverables
- [ ] All new database models created
- [ ] Alembic migrations written and tested
- [ ] Repository classes implemented
- [ ] Unit tests passing (>80% coverage)
- [ ] Code review and merge to main

---

## 🤝 Contributing

### Code Standards
- Follow PEP 8 style guide
- Write docstrings for all functions
- Maintain >80% test coverage
- Use type hints

### Git Workflow
- Create feature branches from `main`
- Write descriptive commit messages
- Submit PRs for review
- Squash commits before merging

### Testing
- Write unit tests for all new code
- Run full test suite before committing
- Add integration tests for API endpoints
- Performance test critical paths

---

## 📞 Support

### Questions?
- Check documentation in `/docs`
- Review code examples in `/tests`
- Ask in team Slack channel

### Issues?
- Check logs in `/logs`
- Review Sentry error reports
- Run tests: `pytest -v`
- Check database migrations: `alembic current`

---

## 📝 Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-20 | Product Team | Initial PRD and implementation plan |

---

**Ready to start building?** 🚀

Begin with Phase 1 in the [Implementation Roadmap](./IMPLEMENTATION_ROADMAP.md)!

