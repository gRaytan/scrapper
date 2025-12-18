"""
Orchestrator for managing scraping sessions and coordinating scrapers.
"""
import asyncio
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import yaml
from sqlalchemy.orm import Session

from config.settings import settings
from src.models.company import Company
from src.models.job_position import JobPosition
from src.models.scraping_session import ScrapingSession
from src.scrapers.playwright_scraper import PlaywrightScraper
from src.scrapers.static_scraper import StaticScraper
from src.storage.database import db
from src.storage.repositories.company_repo import CompanyRepository
from src.storage.repositories.job_repo import JobPositionRepository
from src.services.location_normalizer import location_filter, normalize_location
from src.utils.logger import logger


class ScraperOrchestrator:
    """Orchestrates scraping sessions for multiple companies."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.companies_config = self._load_companies_config()
    
    def _load_companies_config(self) -> dict:
        """Load companies configuration from YAML."""
        config_path = settings.base_dir / "config" / "companies.yaml"
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    
    async def scrape_company(
        self,
        company_name: str,
        session: Session,
        incremental: bool = False
    ) -> ScrapingSession:
        """
        Scrape a single company's career page.
        
        Args:
            company_name: Name of the company to scrape
            session: Database session
            incremental: If True, only fetch jobs from last 24 hours
            
        Returns:
            ScrapingSession instance
        """
        logger.info(f"Starting scrape for {company_name}")
        
        # Get company configuration
        company_config = self._get_company_config(company_name)
        if not company_config:
            raise ValueError(f"Company {company_name} not found in configuration")
        
        # Get or create company in database
        company_repo = CompanyRepository(session)
        company, created = company_repo.get_or_create(
            name=company_name,
            defaults={
                "website": company_config.get("website"),
                "careers_url": company_config.get("careers_url"),
                "industry": company_config.get("industry"),
                "size": company_config.get("size"),
                "location": company_config.get("location"),
                "scraping_config": company_config.get("scraping_config"),
            }
        )
        
        if created:
            logger.info(f"Created new company: {company_name}")
        
        # Create scraping session
        scraping_session = ScrapingSession(
            company_id=company.id,
            status="running",
            started_at=datetime.utcnow(),
        )
        session.add(scraping_session)
        session.commit()
        
        try:
            # Initialize scraper
            scraper = await self._create_scraper(company_config)
            await scraper.setup()
            
            # Scrape jobs
            scraped_jobs = await scraper.scrape()
            logger.info(f"Scraped {len(scraped_jobs)} jobs for {company_name}")
            
            # Process and store jobs
            job_repo = JobPositionRepository(session)
            stats = await self._process_jobs(
                company=company,
                scraped_jobs=scraped_jobs,
                job_repo=job_repo,
                session=session
            )
            
            # Update session
            scraping_session.status = "completed"
            scraping_session.completed_at = datetime.utcnow()
            scraping_session.jobs_found = stats["jobs_found"]
            scraping_session.jobs_new = stats["jobs_new"]
            scraping_session.jobs_updated = stats["jobs_updated"]
            scraping_session.jobs_removed = stats["jobs_removed"]
            scraping_session.performance_metrics = scraper.stats
            
            session.commit()
            logger.success(f"Scraping completed for {company_name}: {stats}")
            
            # Cleanup
            await scraper.teardown()
            
        except Exception as e:
            logger.error(f"Scraping failed for {company_name}: {e}")
            scraping_session.status = "failed"
            scraping_session.completed_at = datetime.utcnow()
            scraping_session.add_error("scraping_error", str(e))
            session.commit()
            raise
        
        return scraping_session
    
    async def _create_scraper(self, company_config: dict):
        """Create appropriate scraper based on configuration."""
        scraping_config = company_config.get("scraping_config", {})
        scraper_type = scraping_config.get("scraper_type", "static")

        # PlaywrightScraper handles most types with different parsers
        playwright_types = [
            "playwright",      # Dynamic content with browser automation
            "api",            # API-based (Comeet, Greenhouse, etc.)
            "rss",            # RSS feeds
            "workday",        # Workday ATS
            "meta_graphql",   # Meta GraphQL API
            "ashby_graphql",  # Ashby GraphQL API
            "jibe",           # Jibe ATS
            "eightfold",      # Eightfold ATS
            "phenom",         # Phenom ATS
            "requests",       # Simple HTTP requests (similar to API)
            "comeet",         # Comeet ATS
            "getro",          # Getro VC portfolio job boards
        ]

        if scraper_type in playwright_types:
            return PlaywrightScraper(company_config, scraping_config)
        elif scraper_type == "static":
            return StaticScraper(company_config, scraping_config)
        else:
            raise ValueError(f"Unknown scraper type: {scraper_type}")

    def _normalize_job_data(self, job_data: dict) -> dict:
        """Normalize job data from parsers to match JobPosition model."""
        normalized = job_data.copy()

        # Map is_remote to remote_type
        if "is_remote" in normalized:
            is_remote = normalized.pop("is_remote")
            if is_remote and "remote_type" not in normalized:
                normalized["remote_type"] = "remote"
            elif not is_remote and "remote_type" not in normalized:
                normalized["remote_type"] = "onsite"

        # Ensure required timestamp fields
        now = datetime.utcnow()
        if "scraped_at" not in normalized:
            normalized["scraped_at"] = now
        if "first_seen_at" not in normalized:
            normalized["first_seen_at"] = now
        if "last_seen_at" not in normalized:
            normalized["last_seen_at"] = now

        return normalized

    async def _process_jobs(
        self,
        company: Company,
        scraped_jobs: List[dict],
        job_repo: JobPositionRepository,
        session: Session
    ) -> dict:
        """
        Process scraped jobs and update database.
        
        Returns:
            Dictionary with statistics (jobs_found, jobs_new, jobs_updated, jobs_removed)
        """
        stats = {
            "jobs_found": len(scraped_jobs),
            "jobs_new": 0,
            "jobs_updated": 0,
            "jobs_removed": 0,
            "jobs_filtered_location": 0,
        }

        # Filter jobs by location before processing
        allowed_jobs, filtered_jobs = location_filter.filter_jobs(scraped_jobs)
        stats["jobs_filtered_location"] = len(filtered_jobs)

        if filtered_jobs:
            logger.info(f"Filtered out {len(filtered_jobs)} jobs due to location restrictions")

        # Get current external IDs from scrape (only from allowed jobs)
        current_external_ids = [job.get("external_id") for job in allowed_jobs if job.get("external_id")]

        # Process each allowed job
        for job_data in allowed_jobs:
            # Normalize job data to match model
            job_data = self._normalize_job_data(job_data)

            external_id = job_data.get("external_id")
            if not external_id:
                logger.warning(f"Job missing external_id: {job_data.get('title')}")
                continue

            # Check if job exists
            existing_job = job_repo.get_by_external_id(external_id, company.id)
            
            if existing_job:
                # Update existing job
                updated = False
                for key, value in job_data.items():
                    if key not in ["external_id", "company_id"] and hasattr(existing_job, key):
                        if key == "location":
                            # Normalize location
                            normalized_loc = normalize_location(value)
                            if existing_job.location != normalized_loc:
                                existing_job.location = normalized_loc
                                updated = True
                        elif getattr(existing_job, key) != value:
                            setattr(existing_job, key, value)
                            updated = True

                if updated:
                    existing_job.is_active = True  # Reactivate if was inactive
                    stats["jobs_updated"] += 1
                    logger.debug(f"Updated job: {existing_job.title}")
            else:
                # Create new job - normalize location
                job_data["company_id"] = company.id
                job_data["is_active"] = True
                if "location" in job_data:
                    job_data["location"] = normalize_location(job_data["location"])
                job_repo.create(job_data)
                stats["jobs_new"] += 1
                logger.debug(f"Created new job: {job_data.get('title')}")
        
        # Deactivate jobs that are no longer in the scrape
        stats["jobs_removed"] = job_repo.deactivate_missing_jobs(
            company.id,
            current_external_ids
        )
        
        session.commit()
        return stats
    
    def _get_company_config(self, company_name: str) -> Optional[dict]:
        """Get configuration for a specific company."""
        companies = self.companies_config.get("companies", [])
        for company in companies:
            if company.get("name") == company_name:
                return company
        return None
    
    async def scrape_all_companies(self, incremental: bool = False):
        """
        Scrape all active companies.

        Args:
            incremental: If True, only fetch jobs from last 24 hours

        Returns:
            Dictionary mapping company names to scraping results
        """
        companies = self.companies_config.get("companies", [])
        active_companies = [c for c in companies if c.get("is_active", True)]

        logger.info(f"Scraping {len(active_companies)} companies")

        results = {}

        for company_config in active_companies:
            company_name = company_config.get("name")
            try:
                with db.get_session() as session:
                    scraping_session = await self.scrape_company(company_name, session, incremental)

                    # Extract data while session is still active
                    results[company_name] = {
                        'status': 'success',
                        'session_id': str(scraping_session.id),
                        'jobs_found': scraping_session.jobs_found,
                        'jobs_new': scraping_session.jobs_new,
                        'jobs_updated': scraping_session.jobs_updated,
                        'jobs_removed': scraping_session.jobs_removed,
                    }
            except Exception as e:
                logger.error(f"Failed to scrape {company_name}: {e}")
                results[company_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                continue

        logger.success("All companies scraped")
        return results


async def run_scraper(company_name: Optional[str] = None, incremental: bool = False):
    """
    Run the scraper.
    
    Args:
        company_name: Specific company to scrape (None = all companies)
        incremental: If True, only fetch jobs from last 24 hours
    """
    orchestrator = ScraperOrchestrator()
    
    if company_name:
        with db.get_session() as session:
            await orchestrator.scrape_company(company_name, session, incremental)
    else:
        await orchestrator.scrape_all_companies(incremental)

