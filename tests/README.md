# Company Scraper Tests

This directory contains tests for all company scrapers in the project.

## Current Test Coverage

The consolidated test suite (`test_company_scrapers.py`) includes tests for **13 companies**:

1. **Monday.com** - Comeet API scraper (~279 jobs)
2. **Wiz** - Greenhouse API scraper (~115 jobs)
3. **Island** - HTML scraper with requests (~40 jobs)
4. **EON** - Greenhouse API scraper (~14 jobs)
5. **Palo Alto Networks** - RSS/XML feed scraper (~1,002 jobs)
6. **Amazon** - Custom JSON API scraper with offset pagination (~300 jobs)
7. **Meta** - GraphQL API scraper (~1,166 jobs)
8. **Nvidia** - Eightfold AI API scraper (~50 jobs)
9. **Wix** - SmartRecruiters API scraper (~125 jobs)
10. **Salesforce** - Workday API scraper (~40 jobs)
11. **Datadog** - Greenhouse API scraper (~425 jobs)
12. **Unity** - Greenhouse API scraper (~110 jobs)
13. **AppsFlyer** - Greenhouse API scraper (~26 jobs)

**Total**: ~3,692 jobs across all companies

## Running Tests

To run all company scraper tests:

```bash
python3 tests/test_company_scrapers.py
```

## Test Results Format

**CRITICAL**: Each test MUST store results in the exact format below:

```python
self.results['Company Name'] = {
    'success': True,  # or False - whether the test passed
    'jobs_count': len(jobs),  # Total number of jobs scraped
}
```

**Important Notes:**
- The key must be the exact company name (e.g., 'Monday.com', 'AppsFlyer')
- The dictionary MUST have both 'success' and 'jobs_count' keys
- Do NOT use a boolean directly - it must be a dictionary
- The results are used by `run_all_tests()` to generate the summary

## Adding a New Company Test

When adding a new company to the test suite, follow these steps:

### 1. Add the test method BEFORE `run_all_tests()` method

**CRITICAL**: The test method must be added **BEFORE** the `run_all_tests()` method, NOT after `main()`.

```python
async def test_new_company_scraper(self):
    """Test New Company scraper."""
    logger.info("=" * 80)
    logger.info("Testing New Company Scraper")
    logger.info("=" * 80)
    
    company_config = {
        "name": "New Company",
        "website": "https://www.newcompany.com",
        "careers_url": "https://careers.newcompany.com",
        "industry": "Technology"
    }
    
    scraping_config = {
        # Add scraping configuration here
    }
    
    scraper = PlaywrightScraper(company_config, scraping_config)
    
    try:
        await scraper.setup()
        jobs = await scraper.scrape()
        
        logger.success(f"New Company: Scraped {len(jobs)} jobs")
        
        # Show sample job
        if jobs:
            logger.info(f"Sample job: {jobs[0].get('title')} - {jobs[0].get('location')}")
        
        # CRITICAL: Use exact format below
        self.results['New Company'] = {
            'success': len(jobs) > 0,
            'jobs_count': len(jobs),
        }
        return len(jobs) > 0
        
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        self.results['New Company'] = {
            'success': False,
            'jobs_count': 0,
        }
        return False
        
    finally:
        await scraper.teardown()
```

### 2. Add a call to the new test in `run_all_tests()` method

```python
async def run_all_tests(self):
    """Run all company scraper tests."""
    logger.info("\n" + "=" * 80)
    logger.info("RUNNING ALL COMPANY SCRAPER TESTS")
    logger.info("=" * 80 + "\n")
    
    # Run all tests - ADD YOUR NEW TEST HERE
    await self.test_monday_scraper()
    await self.test_wiz_scraper()
    await self.test_island_scraper()
    await self.test_eon_scraper()
    await self.test_palo_alto_scraper()
    await self.test_amazon_scraper()
    await self.test_meta_scraper()
    await self.test_nvidia_scraper()
    await self.test_wix_scraper()
    await self.test_salesforce_scraper()
    await self.test_datadog_scraper()
    await self.test_unity_scraper()
    await self.test_appsflyer_scraper()
    await self.test_new_company_scraper()  # ADD YOUR NEW TEST HERE
    
    # Print summary (automatically includes all companies in self.results)
    logger.info("\n" + "=" * 80)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    total_jobs = 0
    for company, result in self.results.items():
        status = "✓ PASS" if result['success'] else "✗ FAIL"
        logger.info(f"{company:15} {status:10} - {result['jobs_count']} jobs")
        total_jobs += result['jobs_count']
    
    logger.info("=" * 80)
    logger.info(f"Total jobs scraped: {total_jobs}")
    
    # Check if all tests passed
    all_passed = all([result['success'] for result in self.results.values()])
    
    if all_passed:
        logger.success("\n✓ ALL TESTS PASSED")
        return True
    else:
        logger.error("\n✗ SOME TESTS FAILED")
        return False
```

