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
        days_back: int = 30,
        skip_linkedin: bool = False
    ) -> List[JobPosition]:
        """Get jobs that don't have descriptions.

        Args:
            limit: Maximum number of jobs to return
            company_id: Optional filter by company
            days_back: Only get jobs from the last N days
            skip_linkedin: If True, exclude LinkedIn URLs

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

        # Optionally skip LinkedIn URLs
        if skip_linkedin:
            query = query.filter(~JobPosition.job_url.contains("linkedin.com"))

        if company_id:
            query = query.filter(JobPosition.company_id == company_id)

        query = query.order_by(JobPosition.first_seen_at.desc()).limit(limit)

        return query.all()

    def _normalize_job_url(self, job_url: str) -> str:
        """Normalize job URL to fix known issues with stored URLs.

        Args:
            job_url: Original job URL from database

        Returns:
            Normalized URL that should work for fetching
        """
        # Fix Workday URLs: Add /External_Career_Site if missing
        # Old format: https://company.wd12.myworkdayjobs.com/job/Location/Title
        # New format: https://company.wd12.myworkdayjobs.com/External_Career_Site/job/Location/Title
        if "myworkdayjobs.com" in job_url and "/External_Career_Site/" not in job_url:
            # Insert External_Career_Site before /job/
            job_url = re.sub(
                r'(\.myworkdayjobs\.com)/job/',
                r'\1/External_Career_Site/job/',
                job_url
            )
            logger.debug(f"Normalized Workday URL: {job_url}")

        return job_url

    def fetch_job_description(self, job_url: str) -> Optional[str]:
        """Fetch job description from the job URL (synchronous).

        Args:
            job_url: URL of the job posting

        Returns:
            Job description text or None if failed
        """
        # Normalize URL to fix known issues
        normalized_url = self._normalize_job_url(job_url)

        try:
            headers = {
                "User-Agent": self.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(normalized_url, headers=headers)
                response.raise_for_status()

                html = response.text
                description = self._extract_description(html, normalized_url)
                return description

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching {normalized_url}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error fetching job description from {normalized_url}: {e}")
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

        # SmartRecruiters
        if "smartrecruiters.com" in job_url or "jobs.smartrecruiters" in job_url:
            return self._extract_smartrecruiters_description(soup)

        # Getro (job boards on getro.com or custom domains using Getro)
        if "getro.com" in job_url or "jobs.getro" in job_url:
            return self._extract_getro_description(soup)

        # Comeet
        if "comeet.com" in job_url or "comeet.co" in job_url:
            return self._extract_comeet_description(soup)

        # Jibe (used by many enterprises)
        if "jibe.com" in job_url or "jobs.jibe" in job_url:
            return self._extract_jibe_description(soup)

        # LinkedIn (public job pages)
        if "linkedin.com/jobs" in job_url:
            return self._extract_linkedin_description(soup)

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
        """Extract description from Eightfold job page.

        Eightfold pages are JavaScript-rendered, but they include job data
        as JSON-LD structured data in the page. We extract the description
        from the schema.org JobPosting object.
        """
        import json

        # First, try to find JSON-LD structured data (most reliable for Eightfold)
        # Look for script tags that might contain the JSON-LD data
        # Eightfold embeds it inline in the page, not in a proper script tag
        page_text = str(soup)

        # Look for the JobPosting JSON-LD pattern
        job_posting_pattern = r'"@type"\s*:\s*"JobPosting"'
        if re.search(job_posting_pattern, page_text):
            # Try to extract the JSON block containing JobPosting
            # Look for the description field
            desc_pattern = r'"@type"\s*:\s*"JobPosting"[^}]*"description"\s*:\s*"([^"]+)"'
            match = re.search(desc_pattern, page_text, re.DOTALL)
            if match:
                description = match.group(1)
                # Unescape JSON string
                description = description.replace('\\"', '"').replace('\\n', '\n').replace('\\t', ' ')
                if len(description) > 50:
                    return self._clean_text(description)

        # Fallback: Try HTML elements (for older Eightfold implementations)
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

    def _extract_smartrecruiters_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from SmartRecruiters job page."""
        # SmartRecruiters uses specific class for job description
        desc = soup.find("div", class_="job-description")
        if desc:
            return self._clean_text(desc.get_text())

        # Alternative: section with job-ad class
        desc = soup.find("section", class_="job-ad")
        if desc:
            return self._clean_text(desc.get_text())

        # Try RichText component (newer SmartRecruiters)
        desc = soup.find("div", class_="RichText")
        if desc:
            return self._clean_text(desc.get_text())

        # Try sectionBody (another variant)
        desc = soup.find("div", class_="sectionBody")
        if desc:
            return self._clean_text(desc.get_text())

        return None

    def _extract_getro_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from Getro job page."""
        # Getro uses job-description class
        desc = soup.find("div", class_="job-description")
        if desc:
            return self._clean_text(desc.get_text())

        # Alternative: content area
        desc = soup.find("div", class_="job-content")
        if desc:
            return self._clean_text(desc.get_text())

        # Try job-details section
        desc = soup.find("div", class_="job-details")
        if desc:
            return self._clean_text(desc.get_text())

        return None

    def _extract_comeet_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from Comeet job page."""
        # Comeet uses position-description
        desc = soup.find("div", class_="position-description")
        if desc:
            return self._clean_text(desc.get_text())

        # Alternative: job-description
        desc = soup.find("div", class_="job-description")
        if desc:
            return self._clean_text(desc.get_text())

        return None

    def _extract_jibe_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from Jibe job page."""
        desc = soup.find("div", class_="job-description")
        if desc:
            return self._clean_text(desc.get_text())

        # Jibe often uses jobDescription ID
        desc = soup.find("div", {"id": "jobDescription"})
        if desc:
            return self._clean_text(desc.get_text())

        return None

    def _extract_linkedin_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from LinkedIn public job page."""
        # LinkedIn uses show-more-less-html__markup for job descriptions
        desc = soup.find("div", class_="show-more-less-html__markup")
        if desc:
            return self._clean_text(desc.get_text())

        # Alternative: description__text
        desc = soup.find("div", class_="description__text")
        if desc:
            return self._clean_text(desc.get_text())

        # Try decorated-job-posting__details
        desc = soup.find("div", class_="decorated-job-posting__details")
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

    def _is_valid_description(self, description: str, job_url: str = "") -> bool:
        """Validate that the description is actual job content, not login walls or junk.

        Args:
            description: The extracted description text
            job_url: Original job URL for context

        Returns:
            True if the description appears to be valid job content
        """
        if not description:
            return False

        # Minimum length check
        if len(description) < 100:
            return False

        # LinkedIn login wall indicators (English and Hebrew)
        linkedin_junk_patterns = [
            "LinkedIn User Agreement",
            "Privacy Policy",
            "Cookie Policy",
            "Sign in",
            "Join now",
            "Join or sign in",
            "Agree & Join",
            "להגיש מועמדות",  # Hebrew: "Apply"
            "הצטרף",  # Hebrew: "Join"
            "להתחבר",  # Hebrew: "Sign in"
            "שכחת סיסמה",  # Hebrew: "Forgot password"
            "התחברות",  # Hebrew: "Login"
            "דוא\"ל או טלפון",  # Hebrew: "Email or phone"
            "סיסמה",  # Hebrew: "Password"
            "הסכם המשתמש",  # Hebrew: "User Agreement"
            "מדיניות הפרטיות",  # Hebrew: "Privacy Policy"
        ]

        # Count how many junk patterns are found
        junk_count = sum(1 for pattern in linkedin_junk_patterns if pattern in description)

        # If multiple junk patterns found, it's likely a login wall
        if junk_count >= 3:
            logger.warning(f"Description appears to be login wall junk (found {junk_count} patterns)")
            return False

        # Check for high ratio of non-ASCII characters (might be garbled text)
        non_ascii_count = sum(1 for c in description if ord(c) > 127)
        non_ascii_ratio = non_ascii_count / len(description) if description else 0

        # If more than 30% non-ASCII and contains login patterns, likely junk
        if non_ascii_ratio > 0.3 and junk_count >= 1:
            logger.warning(f"Description has high non-ASCII ratio ({non_ascii_ratio:.2%}) with login patterns")
            return False

        return True

    def _should_skip_url(self, job_url: str) -> bool:
        """Check if this URL should be skipped for enrichment.

        Args:
            job_url: The job URL to check

        Returns:
            True if the URL should be skipped
        """
        if not job_url:
            return True

        # Note: LinkedIn public job pages CAN be scraped, so we don't skip them
        # The extractor will handle extraction from public LinkedIn job pages

        return False

    def enrich_job(self, job: JobPosition) -> bool:
        """Enrich a single job with its description.

        Args:
            job: Job to enrich

        Returns:
            True if enrichment was successful
        """
        if not job.job_url:
            return False

        # Skip URLs that we know won't work
        if self._should_skip_url(job.job_url):
            logger.debug(f"Skipping URL that requires auth: {job.job_url}")
            return False

        description = self.fetch_job_description(job.job_url)

        # Validate the description is actual job content
        if description and self._is_valid_description(description, job.job_url):
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
        days_back: int = 30,
        skip_linkedin: bool = False
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

        # Optionally skip LinkedIn URLs
        if skip_linkedin:
            query = query.filter(~JobPosition.job_url.contains("linkedin.com"))

        if company_id:
            query = query.filter(JobPosition.company_id == company_id)

        return query.scalar() or 0
