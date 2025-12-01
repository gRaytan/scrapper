# Product Requirements Document (PRD)
## Job Scraping & Alert Platform

### 1. Executive Summary

**Product Name**: Job Scraping & Alert Platform  
**Version**: 1.0  
**Date**: November 28, 2025  
**Owner**: Engineering Team

#### Vision
Build an automated job scraping and notification platform that monitors tech companies in Israel and the US, stores job positions in a PostgreSQL database, and alerts users when relevant positions matching their preferences become available.

#### Goals
- Automate daily job scraping from 35+ tech companies
- Store and track job positions with historical data
- Enable users to set up personalized job alerts based on role, company, and location preferences
- Detect new job postings and expired positions automatically
- Provide a reliable notification system for job seekers

---

### 2. Problem Statement

**Current Pain Points**:
- Job seekers must manually check multiple company career pages daily
- No centralized system to track job openings across companies
- Missing opportunities when new positions are posted
- No way to know when positions are removed/filled
- Difficult to track application history

**Target Users**:
- Job seekers in tech industry (Israel & US markets)
- Recruiters monitoring market trends
- Career advisors tracking opportunities

---

### 3. Core Features

#### 3.1 Job Scraping System
- **Daily automated scraping** of 35+ tech companies
- **Multi-platform support**: Greenhouse, Comeet, Workday, custom career pages
- **Intelligent detection** of new and expired positions
- **Data normalization** across different ATS platforms
- **Location filtering** (Israel, United States focus)

#### 3.2 Database Management
- **PostgreSQL database** for reliable data storage
- **Job position tracking** with historical data
- **Company management** with metadata
- **User management** with preferences
- **Alert configuration** per user

#### 3.3 User Alert System
- **Personalized alerts** based on:
  - Specific companies
  - Job roles/titles (keywords)
  - Locations
  - Departments
- **Alert delivery** via email/webhook
- **Alert history** tracking

#### 3.4 Position Lifecycle Management
- **New position detection**: Compare scraped jobs with DB
- **Expiration detection**: Mark positions no longer on career pages
- **Status tracking**: Active, Expired, Filled
- **Change detection**: Track updates to existing positions

---

### 4. User Stories

#### As a Job Seeker
- I want to receive alerts when new Data Engineer positions open at Google, Microsoft, or Meta in Israel
- I want to know when positions I'm tracking are removed (likely filled)
- I want to see all active positions at my target companies
- I want to track which positions I've applied to

#### As a System Administrator
- I want to monitor scraping success rates
- I want to add new companies to the scraping list
- I want to see database health metrics
- I want to manage user accounts

---

### 5. Success Metrics

#### Technical Metrics
- **Scraping Success Rate**: >95% of companies scraped successfully daily
- **Data Freshness**: All jobs updated within 24 hours
- **System Uptime**: >99.5%
- **Alert Delivery Time**: <5 minutes after new job detected

#### User Metrics
- **Alert Accuracy**: >98% relevant alerts (low false positives)
- **Position Detection Rate**: >99% of new positions detected within 24h
- **User Engagement**: Track alert open rates, click-through rates

---

### 6. Non-Functional Requirements

#### Performance
- Handle 3000+ job positions across 35+ companies
- Support 100+ concurrent users
- Process daily scraping within 2 hours

#### Reliability
- Automated retry logic for failed scrapes
- Database backups every 6 hours
- Graceful degradation if individual scrapers fail

#### Security
- Secure user authentication
- Encrypted database connections
- API rate limiting to prevent abuse
- No storage of sensitive user data

#### Scalability
- Easy addition of new companies
- Support for 1000+ users
- Horizontal scaling of Celery workers

---

### 7. Out of Scope (v1.0)

- Job application tracking/management
- Resume parsing or matching
- Salary data collection
- Company reviews or ratings
- Mobile applications
- Real-time notifications (push notifications)
- Machine learning for job recommendations
- Integration with LinkedIn/Indeed

---

### 8. Dependencies

#### Technical Dependencies
- PostgreSQL 14+
- Redis (for Celery)
- Playwright (for web scraping)
- Celery (for task scheduling)
- Python 3.9+

#### External Dependencies
- Company career pages availability
- ATS platform APIs (Greenhouse, Comeet, etc.)
- Email service provider (for alerts)

---

### 9. Timeline & Phases

#### Phase 1: Database & Core Infrastructure (Week 1-2)
- PostgreSQL setup (local + remote)
- Database schema design and migration
- Core models implementation
- Basic CRUD operations

#### Phase 2: Scraping Integration (Week 2-3)
- Integrate existing scrapers with database
- Implement position lifecycle management
- Add new/expired position detection
- Testing with existing 35 companies

#### Phase 3: User & Alert System (Week 3-4)
- User management implementation
- Alert configuration system
- Alert matching engine
- Email notification system

#### Phase 4: Testing & Optimization (Week 4-5)
- End-to-end testing
- Performance optimization
- Documentation
- Deployment to production

---

### 10. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Company websites block scrapers | High | Medium | Implement stealth mode, rotate user agents, add delays |
| Database performance issues | Medium | Low | Proper indexing, query optimization, connection pooling |
| High false positive alerts | High | Medium | Implement smart matching, user feedback loop |
| Scraper failures | Medium | High | Retry logic, monitoring, fallback mechanisms |
| Email delivery issues | Medium | Low | Use reliable email service, implement retry queue |

---

### 11. Open Questions

1. Should we support multiple alert delivery methods (email, Slack, webhook)?
2. How long should we retain expired job positions?
3. Should users be able to see historical data (e.g., "this position was posted 3 times in the last year")?
4. Do we need user authentication or can it be open access initially?
5. Should we track salary information if available?
6. What's the retention policy for user data?

---

### 12. Appendix

#### Current System State
- 35 companies configured
- ~2700 active job positions
- Playwright-based scraping infrastructure
- Celery workers for background tasks
- Redis for task queue
- No database persistence (currently)

#### Target Companies (Sample)
- FAANG: Google, Meta, Amazon, Microsoft, Apple
- Israeli Unicorns: Wiz, Monday.com, JFrog
- Security: Palo Alto Networks, SentinelOne, Check Point
- Others: Nvidia, Intel, Salesforce, Datadog, etc.

