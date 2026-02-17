# Career Scraper Architecture

## Overview

This document describes the architecture and design decisions for the career page scraper system.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Scraper Orchestrator                     │
│  (Task Queue, Scheduling, Rate Limiting, Retry Logic)       │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Scraper    │   │   Scraper    │   │   Scraper    │
│   Worker 1   │   │   Worker 2   │   │   Worker N   │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │      Page Analysis & Extraction       │
        │  ┌─────────────┐  ┌─────────────┐    │
        │  │  LLM Agent  │  │  Parsers    │    │
        │  │  (Smart)    │  │  (Rules)    │    │
        │  └─────────────┘  └─────────────┘    │
        └───────────────────────────────────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │         Data Pipeline                 │
        │  (Validation, Deduplication, Enrich)  │
        └───────────────────────────────────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │         Storage Layer                 │
        │  (PostgreSQL + Redis Cache)           │
        └───────────────────────────────────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │         API / Export Layer            │
        │  (REST API, CSV, JSON exports)        │
        └───────────────────────────────────────┘
```

## Components

### 1. Scrapers (`src/scrapers/`)

**Purpose**: Extract raw HTML and job data from career pages

**Types**:
- `StaticScraper`: For static pages (BeautifulSoup + httpx)
- `PlaywrightScraper`: For dynamic pages (Playwright)
- `SeleniumScraper`: Fallback option (Selenium)

**Strategies** (`src/scrapers/strategies/`):
- `pagination.py`: Handle button-based and URL parameter pagination
- `infinite_scroll.py`: Handle infinite scroll pages
- `dynamic_content.py`: Handle AJAX/lazy-loaded content

### 2. Parsers (`src/parsers/`)

**Purpose**: Extract structured data from HTML

**Types**:
- `RuleBasedParser`: CSS/XPath selectors (fast, cheap)
- `LLMParser`: AI-powered extraction (flexible, expensive)
- `HybridParser`: Combines both approaches

### 3. LLM Integration (`src/llm/`)

**Purpose**: Intelligent page analysis and data extraction

**Components**:
- `client.py`: LLM API wrapper
- `page_analyzer.py`: Analyze page structure
- `data_extractor.py`: Extract structured data
- `content_classifier.py`: Classify and categorize jobs

### 4. Storage (`src/storage/`)

**Purpose**: Persist and retrieve data

**Components**:
- `database.py`: PostgreSQL connection management
- `repositories/`: Data access layer
- `cache.py`: Redis caching

### 5. Pipeline (`src/pipeline/`)

**Purpose**: Process and clean scraped data

**Components**:
- `validator.py`: Validate data quality
- `deduplicator.py`: Remove duplicates
- `enricher.py`: Add additional information
- `normalizer.py`: Standardize formats

### 6. Orchestrator (`src/orchestrator/`)

**Purpose**: Manage scraping tasks and workers

**Components**:
- `scheduler.py`: Schedule recurring scrapes
- `queue_manager.py`: Manage task queue
- `worker.py`: Worker process implementation
- `rate_limiter.py`: Rate limiting logic

### 7. API (`src/api/`)

**Purpose**: Expose data via REST API

**Components**:
- `app.py`: FastAPI application
- `routes/`: API endpoints
- `schemas/`: Pydantic models

## Data Flow

1. **Scheduling**: Orchestrator schedules scraping tasks based on company configuration
2. **Queueing**: Tasks are added to Celery/Dramatiq queue
3. **Scraping**: Workers pick up tasks and scrape career pages
4. **Parsing**: Raw HTML is parsed into structured data
5. **Pipeline**: Data is validated, deduplicated, and enriched
6. **Storage**: Clean data is stored in PostgreSQL
7. **API**: Data is exposed via REST API

## Scraping Strategy Decision Tree

```
Start
  │
  ├─> Try Static Scraper (fastest)
  │     │
  │     ├─> Success? → Parse & Store
  │     │
  │     └─> Fail → Try Playwright
  │           │
  │           ├─> Success? → Parse & Store
  │           │
  │           └─> Fail → Enable Stealth Mode
  │                 │
  │                 ├─> Success? → Parse & Store
  │                 │
  │                 └─> Fail → Use LLM Analysis
  │                       │
  │                       ├─> Success? → Parse & Store
  │                       │
  │                       └─> Fail → Flag for Manual Review
```

## Database Schema

### Companies Table
- id (UUID, PK)
- name (String, Unique)
- website (String)
- careers_url (String)
- industry (String)
- size (String)
- location (String)
- scraping_config (JSON)
- scraping_frequency (String)
- last_scraped_at (Timestamp)
- is_active (Boolean)
- created_at (Timestamp)
- updated_at (Timestamp)

### Job Positions Table
- id (UUID, PK)
- company_id (UUID, FK)
- title (String)
- description (Text)
- location (String)
- remote_type (String)
- employment_type (String)
- department (String)
- seniority_level (String)
- salary_range (JSON)
- requirements (Array)
- benefits (Array)
- posted_date (Timestamp)
- application_url (String)
- job_url (String)
- is_active (Boolean)
- scraped_at (Timestamp)
- raw_html (Text)
- metadata (JSON)
- created_at (Timestamp)
- updated_at (Timestamp)

### Scraping Sessions Table
- id (UUID, PK)
- company_id (UUID, FK)
- status (String)
- started_at (Timestamp)
- completed_at (Timestamp)
- jobs_found (Integer)
- jobs_new (Integer)
- jobs_updated (Integer)
- jobs_removed (Integer)
- errors (JSON)
- performance_metrics (JSON)
- scraper_config_snapshot (JSON)
- created_at (Timestamp)
- updated_at (Timestamp)

## Configuration

### Company Configuration (`config/companies.yaml`)
- Company metadata
- Scraping configuration
- Selectors
- Pagination settings

### Scraping Rules (`config/scraping_rules.yaml`)
- Common selector patterns
- Text extraction patterns
- Rate limiting rules
- Validation rules
- LLM configuration

### Environment Variables (`.env`)
- Database credentials
- API keys
- Scraping parameters
- Feature flags

## Scalability Considerations

1. **Horizontal Scaling**: Multiple worker processes
2. **Database**: Connection pooling, read replicas
3. **Caching**: Redis for frequently accessed data
4. **Queue**: Distributed task queue
5. **Rate Limiting**: Per-domain rate limits
6. **Proxy Rotation**: Avoid IP bans

## Security

1. **API Keys**: Stored in environment variables
2. **Database**: Encrypted connections
3. **Proxies**: Authenticated proxies
4. **Rate Limiting**: Respect robots.txt
5. **Data Privacy**: Handle PII appropriately

## Monitoring

1. **Logging**: Structured logging with Loguru
2. **Metrics**: Prometheus metrics
3. **Errors**: Sentry error tracking
4. **Health Checks**: API health endpoints
5. **Alerts**: Notify on failures

## Future Enhancements

1. **Machine Learning**: Train models for better extraction
2. **Real-time Updates**: WebSocket notifications
3. **Advanced Analytics**: Job market insights
4. **Multi-language**: Support non-English pages
5. **Mobile Apps**: Native mobile applications

