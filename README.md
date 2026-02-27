# Career Page Scraper

A scalable Python-based web scraper for extracting job positions from 100+ company career pages with LLM-powered intelligent extraction.

## Features

- 🚀 **Multi-strategy scraping**: Handles pagination, infinite scroll, and dynamic content
- 🤖 **LLM Integration**: Intelligent page analysis and data extraction
- 📊 **Structured Data**: PostgreSQL storage with comprehensive job metadata
- ⚡ **Scalable**: Distributed task queue for concurrent scraping
- 🛡️ **Anti-bot Evasion**: Stealth mode, proxy rotation, and human-like behavior
- 🔄 **Adaptive**: Automatically adjusts to page structure changes
- 📈 **Monitoring**: Comprehensive logging and error tracking

## 📚 Documentation

**Start here:** [docs/TABLE_OF_CONTENTS.md](docs/TABLE_OF_CONTENTS.md)

Key docs:
- [EC2 Operations](docs/EC2_OPERATIONS.md) - Deployment & server management
- [API Usage](docs/API_USAGE.md) - API endpoints
- [Architecture](docs/ARCHITECTURE.md) - System design

## Architecture

```
Orchestrator → Workers → Scrapers → Parsers (Rule-based + LLM) → Pipeline → Storage
```

## Project Structure

```
scrapper/
├── config/          # Configuration files
├── src/             # Source code
│   ├── models/      # Data models
│   ├── scrapers/    # Scraping engines
│   ├── parsers/     # Data extraction
│   ├── llm/         # LLM integration
│   ├── storage/     # Database & cache
│   ├── pipeline/    # Data processing
│   ├── orchestrator/# Task management
│   ├── api/         # REST API
│   └── utils/       # Utilities
├── tests/           # Test suite
├── scripts/         # Entry points
└── data/            # Data storage
```

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Docker (optional)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd scrapper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python scripts/setup_db.py
```

### Usage

```bash
# Run scraper for all companies
python scripts/run_scraper.py

# Run scraper for specific company
python scripts/run_scraper.py --company "Company Name"

# Export data
python scripts/export_data.py --format csv --output data/exports/jobs.csv

# Start API server
uvicorn src.api.app:app --reload
```

## Configuration

### Adding New Companies

**IMPORTANT:** When adding new companies, you must add them to **both** the YAML configuration **and** the PostgreSQL database.

See the complete guide: **[docs/ADDING_NEW_COMPANIES.md](docs/ADDING_NEW_COMPANIES.md)**

Quick steps:
1. Add company to `config/companies.yaml`
2. Run migration script: `.venv/bin/python scripts/migrate_companies_to_db.py`
3. Test scraping: `.venv/bin/python scripts/run_scraper.py --company "Company Name"`

### Company Configuration (`config/companies.yaml`)

```yaml
companies:
  - name: "Example Corp"
    website: "https://example.com"
    careers_url: "https://example.com/careers"
    industry: "Technology"
    is_active: true
    scraper_type: "playwright"
    pagination_type: "infinite_scroll"
    location_filter:
      enabled: true
      countries: ["Israel", "United States"]
    selectors:
      job_list: ".careers-list"
      job_item: ".job-card"
```

### Environment Variables (`.env`)

```
DATABASE_URL=postgresql://user:password@localhost:5432/scrapper
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-api-key
LOG_LEVEL=INFO
```

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src

# Format code
black src/

# Lint
ruff check src/
```

## Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f scraper

# Stop services
docker-compose down
```

## Roadmap

- [x] Phase 1: Foundation
- [x] Phase 2: Core Scraping
- [ ] Phase 3: LLM Integration
- [ ] Phase 4: Orchestration
- [ ] Phase 5: Data Pipeline
- [ ] Phase 6: API & Interface
- [ ] Phase 7: Scaling & Optimization
- [ ] Phase 8: Production Ready

## License

MIT License

## Contributing

Contributions are welcome! Please read our contributing guidelines first.

