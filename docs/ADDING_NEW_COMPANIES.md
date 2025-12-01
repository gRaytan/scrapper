# Adding New Companies to the Scraper

**Last Updated:** December 1, 2025  
**Status:** Active

---

## 📋 Overview

This guide explains how to add new companies to the job scraper system. With the database integration, you must add companies to **both** the YAML configuration file **and** the PostgreSQL database.

---

## 🎯 Two-Step Process

### Step 1: Add to YAML Configuration
### Step 2: Add to PostgreSQL Database

**IMPORTANT:** Both steps are required! The YAML file is used for scraper configuration, while the database is used for runtime operations and job storage.

---

## 📝 Step 1: Add to YAML Configuration

### Location
`config/companies.yaml`

### Template

```yaml
- name: Company Name
  website: https://company.com
  careers_url: https://company.com/careers
  industry: Technology
  size: 1000-5000
  location: City, Country
  is_active: true
  scraping_frequency: 0 0 * * *
  location_filter:
    enabled: true
    countries:
    - Israel
    - United States
    match_keywords:
    - Israel
    - Tel Aviv
    - Herzliya
    - Remote
  scraping_config:
    scraper_type: api  # or 'playwright', 'static'
    pagination_type: none
    requires_js: false
    anti_bot_measures: false
    wait_time: 2
    api_endpoint: https://api.company.com/jobs
    api_method: GET
    selectors:
      job_list: null
      job_item: null
```

### Field Descriptions

#### Basic Information
- **name** (required): Company name - must be unique
- **website** (required): Company main website URL
- **careers_url** (required): URL to careers/jobs page
- **industry** (optional): Industry category (e.g., "Technology", "Finance", "Healthcare")
- **size** (optional): Company size (e.g., "1-50", "51-200", "1000-5000", "10000+")
- **location** (optional): Company headquarters location
- **is_active** (required): Set to `true` to enable scraping, `false` to disable
- **scraping_frequency** (optional): Cron expression for scraping schedule (default: "0 0 * * *" = daily at midnight)

#### Location Filter
- **enabled** (boolean): Enable/disable location filtering
- **countries** (list): List of countries to include (e.g., ["Israel", "United States"])
- **match_keywords** (list): Keywords to match in job location field

#### Scraping Configuration
- **scraper_type**: Type of scraper to use
  - `api`: For companies with public job APIs
  - `playwright`: For dynamic JavaScript-heavy pages
  - `static`: For simple HTML pages
- **pagination_type**: How pagination works
  - `none`: No pagination
  - `click`: Click "Load More" button
  - `scroll`: Infinite scroll
  - `url`: URL-based pagination
- **requires_js**: Whether page requires JavaScript
- **anti_bot_measures**: Whether site has anti-bot protection
- **wait_time**: Seconds to wait between requests
- **api_endpoint**: API URL (for `scraper_type: api`)
- **api_method**: HTTP method (GET, POST)
- **selectors**: CSS selectors for scraping (for `scraper_type: playwright`)

---

## 💾 Step 2: Add to PostgreSQL Database

### Option A: Run Migration Script (Recommended)

After adding the company to `companies.yaml`, run the migration script:

```bash
# From project root
.venv/bin/python scripts/migrate_companies_to_db.py
```

This script will:
- ✅ Read all companies from `companies.yaml`
- ✅ Create new companies in the database
- ✅ Update existing companies with new configuration
- ✅ Verify the migration was successful

### Option B: Manual Database Entry

If you need to add a company directly to the database without YAML:

```python
from src.storage.database import db
from src.storage.repositories.company_repo import CompanyRepository

with db.get_session() as session:
    company_repo = CompanyRepository(session)
    
    company_data = {
        "name": "Company Name",
        "website": "https://company.com",
        "careers_url": "https://company.com/careers",
        "industry": "Technology",
        "size": "1000-5000",
        "location": "Tel Aviv, Israel",
        "is_active": True,
        "scraping_frequency": "0 0 * * *",
        "scraping_config": {
            "scraper_type": "api",
            "api_endpoint": "https://api.company.com/jobs",
            # ... rest of config
        }
    }
    
    company = company_repo.create(company_data)
    print(f"Created company: {company.name} ({company.id})")
```

---

## 🔍 Common Scraper Types

### 1. API-Based Scrapers (Easiest)

**When to use:** Company has a public jobs API

**Examples:** Greenhouse, Lever, Comeet, SmartRecruiters

