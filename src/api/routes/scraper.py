"""Scraper API routes."""
from fastapi import APIRouter, HTTPException
from typing import Optional, List
import requests
from datetime import datetime

from src.scrapers.parsers.apple_parser import AppleParser
from src.utils.logger import logger

router = APIRouter()


@router.get("/scrape/apple")
async def scrape_apple(
    location: Optional[str] = "israel-ISR",
    background: bool = False
):
    """
    Scrape Apple jobs.
    
    Args:
        location: Location filter (default: israel-ISR)
        background: Run in background (default: False)
        
    Returns:
        Job listings from Apple
        
    Example:
        GET /api/v1/scraper/scrape/apple
        GET /api/v1/scraper/scrape/apple?location=israel-ISR
        GET /api/v1/scraper/scrape/apple?background=true
    """
    
    if background:
        # For background tasks, return immediately
        # In production, you'd use Celery or similar
        return {
            "status": "started",
            "message": "Apple scraping started in background (not implemented yet)",
            "location": location
        }
    
    # Run synchronously
    try:
        result = _scrape_apple_sync(location)
        return result
    except Exception as e:
        logger.error(f"Error scraping Apple: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/apple")
async def scrape_apple_post(
    location: Optional[str] = "israel-ISR",
    location_keywords: Optional[List[str]] = None
):
    """
    Scrape Apple jobs with POST request (for custom filters).
    
    Request body:
    {
        "location": "israel-ISR",
        "location_keywords": ["Israel", "Herzliya", "Tel Aviv", "Haifa"]
    }
    
    Returns:
        Job listings from Apple
    """
    try:
        result = _scrape_apple_sync(location, location_keywords)
        return result
    except Exception as e:
        logger.error(f"Error scraping Apple: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _scrape_apple_sync(location: str = "israel-ISR", location_keywords: Optional[List[str]] = None):
    """Synchronous Apple scraping function."""
    
    # Build URL
    url = f"https://jobs.apple.com/en-il/search?location={location}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    logger.info(f"Scraping Apple jobs from: {url}")
    
    # Fetch HTML
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    # Parse jobs
    parser = AppleParser()
    jobs = parser.parse(response.text)
    
    logger.info(f"Found {len(jobs)} jobs from Apple")
    
    # Apply location filter if provided
    if location_keywords:
        filtered_jobs = []
        for job in jobs:
            job_location = job.get('location', '')
            if any(keyword.lower() in job_location.lower() for keyword in location_keywords):
                filtered_jobs.append(job)
        jobs = filtered_jobs
        logger.info(f"After filtering: {len(jobs)} jobs")
    
    return {
        "status": "success",
        "company": "Apple",
        "location": location,
        "total_jobs": len(jobs),
        "scraped_at": datetime.utcnow().isoformat(),
        "jobs": jobs
    }


async def _scrape_apple_task(location: str):
    """Background task for scraping Apple jobs."""
    try:
        result = _scrape_apple_sync(location)
        logger.info(f"Background scraping completed: {result['total_jobs']} jobs")
    except Exception as e:
        logger.error(f"Background scraping failed: {e}")




@router.get("/scrape/microsoft")
async def scrape_microsoft(
    location: Optional[str] = "israel",
    query: Optional[str] = ""
):
    """
    Scrape Microsoft jobs.
    
    Args:
        location: Location filter (default: israel)
        query: Search query (default: empty)
        
    Returns:
        Job listings from Microsoft
        
    Example:
        GET /api/v1/scraper/scrape/microsoft
        GET /api/v1/scraper/scrape/microsoft?location=israel
        GET /api/v1/scraper/scrape/microsoft?location=united%20states&query=software
    """
    try:
        result = _scrape_microsoft_sync(location, query)
        return result
    except Exception as e:
        logger.error(f"Error scraping Microsoft: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _scrape_microsoft_sync(location: str = "israel", query: str = ""):
    """Synchronous Microsoft scraping function with pagination."""
    
    import json
    from src.scrapers.parsers.microsoft_parser import MicrosoftParser
    
    base_url = "https://apply.careers.microsoft.com/api/pcsx/search"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    logger.info(f"Scraping Microsoft jobs: location={location}, query={query}")
    
    all_jobs = []
    parser = MicrosoftParser()
    page = 0
    page_size = 10
    
    while True:
        params = {
            'domain': 'microsoft.com',
            'query': query,
            'location': location,
            'start': page * page_size
        }
        
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse jobs from this page
        jobs = parser.parse(response.text)
        
        if not jobs:
            break
        
        all_jobs.extend(jobs)
        logger.info(f"Found {len(jobs)} jobs on page {page + 1}")
        
        # Check if there are more pages
        data = json.loads(response.text)
        total_count = data.get('data', {}).get('count', 0)
        
        if len(all_jobs) >= total_count:
            break
        
        page += 1
        
        # Safety limit
        if page >= 20:
            logger.warning("Reached page limit (20)")
            break
    
    logger.info(f"Total Microsoft jobs found: {len(all_jobs)}")
    
    return {
        "status": "success",
        "company": "Microsoft",
        "location": location,
        "query": query,
        "total_jobs": len(all_jobs),
        "scraped_at": datetime.utcnow().isoformat(),
        "jobs": all_jobs
    }



@router.get("/scrape/google")
async def scrape_google(
    location: Optional[str] = "Israel"
):
    """
    Scrape Google jobs.
    
    Args:
        location: Location filter (default: Israel)
        
    Returns:
        Job listings from Google
        
    Example:
        GET /api/v1/scraper/scrape/google
        GET /api/v1/scraper/scrape/google?location=United%20States
    """
    try:
        result = _scrape_google_sync(location)
        return result
    except Exception as e:
        logger.error(f"Error scraping Google: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _scrape_google_sync(location: str = "Israel"):
    """Synchronous Google scraping function."""
    
    from src.scrapers.parsers.google_parser import GoogleParser
    
    # Build URL
    url = f"https://www.google.com/about/careers/applications/jobs/results/?location={location}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    logger.info(f"Scraping Google jobs from: {url}")
    
    # Fetch HTML
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    # Parse jobs
    parser = GoogleParser()
    jobs = parser.parse(response.text)
    
    logger.info(f"Total Google jobs found: {len(jobs)}")
    
    return {
        "status": "success",
        "company": "Google",
        "location": location,
        "total_jobs": len(jobs),
        "scraped_at": datetime.utcnow().isoformat(),
        "jobs": jobs
    }



@router.get("/scrape/intel")
async def scrape_intel(
    location: Optional[str] = "Israel",
    max_jobs: Optional[int] = 100
):
    """
    Scrape Intel jobs using Workday API.
    
    Args:
        location: Location filter (default: Israel)
        max_jobs: Maximum number of jobs to fetch (default: 100)
        
    Returns:
        Job listings from Intel
        
    Example:
        GET /api/v1/scraper/scrape/intel
        GET /api/v1/scraper/scrape/intel?location=United%20States&max_jobs=50
    """
    try:
        result = _scrape_intel_sync(location, max_jobs)
        return result
    except Exception as e:
        logger.error(f"Error scraping Intel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _scrape_intel_sync(location: str = "Israel", max_jobs: int = 100):
    """Synchronous Intel scraping function."""
    
    logger.info(f"Scraping Intel jobs for location: {location}")
    
    # Parse jobs
    parser = IntelParser()
    jobs = parser.parse(location=location, max_jobs=max_jobs)
    
    logger.info(f"Total Intel jobs found: {len(jobs)}")
    
    return {
        "status": "success",
        "company": "Intel",
        "location": location,
        "total_jobs": len(jobs),
        "scraped_at": datetime.utcnow().isoformat(),
        "jobs": jobs
    }



@router.get("/scrape/intel")
async def scrape_intel(
    location: Optional[str] = "Israel",
    max_jobs: Optional[int] = 100
):
    """
    Scrape Intel jobs using Workday API.
    
    Args:
        location: Location filter (default: Israel)
        max_jobs: Maximum number of jobs to fetch (default: 100)
        
    Returns:
        Job listings from Intel
        
    Example:
        GET /api/v1/scraper/scrape/intel
        GET /api/v1/scraper/scrape/intel?location=United%20States&max_jobs=50
    """
    try:
        result = _scrape_intel_sync(location, max_jobs)
        return result
    except Exception as e:
        logger.error(f"Error scraping Intel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _scrape_intel_sync(location: str = "Israel", max_jobs: int = 100):
    """Synchronous Intel scraping function using Workday API."""
    
    import yaml
    from src.scrapers.parsers.workday_parser import WorkdayParser
    from config.settings import settings
    
    # Load Intel configuration from companies.yaml
    config_path = settings.base_dir / "config" / "companies.yaml"
    with open(config_path, 'r') as f:
        companies_config = yaml.safe_load(f)
    
    # Find Intel config
    intel_config = None
    for company in companies_config['companies']:
        if company['name'] == 'Intel':
            intel_config = company
            break
    
    if not intel_config:
        logger.error("Intel not found in companies.yaml")
        return {
            "status": "error",
            "company": "Intel",
            "message": "Intel configuration not found",
            "total_jobs": 0,
            "jobs": []
        }
    
    # Get configuration values
    scraping_config = intel_config['scraping_config']
    api_url = scraping_config['api_endpoint']
    base_url = scraping_config['workday_config']['base_url']
    
    logger.info(f"Scraping Intel jobs for location: {location}")
    
    # Fetch jobs with pagination
    all_jobs = []
    offset = 0
    limit = 20
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    # Fetch first page to get total
    payload = {
        "limit": limit,
        "offset": 0,
        "searchText": ""
    }
    
    response = requests.post(api_url, json=payload, headers=headers, timeout=30)
    
    if response.status_code != 200:
        logger.error(f"Error fetching Intel jobs: {response.status_code}")
        return {
            "status": "error",
            "company": "Intel",
            "location": location,
            "total_jobs": 0,
            "scraped_at": datetime.utcnow().isoformat(),
            "jobs": []
        }
    
    data = response.json()
    total = data.get('total', 0)
    
    # Initialize Workday parser
    parser = WorkdayParser(base_url=base_url)
    
    # Fetch all pages up to max_jobs
    while offset < min(total, max_jobs):
        payload = {
            "limit": limit,
            "offset": offset,
            "searchText": ""
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            job_postings = data.get('jobPostings', [])
            
            # Parse each job
            for job_data in job_postings:
                parsed_job = parser.parse(job_data)
                if parsed_job:
                    all_jobs.append(parsed_job)
            
            offset += limit
        else:
            break
    
    # Filter by location if specified
    if location:
        location_lower = location.lower()
        filtered_jobs = [
            job for job in all_jobs 
            if location_lower in job.get('location', '').lower()
        ]
    else:
        filtered_jobs = all_jobs
    
    # Convert to API format
    api_jobs = []
    for job in filtered_jobs:
        api_jobs.append({
            'title': job.get('title', ''),
            'location': job.get('location', ''),
            'url': job.get('job_url', ''),
            'job_id': job.get('external_id', ''),
            'company': 'Intel',
            'department': job.get('department', ''),
        })
    
    logger.info(f"Total Intel jobs found: {len(api_jobs)}")
    
    return {
        "status": "success",
        "company": "Intel",
        "location": location,
        "total_jobs": len(api_jobs),
        "scraped_at": datetime.utcnow().isoformat(),
        "jobs": api_jobs
    }

@router.get("/scrape/companies")
async def list_available_companies():
    """
    List all available companies that can be scraped.
    
    Returns:
        List of company names and their scraping status
    """
    return {
        "companies": [
            {
                "name": "Apple",
                "endpoint": "/api/v1/scraper/scrape/apple",
                "status": "active",
                "method": "embedded_json",
                "locations": ["israel-ISR", "united-states-USA"]
            },
            {
                "name": "Microsoft",
                "endpoint": "/api/v1/scraper/scrape/microsoft",
                "status": "active",
                "method": "api",
                "locations": ["israel", "united states", "worldwide"]
            },
            {
                "name": "Google",
                "endpoint": "/api/v1/scraper/scrape/google",
                "status": "active",
                "method": "embedded_data",
                "locations": ["Israel", "United States", "worldwide"]
            },
            {
                "name": "Intel",
                "endpoint": "/api/v1/scraper/scrape/intel",
                "status": "active",
                "method": "workday_api",
                "locations": ["Israel", "United States", "worldwide"]
            },
            # Add more companies here as they're implemented
        ]
    }

