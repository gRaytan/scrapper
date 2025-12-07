# LinkedIn Job Positions Configuration

## Overview

The LinkedIn scraper searches for jobs across multiple job titles/positions. You can configure which positions to search for by editing the `.env.production` file.

## Configuration

### Environment Variables

Add these to your `.env.production` file:

```bash
# Comma-separated list of job titles to search
LINKEDIN_JOB_POSITIONS=Software Engineer,Backend Developer,Frontend Developer,...

# Location to search (default: Israel)
LINKEDIN_SEARCH_LOCATION=Israel

# Maximum pages per position (default: 10, ~25 jobs per page)
LINKEDIN_MAX_PAGES=10
```

## Currently Configured Positions (130+ roles)

### Software Engineering (30 positions)
- Software Engineer
- Backend Developer
- Frontend Developer
- Full Stack Developer
- Web Developer
- Python Developer
- Java Developer
- Node.js Developer
- Go Developer
- Rust Developer
- C++ Developer
- .NET Developer
- PHP Developer
- Ruby Developer
- Scala Developer
- Kotlin Developer
- Swift Developer
- TypeScript Developer
- JavaScript Developer
- React Developer
- iOS Developer
- Android Developer
- Mobile Developer
- Embedded Engineer
- Firmware Engineer
- Computer Graphics Engineer
- Rendering Engineer
- Game Developer
- Unity Developer
- Unreal Developer

### DevOps & Infrastructure (15 positions)
- DevOps Engineer
- Cloud Engineer
- Platform Engineer
- Infrastructure Engineer
- Site Reliability Engineer (SRE)
- Release Engineer
- Build Engineer
- Network Engineer
- Database Administrator (DBA)
- System Architect
- Solutions Architect
- Enterprise Architect
- Network Security Engineer
- SOC Analyst
- Security Operations (SecOps Engineer)

### Data & AI/ML (15 positions)
- Data Engineer
- Data Scientist
- Machine Learning Engineer
- AI Engineer
- Deep Learning Engineer
- Computer Vision Engineer
- NLP Engineer
- Research Scientist
- Applied Scientist
- Quantitative Analyst
- Business Intelligence Engineer
- Analytics Engineer
- ETL Developer
- Big Data Engineer
- Spark Developer

### Quality & Testing (5 positions)
- QA Engineer
- QA Automation Engineer
- Test Engineer
- Automation Engineer
- Performance Engineer

### Security & Compliance (20 positions)
- Security Engineer
- Cybersecurity Engineer
- Information Security Engineer
- Security Analyst
- Penetration Tester
- Ethical Hacker
- Security Architect
- CISO
- Compliance Engineer
- Risk Analyst
- Incident Response
- Threat Intelligence Analyst
- Malware Analyst
- Forensics Analyst
- Identity and Access Management (IAM Engineer)
- Application Security Engineer (AppSec Engineer)

### Product & Design (5 positions)
- Product Manager
- Technical Program Manager
- Product Owner
- UI/UX Designer
- Product Designer

### Leadership & Management (10 positions)
- Technical Lead
- Engineering Manager
- Team Lead
- Staff Engineer
- Principal Engineer
- Distinguished Engineer
- CTO
- VP Engineering
- Director of Engineering
- Head of Engineering

### Other Specialized Roles (30+ positions)
- Blockchain Developer
- Smart Contract Developer
- Kafka Developer
- AR/VR Developer
- Solutions Engineer
- Sales Engineer
- Customer Success Engineer
- Technical Support Engineer
- And many more...

## How to Customize

### Add New Positions

Edit `.env.production` and add your positions to the comma-separated list:

```bash
LINKEDIN_JOB_POSITIONS=Software Engineer,Your New Position,Another Position
```

### Remove Positions

Simply delete them from the comma-separated list.

### Change Search Location

```bash
LINKEDIN_SEARCH_LOCATION=United States
# or
LINKEDIN_SEARCH_LOCATION=Tel Aviv, Israel
```

### Adjust Scraping Depth

```bash
# Scrape more jobs per position (more pages)
LINKEDIN_MAX_PAGES=20

# Scrape fewer jobs per position (faster)
LINKEDIN_MAX_PAGES=5
```

## Usage

### Automatic Daily Scraping

The LinkedIn scraper runs automatically as part of the daily scraping job at 2:00 AM UTC.

### Manual Scraping

```python
# Scrape all configured positions
from src.workers.tasks import scrape_linkedin_jobs
scrape_linkedin_jobs.delay()

# Scrape specific position
scrape_linkedin_jobs.delay(keywords="Software Engineer", location="Israel")
```

## Performance Considerations

- **130 positions × 10 pages × 25 jobs/page = ~32,500 jobs** (maximum)
- **Scraping time**: ~2-3 minutes per position = **4-6 hours total**
- **Rate limiting**: 2 seconds between requests (respectful to LinkedIn)

### Recommendations

1. **For daily scraping**: Use all 130+ positions
2. **For testing**: Reduce to 5-10 positions or set `LINKEDIN_MAX_PAGES=2`
3. **For specific needs**: Create custom position lists

## Notes

- LinkedIn may block aggressive scraping - the 2-second delay helps prevent this
- Jobs are deduplicated by (company_name, title, location)
- LinkedIn jobs are attributed to actual companies, not "LinkedIn" as a company

