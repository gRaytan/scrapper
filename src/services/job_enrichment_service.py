"""Job enrichment service for fetching missing job descriptions."""
import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from src.models.job_position import JobPosition
from src.models.company import Company
from src.utils.logger import logger


class JobEnrichmentService:
    """Service for enriching jobs with missing descriptions."""

    # User agent for requests
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Rate limiting
    REQUEST_DELAY = 1.0  # seconds between requests

    def __init__(self, db: Session):
        """Initialize the enrichment service.
        
        Args:
            db: Database session
        """
        self.db = db

    def get_jobs_without_description(
        self,
        limit: int = 100,
        company_id: Optional[UUID] = None,
        days_back: int = 30
    ) -> List[JobPosition]:
        """Get jobs that don't have descriptions.
        
        Args:
            limit: Maximum number of jobs to return
            company_id: Optional filter by company
            days_back: Only get jobs from the last N days
            
        Returns:
            List of jobs without descriptions
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        query = self.db.query(JobPosition).filter(
            and_(
                or_(
                    JobPosition.description.is_(None),
                    JobPosition.description == ""
                ),
                JobPosition.is_active == True,
                JobPosition.job_url.isnot(None),
                JobPosition.job_url != "",
                JobPosition.first_seen_at >= cutoff_date
            )
        )
        
        if company_id:
            query = query.filter(JobPosition.company_id == company_id)
        
        query = query.order_by(JobPosition.first_seen_at.desc()).limit(limit)
        
        return query.all()

    def fetch_job_description(self, job_url: str) -> Optional[str]:
        """Fetch job description from the job URL (synchronous).
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Job description text or None if failed
        """
        try:
            headers = {
                "User-Agent": self.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(job_url, headers=headers)
                response.raise_for_status()
                
                html = response.text
                description = self._extract_description(html, job_url)
                return description
                
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching {job_url}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error fetching job description from {job_url}: {e}")
            return None

    def _extract_description(self, html: str, job_url: str) -> Optional[str]:
        """Extract job description from HTML based on the job board type.
        
        Args:
            html: Raw HTML content
            job_url: URL to determine the job board type
            
        Returns:
            Extracted description text
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # Greenhouse
        if "greenhouse.io" in job_url or "boards.greenhouse.io" in job_url:
            return self._extract_greenhouse_description(soup)
        
        # Workday
        if "myworkdayjobs.com" in job_url or "workday.com" in job_url:
            return self._extract_workday_description(soup)
        
        # Eightfold
        if "eightfold.ai" in job_url:
            return self._extract_eightfold_description(soup)
        
        # Phenom
        if "phenom" in job_url.lower():
            return self._extract_phenom_description(soup)
        
        # Ashby
        if "ashbyhq.com" in job_url:
            return self._extract_ashby_description(soup)
        
        # Lever
        if "lever.co" in job_url:
            return self._extract_lever_description(soup)
        
        # Generic fallback
        return self._extract_generic_description(soup)

    def _extract_greenhouse_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from Greenhouse job page."""
        # Try content div
        content = soup.find("div", {"id": "content"})
        if content:
            return self._clean_text(content.get_text())
        
        # Try job description section
        desc = soup.find("div", class_="job-description")
        if desc:
            return self._clean_text(desc.get_text())
        
        return None

    def _extract_workday_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from Workday job page."""
        # Workday uses data-automation-id attributes
        desc = soup.find("div", {"data-automation-id": "jobPostingDescription"})
        if desc:
            return self._clean_text(desc.get_text())
        
        # Alternative selector
        desc = soup.find("div", class_="job-description")
        if desc:
            return self._clean_text(desc.get_text())
        
        return None

    def _extract_eightfold_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from Eightfold job page."""
        # Eightfold uses specific class names
        desc = soup.find("div", class_="position-job-description")
        if desc:
            return self._clean_text(desc.get_text())
        
        # Alternative
        desc = soup.find("div", {"id": "job-description"})
        if desc:
            return self._clean_text(desc.get_text())
        
        return None

    def _extract_phenom_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from Phenom job page."""
        desc = soup.find("div", class_="job-description")
        if desc:
            return self._clean_text(desc.get_text())
        
        # Alternative
        desc = soup.find("div", {"data-ph-id": "job-description"})
        if desc:
            return self._clean_text(desc.get_text())
        
        return None

    def _extract_ashby_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from Ashby job page."""
        desc = soup.find("div", class_="ashby-job-posting-description")
        if desc:
            return self._clean_text(desc.get_text())
        
        return None

    def _extract_lever_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from Lever job page."""
        desc = soup.find("div", class_="section-wrapper")
        if desc:
            return self._clean_text(desc.get_text())
        
        return None

    def _extract_generic_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Generic description extraction fallback."""
        # Try common class names
        for class_name in ["job-description", "description", "job-content", "posting-description"]:
            desc = soup.find("div", class_=class_name)
            if desc:
                return self._clean_text(desc.get_text())
        
        # Try common IDs
        for id_name in ["job-description", "description", "job-content"]:
            desc = soup.find("div", {"id": id_name})
            if desc:
                return self._clean_text(desc.get_text())
        
        # Try article or main content
        for tag in ["article", "main"]:
            content = soup.find(tag)
            if content:
                text = self._clean_text(content.get_text())
                if len(text) > 200:  # Only use if substantial content
                    return text
        
        return None

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    def enrich_job(self, job: JobPosition) -> bool:
        """Enrich a single job with its description.
        
        Args:
            job: Job to enrich
            
        Returns:
            True if enrichment was successful
        """
        if not job.job_url:
            return False
        
        description = self.fetch_job_description(job.job_url)
        
        if description and len(description) > 50:  # Minimum length check
            job.description = description
            self.db.commit()
            logger.info(f"Enriched job {job.id} with description ({len(description)} chars)")
            return True
        
        return False

    def enrich_jobs_batch(
        self,
        limit: int = 50,
        company_id: Optional[UUID] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Enrich a batch of jobs with missing descriptions.
        
        Args:
            limit: Maximum number of jobs to process
            company_id: Optional filter by company
            days_back: Only process jobs from the last N days
            
        Returns:
            Summary of enrichment results
        """
        import time
        
        jobs = self.get_jobs_without_description(
            limit=limit,
            company_id=company_id,
            days_back=days_back
        )
        
        logger.info(f"Found {len(jobs)} jobs without descriptions to enrich")
        
        enriched = 0
        failed = 0
        
        for job in jobs:
            try:
                success = self.enrich_job(job)
                if success:
                    enriched += 1
                else:
                    failed += 1
                
                # Rate limiting
                time.sleep(self.REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"Error enriching job {job.id}: {e}")
                failed += 1
        
        return {
            "total_processed": len(jobs),
            "enriched": enriched,
            "failed": failed,
            "remaining": self._count_jobs_without_description(company_id, days_back)
        }

    def _count_jobs_without_description(
        self,
        company_id: Optional[UUID] = None,
        days_back: int = 30
    ) -> int:
        """Count jobs without descriptions."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        query = self.db.query(func.count(JobPosition.id)).filter(
            and_(
                or_(
                    JobPosition.description.is_(None),
                    JobPosition.description == ""
                ),
                JobPosition.is_active == True,
                JobPosition.job_url.isnot(None),
                JobPosition.job_url != "",
                JobPosition.first_seen_at >= cutoff_date
            )
        )
        
        if company_id:
            query = query.filter(JobPosition.company_id == company_id)
        
        return query.scalar() or 0