**Configuration:**
```yaml
scraping_config:
  scraper_type: api
  api_endpoint: https://api.greenhouse.io/v1/boards/company/jobs
  api_method: GET
  pagination_type: none
```

**Supported Platforms:**
- Greenhouse: `https://boards-api.greenhouse.io/v1/boards/{company}/jobs`
- Lever: `https://api.lever.co/v0/postings/{company}`
- Comeet: `https://www.comeet.co/careers-api/2.0/company/{id}/positions`
- SmartRecruiters: `https://api.smartrecruiters.com/v1/companies/{company}/postings`

### 2. Playwright Scrapers (Dynamic Pages)

**When to use:** Page requires JavaScript, has infinite scroll, or dynamic loading

**Examples:** Microsoft, Google, Apple

**Configuration:**
```yaml
scraping_config:
  scraper_type: playwright
  requires_js: true
  wait_time: 3
  wait_for_selector: div.job-card
  max_pages: 50
  selectors:
    job_list: div.jobs-list
    job_item: div.job-card
    job_title: h3.title
    job_location: span.location
    job_url: a[href*='/job/']
```

### 3. Static Scrapers (Simple HTML)

**When to use:** Simple HTML pages without JavaScript

**Configuration:**
```yaml
scraping_config:
  scraper_type: static
  requires_js: false
  wait_time: 1
  selectors:
    job_list: ul.careers
    job_item: li.job
```

---

## ✅ Verification Checklist

After adding a new company:

- [ ] Company added to `config/companies.yaml`
- [ ] Migration script run successfully
- [ ] Company appears in database (verify with query)
- [ ] Test scraping for the company
- [ ] Verify jobs are saved to database
- [ ] Check location filtering works correctly
- [ ] Confirm scraping session is created

### Verify Company in Database

```bash
# Connect to database
psql -d job_scraper_dev

# Check company exists
SELECT id, name, is_active, careers_url FROM companies WHERE name = 'Company Name';

# Exit
\q
```

### Test Scraping

```bash
# Test scraping for specific company
.venv/bin/python scripts/run_scraper.py --company "Company Name"

# Check logs
tail -f logs/scraper.log
```

---

## 🚨 Common Issues

### Issue 1: Company Not Found
**Error:** `Company {name} not found in configuration`

**Solution:** 
- Check company name matches exactly between YAML and database
- Run migration script again
- Verify YAML syntax is correct

### Issue 2: Scraping Fails
**Error:** Various scraping errors

**Solution:**
- Check `careers_url` is correct and accessible
- Verify `scraper_type` matches the page type
- Test selectors manually in browser DevTools
- Check if site has anti-bot measures

### Issue 3: No Jobs Found
**Error:** Scraping completes but 0 jobs found

**Solution:**
- Verify selectors are correct
- Check if location filter is too restrictive
- Test API endpoint manually (for API scrapers)
- Check if page structure has changed

---

## 📊 Example: Adding Stripe

### 1. Add to YAML

```yaml
- name: Stripe
  website: https://stripe.com
  careers_url: https://stripe.com/jobs
  industry: Fintech
  size: 5000-10000
  location: San Francisco, CA
  is_active: true
  scraping_frequency: 0 0 * * *
  location_filter:
    enabled: true
    countries:
    - United States
    - Israel
    match_keywords:
    - Remote
    - San Francisco
    - Tel Aviv
  scraping_config:
    scraper_type: api
    api_endpoint: https://boards-api.greenhouse.io/v1/boards/stripe/jobs
    api_method: GET
    pagination_type: none
```

### 2. Run Migration

```bash
.venv/bin/python scripts/migrate_companies_to_db.py
```

### 3. Test

```bash
.venv/bin/python scripts/run_scraper.py --company "Stripe"
```

---

## 📚 Additional Resources

- **Scraper Types:** See `src/scrapers/` for implementation details
- **Parser Types:** See `src/scrapers/parsers/` for supported platforms
- **Testing:** See `tests/test_company_scrapers.py` for examples
- **Recommended Companies:** See `docs/RECOMMENDED_COMPANIES_TO_ADD.md`

---

## 🎯 Next Steps

After adding companies:

1. **Monitor scraping performance** - Check logs and scraping sessions
2. **Verify job quality** - Review scraped jobs in database
3. **Adjust filters** - Fine-tune location and keyword filters
4. **Scale gradually** - Add 5-10 companies at a time
5. **Update documentation** - Keep this guide current

---

**Questions?** Check the main README or contact the development team.

