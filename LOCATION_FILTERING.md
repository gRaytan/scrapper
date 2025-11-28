# Location Filtering Feature

## Overview

The scraper now supports location-based filtering to only scrape jobs from specific countries or regions. This is configured per company in the `companies.yaml` file.

## Configuration

Each company in `config/companies.yaml` now has a `location_filter` section:

```yaml
companies:
  - name: "Company Name"
    website: "https://example.com"
    careers_url: "https://careers.example.com"
    industry: "Technology"
    location_filter:
      enabled: true  # Set to false to disable filtering
      countries: ["Israel"]  # List of countries to filter for
      match_keywords: ["Israel", "Tel Aviv", "Herzliya", "Haifa", "Jerusalem", "IL"]
    scraping:
      # ... scraping configuration
```

### Configuration Fields

- **`enabled`** (boolean): Whether to enable location filtering for this company
  - `true`: Only jobs matching the filter will be scraped
  - `false`: All jobs will be scraped (no filtering)

- **`countries`** (list): List of country names for documentation purposes

- **`match_keywords`** (list): List of keywords to match against job locations
  - Case-insensitive matching
  - If any keyword is found in the job's location field, the job passes the filter
  - Examples: `["Israel", "Tel Aviv", "IL"]`

## How It Works

1. **Scraping**: Jobs are scraped normally from the company's careers page/API
2. **Filtering**: Each job's `location` field is checked against the `match_keywords`
3. **Statistics**: The scraper tracks:
   - `jobs_found`: Total jobs scraped before filtering
   - `jobs_filtered`: Number of jobs filtered out
   - Final result: Jobs that passed the filter

## Example Results

For Monday.com with Israel filter enabled:
- Total jobs found: 290
- Jobs filtered out: 170
- Jobs after filter: 120 (Israel-based positions only)

## Current Configuration

All companies are currently configured to filter for **Israel-based positions only**:

1. **Monday.com** - Israel filter enabled
2. **Microsoft** - Israel filter enabled
3. **Wiz** - Israel filter enabled
4. **Island** - Israel filter enabled
5. **EON** - Israel filter enabled
6. **Palo Alto Networks** - Israel filter enabled
7. **Amazon** - Israel filter enabled

## Extending to Other Countries

To filter for different countries, simply update the `location_filter` configuration:

### Example: Filter for US positions

```yaml
location_filter:
  enabled: true
  countries: ["United States"]
  match_keywords: ["United States", "US", "USA", "New York", "California", "Texas"]
```

### Example: Filter for multiple countries

```yaml
location_filter:
  enabled: true
  countries: ["Israel", "United States", "United Kingdom"]
  match_keywords: [
    "Israel", "Tel Aviv", "IL",
    "United States", "US", "USA", "New York",
    "United Kingdom", "UK", "London"
  ]
```

### Example: Disable filtering

```yaml
location_filter:
  enabled: false
  countries: []
  match_keywords: []
```

## Implementation Details

### Base Scraper

The `BaseScraper` class (`src/scrapers/base_scraper.py`) includes:

- **Initialization**: Reads `location_filter` from company config
- **`matches_location_filter(job)`**: Method to check if a job matches the filter
  - Returns `True` if filter is disabled or job matches
  - Returns `False` if job doesn't match filter criteria

### Playwright Scraper

The `PlaywrightScraper` class (`src/scrapers/playwright_scraper.py`) applies filtering in all scraping methods:

- `_scrape_api()` - For API-based scraping (Greenhouse, Comeet)
- `_scrape_html()` - For HTML scraping (Island)
- `_scrape_rss()` - For RSS feed scraping (Palo Alto Networks)
- `_scrape_api_with_pagination()` - For paginated API scraping (Amazon)

Each method:
1. Validates job data
2. Checks location filter
3. Only adds jobs that pass both validation and filter
4. Tracks filtered jobs in statistics

## Testing

To test location filtering, run the consolidated test suite:

```bash
python3 tests/test_company_scrapers.py
```

## Benefits

1. **Reduced Data Volume**: Only store relevant jobs for your target market
2. **Faster Processing**: Less data to process and store
3. **Better User Experience**: Users only see relevant positions
4. **Flexible**: Easy to change filter criteria per company
5. **Extensible**: Can easily add more countries or regions

## Future Enhancements

Potential improvements:
- Support for remote/hybrid filtering
- Support for city-level filtering
- Support for regex patterns in keywords
- Support for excluding certain locations
- Support for salary range filtering