### 3. Common Mistakes to Avoid

❌ **DON'T** add test method after `main()` function
✅ **DO** add test method as a class method before `run_all_tests()` method

❌ **DON'T** use different result format (e.g., boolean or dict with different keys)
✅ **DO** use exact format: `{'success': bool, 'jobs_count': int}`

❌ **DON'T** forget to add the test call in `run_all_tests()`
✅ **DO** add `await self.test_new_company_scraper()` in the test list

❌ **DON'T** manually update `all_passed` - it's now automatic
✅ **DO** just add your test call - the summary is generated from `self.results`

❌ **DON'T** forget to update this README
✅ **DO** update the company count and list in this README

## Scraper Types Supported

The test suite supports multiple scraper types and API platforms:

### 1. **API Scraper** (`scraper_type: "api"`)

Direct API calls without browser automation. Supports various pagination types:

#### Greenhouse API
- **Companies**: Wiz, EON, Datadog, Unity, AppsFlyer
- **Endpoint Pattern**: `https://boards-api.greenhouse.io/v1/boards/{company}/jobs`
- **Response Format**: `{"jobs": [...]}`
- **Pagination**: None (single request)

#### Comeet API
- **Companies**: Monday.com
- **Endpoint Pattern**: `https://www.comeet.com/careers-api/2.0/company/{company_id}/positions`
- **Response Format**: `{"positions": [...]}` or direct array
- **Pagination**: None (single request)

#### Amazon Custom API
- **Companies**: Amazon
- **Endpoint Pattern**: Custom Amazon jobs API
- **Response Format**: `{"jobs": [...], "hits": total}`
- **Pagination**: Offset-based (`offset` parameter)

#### Eightfold AI API
- **Companies**: Nvidia
- **Endpoint Pattern**: `https://nvidia.eightfold.ai/api/apply/v2/careers/search`
- **Response Format**: `{"status": 200, "data": {"positions": [...]}}`
- **Pagination**: Offset-based (`offset` parameter)
- **Special**: Requires `domain` parameter in query

#### SmartRecruiters API
- **Companies**: Wix
- **Endpoint Pattern**: `https://api.smartrecruiters.com/v1/companies/{company}/postings`
- **Response Format**: `{"content": [...], "totalFound": N, "offset": 0, "limit": 100}`
- **Pagination**: Offset-based (`offset` and `limit` parameters)

### 2. **GraphQL Scraper** (`scraper_type: "graphql"`)

Uses Playwright to intercept GraphQL API calls:

- **Companies**: Meta
- **How it works**: Navigates to careers page, intercepts GraphQL requests
- **Response Format**: `{"data": {"job_search_with_featured_jobs": {"all_jobs": [...]}}}`
- **Pagination**: Handled by GraphQL query

### 3. **Workday Scraper** (`scraper_type: "workday"`)

Specialized scraper for Workday ATS platform:

- **Companies**: Salesforce
- **Endpoint Pattern**: `https://{company}.wd1.myworkdayjobs.com/wday/cxs/{company}/{site}/jobs`
- **Method**: POST with JSON body
- **Response Format**: `{"total": N, "jobPostings": [...]}`
- **Pagination**: Offset-based (`offset` in POST body)

### 4. **RSS/XML Feed Scraper** (`scraper_type: "rss"`)

Parses RSS/XML job feeds:

- **Companies**: Palo Alto Networks
- **Platform**: TalentBrew
- **Response Format**: XML with `<item>` elements
- **Pagination**: None (single feed)

### 5. **HTML Scraper with Requests** (`scraper_type: "requests"`)

Simple HTTP requests with BeautifulSoup parsing:

- **Companies**: Island
- **Used for**: Sites that block Playwright but allow simple HTTP requests
- **Pagination**: Dynamic (loads more via JavaScript simulation)

## Notes

- All tests run sequentially to avoid rate limiting
- Each test returns a boolean (True/False) and stores detailed results in `self.results`
- The `run_all_tests()` method automatically generates a summary from all test results
- All scrapers output consistent data with 9 standard fields (see parser consistency tests)
