"""Getro job board parser (used by VC portfolio pages like Viola)."""
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
import json
import re
from loguru import logger

from .base_parser import BaseJobParser


class GetroParser(BaseJobParser):
    """Parser for Getro job board format (used by VC portfolio career pages).

    Getro uses an API for job data. Each job includes the actual
    company name in organization.name, making it ideal for VC portfolio pages.
    """

    # Known Getro collection IDs for VC portfolios
    COLLECTION_IDS = {
        "viola": 6263,
    }

    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job from Getro API format.

        Args:
            job_data: Job data from Getro API

        Returns:
            Standardized job dictionary with company name from organization
        """
        try:
            # Extract company name from organization
            organization = job_data.get("organization", {})
            company_name = organization.get("name", "")

            # Extract location (can be list or string)
            locations = job_data.get("locations", [])
            location = ", ".join(locations) if isinstance(locations, list) else str(locations)

            # Extract job URL
            job_url = job_data.get("url", "")

            # Parse posted date - API uses created_at (ISO string or timestamp)
            posted_date = None
            created_at = job_data.get("created_at") or job_data.get("createdAt")
            if created_at:
                try:
                    if isinstance(created_at, (int, float)):
                        posted_date = datetime.fromtimestamp(created_at)
                    elif isinstance(created_at, str):
                        # Try ISO format
                        posted_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except:
                    pass

            # Determine work mode / remote status
            work_mode = job_data.get("work_mode") or job_data.get("workMode", "")
            is_remote = work_mode.lower() == "remote" if work_mode else False

            # Extract seniority level
            seniority = job_data.get("seniority", "")

            # Extract industry tags from organization
            industry_tags = organization.get("industryTags", organization.get("industry_tags", []))
            industry = ", ".join(industry_tags) if industry_tags else ""

            return {
                "external_id": str(job_data.get("id", "")),
                "title": job_data.get("title", ""),
                "description": "",  # Not in list response
                "location": location,
                "job_url": job_url,
                "department": None,  # Not in Getro format
                "employment_type": None,
                "posted_date": posted_date,
                "is_remote": is_remote,
                "company": company_name,  # Important: actual company name
                "seniority": seniority,
                "industry": industry,
                "work_mode": work_mode,
            }
        except Exception as e:
            logger.error(f"Error parsing Getro job: {e}")
            return {}

    @staticmethod
    def get_collection_id_from_url(careers_url: str) -> Optional[int]:
        """Extract collection ID from Getro careers page.

        Args:
            careers_url: The careers page URL (e.g., https://careers.viola-group.com/jobs)

        Returns:
            Collection ID if found, None otherwise
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html',
            }

            response = httpx.get(careers_url, headers=headers, timeout=60.0, follow_redirects=True)
            response.raise_for_status()

            # Look for collection ID in API calls within the page
            # Pattern: /collections/XXXXX/
            pattern = r'/collections/(\d+)/'
            match = re.search(pattern, response.text)

            if match:
                collection_id = int(match.group(1))
                logger.info(f"Found Getro collection ID: {collection_id}")
                return collection_id

            logger.warning(f"Could not find collection ID in {careers_url}")
            return None

        except Exception as e:
            logger.error(f"Error getting collection ID from {careers_url}: {e}")
            return None

    @staticmethod
    def fetch_all_jobs_from_api(
        collection_id: int,
        origin_url: str = "https://careers.viola-group.com"
    ) -> List[Dict[str, Any]]:
        """Fetch all jobs from Getro API with pagination.

        Args:
            collection_id: The Getro collection ID
            origin_url: The origin URL for CORS headers

        Returns:
            List of all job dictionaries from the API
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': origin_url,
            'Referer': f'{origin_url}/jobs',
        }

        all_jobs = []
        page = 0
        per_page = 20  # Getro API caps at 20 per page

        api_url = f"https://api.getro.com/api/v2/collections/{collection_id}/search/jobs"

        while True:
            payload = {
                'hitsPerPage': per_page,
                'page': page,
                'filters': {'page': page},
                'query': ''
            }

            try:
                response = httpx.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()

                data = response.json()
                results = data.get('results', {})
                jobs = results.get('jobs', [])
                total = results.get('count', 0)

                if not jobs:
                    break

                all_jobs.extend(jobs)
                logger.debug(f"Getro API page {page}: {len(jobs)} jobs (total: {len(all_jobs)}/{total})")

                if len(all_jobs) >= total:
                    break

                page += 1

                # Safety limit
                if page > 100:
                    logger.warning("Reached page limit (100), stopping pagination")
                    break

            except httpx.HTTPStatusError as e:
                logger.error(f"Getro API error on page {page}: {e}")
                break
            except Exception as e:
                logger.error(f"Error fetching Getro jobs page {page}: {e}")
                break

        logger.info(f"Fetched {len(all_jobs)} total jobs from Getro API")
        return all_jobs

    @staticmethod
    def extract_jobs_from_html(html_content: str) -> List[Dict[str, Any]]:
        """Extract jobs from Getro page HTML (fallback method).

        Note: This only gets the first 20 jobs. Use fetch_all_jobs_from_api for all jobs.

        Args:
            html_content: Raw HTML from Getro job board page

        Returns:
            List of job dictionaries from __NEXT_DATA__
        """
        try:
            # Find __NEXT_DATA__ script tag
            pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
            match = re.search(pattern, html_content, re.DOTALL)

            if not match:
                logger.warning("Could not find __NEXT_DATA__ in Getro page")
                return []

            next_data = json.loads(match.group(1))

            # Navigate to jobs array
            jobs = (next_data
                    .get("props", {})
                    .get("pageProps", {})
                    .get("initialState", {})
                    .get("jobs", {})
                    .get("found", []))

            logger.info(f"Found {len(jobs)} jobs in Getro page (HTML method)")
            return jobs

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Getro __NEXT_DATA__ JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error extracting jobs from Getro HTML: {e}")
            return []

