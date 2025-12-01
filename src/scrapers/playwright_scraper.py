"""Playwright-based scraper implementation."""
import asyncio
import hashlib
import xml.etree.ElementTree as ET
import httpx
import requests
import os

from datetime import datetime
from dateutil import parser as date_parser
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page

from .base_scraper import BaseScraper
from .parsers import ComeetParser, GreenhouseParser, AmazonParser, EightfoldParser, SmartRecruitersParser, RSSParser, MetaParser, SalesforceParser, JibeParser, PhenomParser
from src.utils.logger import logger
from urllib.parse import urljoin, urlparse



class PlaywrightScraper(BaseScraper):
    """Scraper using Playwright for dynamic content."""
    
    def __init__(self, company_config: Dict[str, Any], scraping_config: Dict[str, Any], **kwargs):
        """Initialize PlaywrightScraper with lazy parser loading.
        
        Args:
            company_config: Company configuration dictionary
            scraping_config: Scraping configuration dictionary
            **kwargs: Additional keyword arguments
        """
        super().__init__(company_config, scraping_config, **kwargs)
        
        # Browser instances
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright: Optional[Any] = None
        
        # Lazy-loaded parsers (instantiated only when needed)
        self._parsers: Dict[str, Any] = {}
        self._parser_classes = {
            'comeet': ComeetParser,
            'greenhouse': GreenhouseParser,
            'amazon': AmazonParser,
            'eightfold': EightfoldParser,
            'smartrecruiters': SmartRecruitersParser,
            'rss': RSSParser,
            'meta': MetaParser,
            'salesforce': SalesforceParser,
            'jibe': JibeParser,
            'phenom': PhenomParser,
        }
    
    def _get_parser(self, parser_name: str) -> Any:
        """Get or create a parser instance lazily.
        
        Args:
            parser_name: Name of the parser to retrieve
            
        Returns:
            Parser instance
            
        Raises:
            ValueError: If parser_name is not recognized
        """
        if parser_name not in self._parsers:
            if parser_name not in self._parser_classes:
                raise ValueError(f"Unknown parser: {parser_name}")
            self._parsers[parser_name] = self._parser_classes[parser_name]()
        return self._parsers[parser_name]
    
    async def setup(self):
        """Initialize Playwright browser."""
        logger.info("Setting up Playwright browser")
        self.playwright = await async_playwright().start()
        
        # Launch browser with stealth options
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        # Create context with realistic settings
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        )
        
        self.page = await context.new_page()
        logger.success("Playwright browser ready")
    
    async def teardown(self):
        """Close Playwright browser."""
        logger.info("Closing Playwright browser")
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Main scraping method that routes to appropriate scraper based on configuration.

        Returns:
            List of job dictionaries

        Raises:
            ValueError: If scraper_type is not supported
            Exception: If scraping fails
        """
        try:
            scraper_type = self.scraping_config.get("scraper_type", "playwright")

            # Route to appropriate scraper method
            jobs = await self._route_to_scraper(scraper_type)

            # Update stats and log success
            self.stats["jobs_found"] = len(jobs)
            logger.success(f"Scraped {len(jobs)} jobs using {scraper_type} scraper")

            return jobs

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            self.stats["errors"] += 1
            raise

    async def _route_to_scraper(self, scraper_type: str) -> List[Dict[str, Any]]:
        """Route to the appropriate scraper method based on type.

        Args:
            scraper_type: Type of scraper to use

        Returns:
            List of job dictionaries

        Raises:
            ValueError: If scraper_type is not supported
        """
        # Scraper type to method mapping
        scraper_methods = {
            'meta_graphql': self._scrape_meta_graphql,
            'requests': self._scrape_html,
            'rss': self._scrape_rss,
            'workday': self._scrape_workday,
            'phenom': self._scrape_phenom,
            'api': self._get_api_scraper_method,
            'playwright': self._get_playwright_scraper_method,
        }

        if scraper_type not in scraper_methods:
            raise ValueError(f"Unsupported scraper_type: {scraper_type}")

        scraper_method = scraper_methods[scraper_type]
        return await scraper_method()

    async def _get_api_scraper_method(self) -> List[Dict[str, Any]]:
        """Get the appropriate API scraper method based on pagination type.

        Returns:
            List of job dictionaries
        """
        pagination_type = self.scraping_config.get("pagination_type", "offset")

        if pagination_type == "none":
            return await self._scrape_api()
        else:
            return await self._scrape_api_with_pagination()

    async def _get_playwright_scraper_method(self) -> List[Dict[str, Any]]:
        """Get the appropriate Playwright scraper method.

        Returns:
            List of job dictionaries
        """
        return await self._scrape_playwright_page()

    async def _scrape_api(self) -> List[Dict[str, Any]]:
        """Scrape jobs from API endpoint.
        
        Returns:
            List of job dictionaries
            
        Raises:
            ValueError: If api_endpoint is not configured
            httpx.HTTPError: If API request fails
        """
        api_endpoint = self.scraping_config.get("api_endpoint")
        if not api_endpoint:
            raise ValueError("api_endpoint is required for API scraping")
        
        api_params = self.scraping_config.get("api_params", {})
        timeout = self.scraping_config.get("timeout", 30.0)
        
        logger.info(f"Fetching jobs from API: {api_endpoint}")
        logger.debug(f"API params: {api_params}")
        
        try:
            # Fetch data from API
            data = await self._fetch_api_data(api_endpoint, api_params, timeout)
            
            # Detect format and get parser
            api_format = self._detect_api_format(data)
            parser = self._get_parser(api_format)
            
            # Extract positions from response
            positions = self._extract_positions_from_response(data, api_format)
            
            # Parse and filter jobs
            jobs = await self._parse_and_filter_jobs(positions, parser)
            
            self.stats["requests_made"] += 1
            return jobs
            
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {e}")
            self.stats["requests_made"] += 1
            raise
        except Exception as e:
            logger.error(f"Error scraping API: {e}")
            self.stats["requests_made"] += 1
            raise

    async def _fetch_api_data(self, endpoint: str, params: Dict[str, Any], timeout: float) -> Any:
        """Fetch data from API endpoint.
        
        Args:
            endpoint: API endpoint URL
            params: Query parameters
            timeout: Request timeout in seconds
            
        Returns:
            Parsed JSON response
            
        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(endpoint, params=params)
            logger.info(f"API Response Status: {response.status_code}")
            response.raise_for_status()
            return response.json()

    def _detect_api_format(self, data: Any) -> str:
        """Detect API format from response structure.
        
        Args:
            data: API response data
            
        Returns:
            API format name ('jibe', 'greenhouse', 'comeet')
            
        Raises:
            ValueError: If format cannot be detected
        """
        # Check if format is explicitly configured
        configured_format = self.scraping_config.get("api_format")
        if configured_format:
            logger.info(f"Using configured API format: {configured_format}")
            return configured_format
        
        # Auto-detect format based on structure
        if isinstance(data, dict) and "jobs" in data:
            sample_job = data["jobs"][0] if data["jobs"] else {}
            if isinstance(sample_job, dict) and "data" in sample_job:
                logger.info("Auto-detected Jibe API format")
                return 'jibe'
            else:
                logger.info("Auto-detected Greenhouse API format")
                return 'greenhouse'
        elif isinstance(data, list):
            logger.info("Auto-detected Comeet API format (list)")
            return 'comeet'
        elif isinstance(data, dict) and "positions" in data:
            logger.info("Auto-detected Comeet API format (dict)")
            return 'comeet'
        else:
            logger.error(f"Unknown API format. Type: {type(data)}")
            if isinstance(data, dict):
                logger.error(f"Response keys: {list(data.keys())}")
            raise ValueError(f"Unsupported API response format: {type(data)}")

    def _get_api_parser_for_pagination(self) -> Any:
        """
        Determine which parser to use for paginated API responses.

        This is used by _scrape_api_with_pagination() for APIs that use
        company-specific formats (Amazon, Nvidia, Wix) or standard formats.

        Returns:
            Parser instance
        """
        company_name = self.company_config.get("name", "")
        api_endpoint = self.scraping_config.get("api_endpoint", "")
        api_type = self.scraping_config.get("api_type", "")
        jobs_key = self.scraping_config.get("response_structure", {}).get("jobs_key", "jobs")
        field_mapping = self.scraping_config.get("field_mapping", {})

        # Check for generic API parser with field mapping
        if api_type == "generic" and field_mapping:
            logger.debug(f"Using generic API parser with field mapping for {company_name}")
            from .parsers.api_parser import APIParser
            url_template = self.scraping_config.get("url_template")
            return APIParser(field_mapping=field_mapping, url_template=url_template)

        # Company-specific parsers
        if company_name == "Nvidia":
            logger.debug("Using Eightfold parser for Nvidia")
            return self._get_parser('eightfold')
        elif company_name == "Wix":
            logger.debug("Using SmartRecruiters parser for Wix")
            return self._get_parser('smartrecruiters')
        elif company_name == "Amazon":
            logger.debug("Using Amazon parser")
            return self._get_parser('amazon')
        elif jobs_key == "jobs" or "greenhouse" in api_endpoint.lower():
            # Greenhouse API format
            logger.debug("Using Greenhouse parser")
            return self._get_parser('greenhouse')
        else:
            logger.warning(f"No parser defined for company: {company_name}, using greenhouse as fallback")
            return self._get_parser('greenhouse')


    def _extract_positions_from_response(self, data: Any, api_format: str) -> List[Dict[str, Any]]:
        """Extract job positions from API response.
        
        Args:
            data: API response data
            api_format: Detected API format
            
        Returns:
            List of position dictionaries
        """
        if api_format in ['jibe', 'greenhouse']:
            positions = data.get("jobs", [])
        elif api_format == 'comeet':
            if isinstance(data, list):
                positions = data
            else:
                positions = data.get("positions", [])
        else:
            positions = []
        
        logger.info(f"Extracted {len(positions)} positions from {api_format} API")
        return positions

    async def _parse_and_filter_jobs(self, positions: List[Dict[str, Any]], parser: Any) -> List[Dict[str, Any]]:
        """Parse positions and apply filters.
        
        Args:
            positions: List of raw position data
            parser: Parser instance to use
            
        Returns:
            List of validated and filtered job dictionaries
        """
        jobs = []
        
        for position in positions:
            try:
                job = parser.parse(position)
                if not job:
                    position_name = position.get('name') or position.get('title', 'Unknown')
                    logger.warning(f"Failed to parse position: {position_name}")
                    continue
                
                logger.debug(f"Parsed job: {job.get('title')} at {job.get('location')}")
                
                if not self.validate_job_data(job):
                    logger.warning(f"Job failed validation: {job.get('title')}")
                    continue
                
                if not self.matches_location_filter(job):
                    self.stats["jobs_filtered"] += 1
                    logger.debug(f"Filtered out job: {job.get('title')} at {job.get('location')}")
                    continue
                
                jobs.append(self.normalize_job_data(job))
                
            except Exception as e:
                logger.error(f"Error parsing position: {e}")
                continue
        
        return jobs

    def _make_absolute_url(self, href: str) -> str:
        """Convert relative URL to absolute URL.
        
        Args:
            href: URL or path to convert (can be absolute, relative, or protocol-relative)
            
        Returns:
            Absolute URL. Returns original href if it's already absolute or if base URL is not configured.
            
        Examples:
            >>> self._make_absolute_url("https://example.com/jobs")
            "https://example.com/jobs"
            >>> self._make_absolute_url("/careers/job/123")
            "https://company.com/careers/job/123"
            >>> self._make_absolute_url("job/123")
            "https://company.com/job/123"
        """
        
        # If already absolute URL, return as-is
        if href.startswith(("http://", "https://")):
            return href
        
        # Get base URL from config
        base_url = self.company_config.get("website", "")
        if not base_url:
            logger.warning(f"No base URL configured, returning relative URL: {href}")
            return href
        
        # Ensure base_url has a scheme
        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"
        
        # Use urljoin for proper URL joining (handles all edge cases)
        absolute_url = urljoin(base_url, href)
        
        logger.debug(f"Converted URL: {href} -> {absolute_url}")
        return absolute_url

    async def _extract_jobs_from_page(self, selectors: Dict[str, str], page_num: int = 1) -> List[Dict[str, Any]]:
        """Extract job listings from current page.
        
        Args:
            selectors: Dictionary of CSS selectors for job elements
            page_num: Page number for logging context (default: 1)
            
        Returns:
            List of validated and normalized job dictionaries
        """
        jobs = []

        job_item_selector = selectors.get("job_item")
        if not job_item_selector:
            logger.warning("No job_item selector configured")
            return jobs

        logger.info(f"Page {page_num}: Looking for jobs with selector: {job_item_selector}")

        # Get all job items
        job_elements = await self.page.query_selector_all(job_item_selector)
        logger.info(f"Page {page_num}: Found {len(job_elements)} job elements")

        if len(job_elements) == 0:
            await self._debug_selectors(selectors)
            return jobs

        # Extract jobs from elements
        for idx, element in enumerate(job_elements, 1):
            try:
                job = await self._extract_job_from_element(element, selectors)
                
                if not job:
                    logger.debug(f"Page {page_num}, Job {idx}: No data extracted")
                    continue
                
                if not self.validate_job_data(job):
                    logger.debug(f"Page {page_num}, Job {idx}: Failed validation - {job.get('title', 'Unknown')}")
                    continue
                
                jobs.append(self.normalize_job_data(job))
                logger.debug(f"Page {page_num}, Job {idx}: ✓ {job.get('title')} at {job.get('location')}")
                
            except Exception as e:
                logger.error(f"Page {page_num}, Job {idx}: Error extracting - {e}")
                self.stats["errors"] += 1

        logger.info(f"Page {page_num}: Extracted {len(jobs)} valid jobs from {len(job_elements)} elements")
        return jobs

    async def _debug_selectors(self, selectors: Dict[str, str]) -> None:
        """Debug helper to test all selectors when no jobs are found.
        
        Args:
            selectors: Dictionary of CSS selectors to test
        """
        logger.warning("No job elements found. Testing all selectors...")

        for selector_name, selector_value in selectors.items():
            if not selector_value:
                continue
            
            try:
                elements = await self.page.query_selector_all(selector_value)
                logger.debug(f"Selector '{selector_name}' ({selector_value}): {len(elements)} elements")
            except Exception as e:
                logger.error(f"Selector '{selector_name}' ({selector_value}): Error - {e}")

    async def _extract_job_from_element(
        self,
        element,
        selectors: Dict[str, str]
    ) -> Dict[str, Any]:
        """Extract job data from a single element.
        
        Args:
            element: Playwright element handle
            selectors: Dictionary of CSS selectors for job fields
            
        Returns:
            Dictionary containing extracted job data
        """
        job = {}

        try:
            # Extract title
            title_el = await self._extract_text_field(element, selectors.get("job_title"), "title", job)
            
            # Extract location
            await self._extract_text_field(element, selectors.get("job_location"), "location", job)
            
            # Extract URL using multiple strategies
            await self._extract_job_url(element, selectors, job, title_el)
            
            # Extract optional fields
            await self._extract_text_field(element, selectors.get("job_department"), "department", job)
            await self._extract_text_field(element, selectors.get("job_type"), "employment_type", job)
            
            # Generate external_id
            self._generate_external_id(job)
            
        except Exception as e:
            logger.error(f"Error extracting job from element: {e}")
            return {}
        
        return job

    async def _extract_text_field(
        self,
        element,
        selector: Optional[str],
        field_name: str,
        job: Dict[str, Any]
    ) -> Optional[Any]:
        """Extract text from an element using a selector.
        
        Args:
            element: Parent element to search within
            selector: CSS selector for the field
            field_name: Name of the field to store in job dict
            job: Job dictionary to update
            
        Returns:
            The element if found, None otherwise
        """
        if not selector:
            return None
        
        try:
            field_el = await element.query_selector(selector)
            if field_el:
                text = await field_el.inner_text()
                job[field_name] = text.strip()
                return field_el
        except Exception as e:
            logger.debug(f"Failed to extract {field_name} with selector '{selector}': {e}")
        
        return None

    async def _extract_job_url(
        self,
        element,
        selectors: Dict[str, str],
        job: Dict[str, Any],
        title_el: Optional[Any] = None
    ) -> bool:
        """Extract job URL using multiple fallback strategies.
        
        Args:
            element: Parent element to search within
            selectors: Dictionary of CSS selectors
            job: Job dictionary to update
            title_el: Optional title element (if already extracted)
            
        Returns:
            True if URL was found, False otherwise
        """
        # Strategy 1: Check if title element is a link
        if title_el:
            url = await self._get_href_from_element(title_el)
            if url:
                job["job_url"] = self._make_absolute_url(url)
                return True
        
        # Strategy 2: Look for link using URL selector
        url_selector = selectors.get("job_url")
        if url_selector:
            try:
                url_el = await element.query_selector(url_selector)
                if url_el:
                    url = await self._get_href_from_element(url_el)
                    if url:
                        job["job_url"] = self._make_absolute_url(url)
                        return True
            except Exception as e:
                logger.debug(f"Failed to extract URL with selector '{url_selector}': {e}")
        
        # Strategy 3: Look for any job-related link in the element
        try:
            link_el = await element.query_selector("a[href]")
            if link_el:
                url = await self._get_href_from_element(link_el)
                if url and self._is_job_url(url):
                    job["job_url"] = self._make_absolute_url(url)
                    return True
        except Exception as e:
            logger.debug(f"Failed to find fallback link: {e}")
        
        return False

    async def _get_href_from_element(self, element) -> Optional[str]:
        """Safely extract href attribute from an element.
        
        Args:
            element: Element to extract href from
            
        Returns:
            href value or None
        """
        try:
            # Check if element is a link
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            if tag_name == "a":
                href = await element.get_attribute("href")
                return href if href else None
        except Exception as e:
            logger.debug(f"Failed to get href: {e}")
        
        return None

    def _is_job_url(self, url: str) -> bool:
        """Check if URL looks like a job posting URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL appears to be a job posting
        """
        url_lower = url.lower()
        job_indicators = ["/job", "/career", "/position", "/opening", "/vacancy", "/opportunity"]
        return any(indicator in url_lower for indicator in job_indicators)

    def _generate_external_id(self, job: Dict[str, Any]) -> None:
        """Generate external_id for a job.
        
        Args:
            job: Job dictionary to update with external_id
        """
        
        if "job_url" in job:
            # Use last part of URL as ID, but include company name for uniqueness
            url_part = job["job_url"].split("/")[-1].split("?")[0]
            company_name = self.company_config.get("name", "unknown")
            # Combine company and URL part for better uniqueness
            job["external_id"] = f"{company_name}_{url_part}"[:64]
        elif "title" in job:
            # Generate hash from title + company for uniqueness
            company_name = self.company_config.get("name", "unknown")
            unique_str = f"{company_name}_{job['title']}"
            job["external_id"] = hashlib.md5(unique_str.encode()).hexdigest()[:16]

    async def _scrape_playwright_page(self) -> List[Dict[str, Any]]:
        """Scrape jobs from a page using Playwright.
        
        Handles both static and dynamic pages based on configuration.
        
        Configuration options:
            - search_url: URL to navigate to (defaults to careers_url)
            - wait_until: Page load strategy - 'domcontentloaded', 'load', or 'networkidle' (default: 'domcontentloaded')
            - page_timeout: Page load timeout in ms (default: 90000)
            - wait_for_selector: Optional selector to wait for after page load
            - selector_timeout: Timeout for wait_for_selector in ms (default: 30000)
            - debug_mode: Save page HTML for debugging (default: false)
        
        Returns:
            List of job dictionaries
        """
        careers_url = self.company_config.get("careers_url")
        search_url = self.scraping_config.get("search_url", careers_url)
        
        if not search_url:
            logger.error("No search_url or careers_url configured")
            return []
        
        # Get configurable options
        wait_until = self.scraping_config.get("wait_until", "domcontentloaded")
        page_timeout = self.scraping_config.get("page_timeout", 90000)
        selector_timeout = self.scraping_config.get("selector_timeout", 30000)

        logger.info(f"Navigating to {search_url}")
        
        try:
            await self.page.goto(search_url, wait_until=wait_until, timeout=page_timeout)
            logger.info(f"Page loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load page: {e}")
            raise

        # Optional debug mode
        if self.scraping_config.get("debug_mode", False):
            await self._save_page_debug_info()

        # Wait for specific selector if configured
        wait_selector = self.scraping_config.get("wait_for_selector")
        if wait_selector:
            await self._wait_for_content_load(selector_timeout)

        # Extract jobs
        selectors = self.scraping_config.get("selectors", {})
        jobs = await self._extract_jobs_from_page(selectors)

        self.stats["pages_scraped"] += 1
        self.stats["requests_made"] += 1
        
        logger.info(f"Scraped {len(jobs)} jobs from page")
        return jobs

    async def _save_page_debug_info(self) -> None:
        """Save page HTML for debugging purposes.
        
        Only called when debug_mode is enabled in configuration.
        """
        try:
            html_content = await self.page.content()
            logger.debug(f"Page HTML length: {len(html_content)} characters")
            
            # Get debug directory from config or use default
            debug_dir = self.scraping_config.get("debug_dir", "data/raw")
            os.makedirs(debug_dir, exist_ok=True)
            
            company_name = self.company_config.get('name', 'unknown').replace(' ', '_')
            debug_file = os.path.join(debug_dir, f"{company_name}_page.html")
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.debug(f"Saved page HTML to {debug_file}")
        except Exception as e:
            logger.warning(f"Failed to save debug info: {e}")

    async def _wait_for_content_load(self, timeout: int = 30000) -> None:
        """Wait for dynamic content to load.
        
        Args:
            timeout: Maximum time to wait in milliseconds
        """
        wait_selector = self.scraping_config.get("wait_for_selector")
        
        if not wait_selector:
            logger.debug("No wait_for_selector configured, skipping wait")
            return
        
        try:
            await self.page.wait_for_selector(wait_selector, timeout=timeout)
            logger.info(f"Content loaded - found selector: {wait_selector}")
        except Exception as e:
            logger.warning(f"Timeout waiting for selector '{wait_selector}': {e}")
            # Log page info for debugging
            try:
                page_title = await self.page.title()
                page_url = self.page.url
                logger.info(f"Page title: {page_title}")
                logger.info(f"Page URL: {page_url}")
            except Exception as debug_error:
                logger.debug(f"Failed to get page info: {debug_error}")

    async def _scrape_html(self) -> List[Dict[str, Any]]:
        """
        Scrape jobs using simple HTTP requests (for sites like Island that block Playwright).

        Returns:
            List of job dictionaries
        """

        careers_url = self.company_config.get("careers_url")
        logger.info(f"Fetching HTML from: {careers_url}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        try:
            response = requests.get(careers_url, headers=headers, timeout=30)
            response.raise_for_status()
            logger.info(f"HTTP Status: {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Get selectors from config
            selectors = self.scraping_config.get("selectors", {})
            job_link_selector = selectors.get("job_link", "a[href*='comeet.com/jobs']")

            # Find all job links
            job_links = soup.select(job_link_selector)
            logger.info(f"Found {len(job_links)} job links")

            jobs = []
            seen_positions = set()

            for link in job_links:
                href = link.get('href', '')
                position = link.get('data-position', '')

                # Skip if no position or duplicate
                if not position or position in seen_positions:
                    continue
                seen_positions.add(position)

                # Extract location and department
                location = link.get('data-location', '')
                department = link.get('data-team', '')

                # If not in link, try parent container
                if not location or not department:
                    parent = link.find_parent(attrs={'data-location': True})
                    if parent:
                        location = location or parent.get('data-location', '')
                        department = department or parent.get('data-team', '')

                # Make URL absolute
                if href and not href.startswith('http'):
                    if href.startswith('/'):
                        href = 'https://www.comeet.com' + href
                    else:
                        href = 'https://www.comeet.com/' + href

                # Create job dict
                job = {
                    "title": position,
                    "location": location,
                    "department": department,
                    "job_url": href,
                    "description": "",
                    "employment_type": None,
                    "posted_date": None,
                    "is_remote": "remote" in location.lower() if location else False,
                }

                # Validate and normalize
                if self.validate_job_data(job):
                    # Apply location filter
                    if self.matches_location_filter(job):
                        jobs.append(self.normalize_job_data(job))
                        logger.info(f"Parsed job: {job['title']} at {job['location']}")
                    else:
                        self.stats["jobs_filtered"] += 1
                        logger.debug(f'Filtered out job: {job["title"]} at {job["location"]}')
                else:
                    logger.warning(f"Job failed validation: {job}")

            self.stats["requests_made"] += 1
            return jobs

        except Exception as e:
            logger.error(f"Error scraping HTML: {e}")
            self.stats["errors"] += 1
            return []

    async def _scrape_rss(self) -> List[Dict[str, Any]]:
        """Scrape jobs from RSS/XML feed (e.g., TalentBrew)."""

        rss_url = self.scraping_config.get("rss_url")
        if not rss_url:
            logger.error("No rss_url configured for RSS scraping")
            return []

        logger.info(f"Fetching jobs from RSS feed: {rss_url}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(rss_url)
                response.raise_for_status()

                logger.info(f"RSS Response Status: {response.status_code}")
                logger.info(f"Content-Type: {response.headers.get('content-type')}")

            # Parse XML
            root = ET.fromstring(response.content)

            # Find all job items
            items = root.findall('.//item')
            logger.info(f"Found {len(items)} jobs in RSS feed")

            jobs = []
            for item in items:
                job = self._get_parser('rss').parse(item)
                if job:
                    logger.info(f"Parsed job: {job.get('title')} at {job.get('location')}")
                    if self.validate_job_data(job):
                        # Apply location filter
                        if self.matches_location_filter(job):
                            jobs.append(self.normalize_job_data(job))
                        else:
                            self.stats["jobs_filtered"] += 1
                            logger.debug(f'Filtered out job: {job.get("title")} at {job.get("location")}')
                    else:
                        logger.warning(f"Job failed validation: {job}")
                else:
                    logger.warning(f"Failed to parse RSS item")

            self.stats["requests_made"] += 1
            return jobs

        except Exception as e:
            logger.error(f"Error scraping RSS feed: {e}")
            self.stats["errors"] += 1
            return []

    async def _scrape_api_with_pagination(self) -> List[Dict[str, Any]]:
        """
        Scrape jobs from API with offset-based pagination.
        
        Used for APIs like Amazon and Nvidia (Eightfold) that support pagination.
        
        Configuration:
            - api_endpoint: API URL (required)
            - timeout: Request timeout in seconds (default: 30)
            - query_params: Base query parameters (default: {})
            - pagination_params:
                - offset_param: Name of offset parameter (default: "offset")
                - limit_param: Name of limit parameter (default: "limit")
                - page_size: Number of jobs per page (default: 100)
                - max_pages: Maximum pages to fetch (default: 10)
            - response_structure:
                - jobs_key: Path to jobs array (default: "jobs")
                - total_key: Path to total count (default: "hits")
        
        Returns:
            List of job dictionaries
        """
        # Validate required config
        api_endpoint = self.scraping_config.get("api_endpoint")
        if not api_endpoint:
            logger.error("No api_endpoint configured for API pagination scraping")
            return []
        
        # Get configuration
        pagination_params = self.scraping_config.get("pagination_params", {})
        query_params = self.scraping_config.get("query_params", {})
        response_structure = self.scraping_config.get("response_structure", {})
        
        offset_param = pagination_params.get("offset_param", "offset")
        limit_param = pagination_params.get("limit_param", "limit")
        page_size = pagination_params.get("page_size", 100)
        max_pages = pagination_params.get("max_pages", 10)
        jobs_key = response_structure.get("jobs_key", "jobs")
        total_key = response_structure.get("total_key", "hits")
        timeout = self.scraping_config.get("timeout", 30.0)
        
        logger.info(f"Fetching jobs from API with pagination: {api_endpoint}")
        logger.info(f"Pagination: {offset_param}={page_size}, max_pages={max_pages}")
        
        all_jobs = []
        offset = 0
        page = 0
        
        # Get parser once (not in loop)
        parser = self._get_api_parser_for_pagination()
        
        while page < max_pages:
            # Build params for this page
            params = dict(query_params)
            params[offset_param] = offset
            if limit_param:  # Only add limit if specified (Eightfold doesn't use it)
                params[limit_param] = page_size
            
            logger.info(f"Fetching page {page + 1} (offset={offset}, limit={page_size})")
            
            try:
                # Fetch page data
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(api_endpoint, params=params)
                    response.raise_for_status()
                    data = response.json()
                
                # Extract positions from response (supports nested keys)
                positions = self._extract_nested_value(data, jobs_key)
                
                if positions and isinstance(positions, list):
                    # Get total hits if available
                    total_hits = self._extract_nested_value(data, total_key) if total_key else 0
                    
                    logger.info(f"Found {len(positions)} jobs on page {page + 1}" +
                               (f" (total: {total_hits})" if total_hits else ""))
                    
                    # Parse jobs from this page
                    jobs_on_page = []
                    for position in positions:
                        job = parser.parse(position)
                        if job and self.validate_job_data(job):
                            if self.matches_location_filter(job):
                                jobs_on_page.append(self.normalize_job_data(job))
                            else:
                                self.stats["jobs_filtered"] += 1
                                logger.debug(f'Filtered out job: {job.get("title")} at {job.get("location")}')
                    
                    all_jobs.extend(jobs_on_page)
                    self.stats["requests_made"] += 1
                    
                    # Check if we've reached the end
                    if len(positions) == 0:
                        logger.info(f"No more jobs found at page {page + 1}")
                        break
                    elif len(positions) < page_size:
                        logger.info(f"Reached end of results at page {page + 1}")
                        break
                    elif total_hits and offset + len(positions) >= total_hits:
                        logger.info(f"Reached total hits ({total_hits}) at page {page + 1}")
                        break
                else:
                    logger.warning(f"Unexpected API format or no positions found")
                    logger.warning(f"Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    break
                
                # Move to next page
                offset += len(positions)
                page += 1
                
                # Delay between requests
                await asyncio.sleep(self.scraping_config.get("wait_time", 1))
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching page {page + 1} from {api_endpoint}: {e}")
                self.stats["errors"] += 1
                break
            except Exception as e:
                logger.error(f"Error fetching page {page + 1} from {api_endpoint}: {e}")
                self.stats["errors"] += 1
                break
        
        logger.info(f"Total jobs scraped: {len(all_jobs)} across {page} pages")
        return all_jobs

    def _extract_nested_value(self, data: Dict[str, Any], key_path: str) -> Any:
        """
        Extract value from nested dictionary/list using dot notation.

        Supports:
        - Dictionary keys: 'data.positions'
        - Array indices: 'items.0.requisitionList'
        - Mixed: 'data.items.0.jobs'

        Args:
            data: The data structure to extract from
            key_path: Dot-separated path (e.g., 'items.0.requisitionList')

        Returns:
            Extracted value or None if path doesn't exist
        """
        if not key_path:
            return None

        keys = key_path.split('.')
        value = data

        for key in keys:
            # Check if key is a numeric index (for arrays)
            if key.isdigit():
                index = int(key)
                if isinstance(value, list) and 0 <= index < len(value):
                    value = value[index]
                else:
                    return None
            # Otherwise treat as dictionary key
            elif isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    async def _scrape_workday(self) -> List[Dict[str, Any]]:
        """Scrape jobs from Workday API with pagination support (e.g., Salesforce)."""
        api_endpoint = self.scraping_config.get("api_endpoint")
        pagination_params = self.scraping_config.get("pagination_params", {})
        workday_config = self.scraping_config.get("workday_config", {})
        response_structure = self.scraping_config.get("response_structure", {})

        offset_param = pagination_params.get("offset_param", "offset")
        limit_param = pagination_params.get("limit_param", "limit")
        page_size = pagination_params.get("page_size", 20)
        max_pages = pagination_params.get("max_pages", 50)

        # Workday-specific config
        search_text = workday_config.get("search_text", "")
        applied_facets = workday_config.get("applied_facets", {})

        # Get jobs key
        jobs_key = response_structure.get("jobs_key", "jobPostings")
        total_key = response_structure.get("total_key", "total")

        logger.info(f"Fetching jobs from Workday API: {api_endpoint}")
        logger.info(f"Search text: {search_text}")
        logger.info(f"Pagination: {offset_param}={page_size}, max_pages={max_pages}")

        all_jobs = []
        offset = 0
        page = 0

        while page < max_pages:
            # Build Workday POST payload
            payload = {
                "appliedFacets": applied_facets,
                limit_param: page_size,
                offset_param: offset,
                "searchText": search_text
            }

            logger.info(f"Fetching page {page + 1} (offset={offset}, limit={page_size})")

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        api_endpoint,
                        json=payload,
                        headers={
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        }
                    )
                    response.raise_for_status()
                    data = response.json()

                # Extract job postings
                positions = data.get(jobs_key, [])
                total_hits = data.get(total_key, 0)

                if positions and isinstance(positions, list):
                    logger.info(f"Found {len(positions)} jobs on page {page + 1} (total: {total_hits})")

                    jobs_on_page = []
                    for position in positions:
                        # Use Salesforce/Workday parser
                        job = self._get_parser('salesforce').parse(position)

                        if job and self.validate_job_data(job):
                            # Apply location filter
                            if self.matches_location_filter(job):
                                jobs_on_page.append(self.normalize_job_data(job))
                            else:
                                self.stats["jobs_filtered"] += 1
                                logger.debug(f'Filtered out job: {job.get("title")} at {job.get("location")}')

                    all_jobs.extend(jobs_on_page)
                    self.stats["requests_made"] += 1

                    # Check if we've reached the end
                    if len(positions) == 0:
                        logger.info(f"No more jobs found at page {page + 1}")
                        break
                    elif len(positions) < page_size:
                        logger.info(f"Reached end of results at page {page + 1}")
                        break
                    elif offset + len(positions) >= total_hits:
                        logger.info(f"Reached total hits ({total_hits}) at page {page + 1}")
                        break
                else:
                    logger.warning(f"No positions found in response")
                    break

                # Move to next page
                offset += len(positions)
                page += 1

                # Small delay between requests
                await asyncio.sleep(self.scraping_config.get("wait_time", 1))

            except Exception as e:
                logger.error(f"Error fetching page {page + 1}: {e}")
                self.stats["errors"] += 1
                break

        logger.info(f"Total jobs scraped: {len(all_jobs)} across {page + 1} pages")
        return all_jobs



    async def _scrape_phenom(self) -> List[Dict[str, Any]]:
        """Scrape jobs from Phenom People platform using Playwright.

        Returns:
            List of job dictionaries
        """
        careers_url = self.company_config.get("careers_url")
        phenom_config = self.scraping_config.get("phenom_config", {})

        # Get location filter from config
        location_filter = phenom_config.get("location_filter", "")
        max_pages = phenom_config.get("max_pages", 5)

        logger.info(f"Scraping Phenom People platform: {careers_url}")
        if location_filter:
            logger.info(f"Location filter: {location_filter}")

        # Build URL with location filter
        search_url = careers_url
        if location_filter:
            # Check if we should use path-based or query parameter
            location_param_type = phenom_config.get("location_param_type", "query")
            if location_param_type == "path":
                # Path-based: /search-jobs/Location (Intuit)
                search_url = f"{careers_url}/{location_filter}"
            else:
                # Query parameter: ?location=Location (ServiceNow)
                search_url = f"{careers_url}?location={location_filter}"

        logger.info(f"Navigating to {search_url}")
        await self.page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        await self.page.wait_for_timeout(10000)  # Wait for jobs to load

        # Scroll to load more jobs
        for i in range(3):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(2000)

        all_jobs = []
        seen_urls = set()

        # Find all job links
        # Try multiple selectors for different platforms
        job_links = []
        selectors = [
    'a[href*="/job/"]',  # Intuit/Phenom - try this first
    'a[class*="job"]',  # ServiceNow
    'h2 a',  # ServiceNow alternative
        ]

        for selector in selectors:
            try:
                links = await self.page.query_selector_all(selector)
                if links:
                    job_links = links
                    logger.info(f"Using selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
        logger.info(f"Found {len(job_links)} job links")

        for link in job_links:
            try:
                href = await link.get_attribute('href')
                if href and href not in seen_urls and ('/job/' in href or '/jobs/' in href):
                    seen_urls.add(href)

                    # Get the link text (title)
                    title = await link.inner_text()
                    title = title.strip()

                    # Check if this is a real job title (not navigation)
                    if title and len(title) > 5 and 'saved' not in title.lower() and 'alert' not in title.lower() and 'jobs' != title.lower():
                        # Try to find location from nearby elements
                        location = "Unknown"
                        try:
                            # Try to find parent container and look for location
                            parent = await link.evaluate_handle('el => el.closest("article, div[class*=\'job\'], li")')
                            if parent:
                                # Look for location text in parent
                                location_text = await parent.evaluate(
                                    '''el => { const locationEl = el.querySelector('[class*="location"], [class*="city"], .card-text, .list-inline'); return locationEl ? locationEl.textContent.trim() : null; }'''
                                )
                                if location_text:
                                    location = location_text
                        except Exception as e:
                            logger.debug(f"Could not extract location from parent: {e}")

                        # If location not found, try to extract from URL
                        if location == "Unknown":
                            import re
                            # Match /job/{location}/{title}/ pattern (not /jobs/{id}/{title}/)
                            location_match = re.search(r'/job/([^/]+)/', href)
                            if location_match:
                                potential_location = location_match.group(1)
                                # Skip if it's just a number (job ID)
                                if not potential_location.isdigit():
                                    location = potential_location.replace('-', ' ').title()

                        # Build full URL
                        job_url = href if href.startswith('http') else f"{careers_url.rstrip('/')}{href}"

                        job_data = {
                            'title': title,
                            'location': location,
                            'url': job_url
                        }

                        # Parse using Phenom parser
                        job = self._get_parser('phenom').parse(job_data)

                        if job and self.validate_job_data(job):
                            # Apply location filter
                            if self.matches_location_filter(job):
                                all_jobs.append(self.normalize_job_data(job))
                            else:
                                self.stats["jobs_filtered"] += 1
                                logger.debug(f'Filtered out job: {job.get("title")} at {job.get("location")}')
            except Exception as e:
                logger.warning(f"Error extracting job from link: {e}")
                continue

        logger.info(f"Total jobs scraped: {len(all_jobs)}")
        self.stats["requests_made"] += 1
        return all_jobs

    async def _scrape_meta_graphql(self) -> List[Dict[str, Any]]:
        """
        Scrape Meta careers using Playwright to intercept GraphQL responses.

        Returns:
            List of job dictionaries
        """
        jobs = []
        search_url = self.scraping_config.get("search_url") or self.company_config.get("careers_url")

        logger.info(f"Scraping Meta GraphQL from: {search_url}")

        # Variable to store GraphQL response
        graphql_jobs_data = None

        async def handle_response(response):
            """Intercept GraphQL responses to extract job data."""
            nonlocal graphql_jobs_data

            if 'graphql' in response.url:
                try:
                    data = await response.json()
                    if 'data' in data and data['data']:
                        if 'job_search_with_featured_jobs' in data['data']:
                            graphql_jobs_data = data['data']['job_search_with_featured_jobs']
                            logger.info("Captured Meta GraphQL jobs response")
                except Exception as e:
                    logger.debug(f"Error parsing GraphQL response: {e}")

        try:
            # Set up response handler
            self.page.on('response', handle_response)

            # Navigate to Meta careers page
            logger.info(f"Navigating to: {search_url}")
            await self.page.goto(search_url, wait_until='networkidle', timeout=60000)

            # Wait for GraphQL to load
            wait_time = self.scraping_config.get("wait_time", 5)
            await self.page.wait_for_timeout(wait_time * 1000)

            # Check if we captured the GraphQL response
            if graphql_jobs_data and 'all_jobs' in graphql_jobs_data:
                all_jobs = graphql_jobs_data['all_jobs']

                if isinstance(all_jobs, list):
                    logger.info(f"Found {len(all_jobs)} jobs in GraphQL response")

                    for job_data in all_jobs:
                        job = self._get_parser('meta').parse(job_data)
                        if job:
                            logger.info(f"Parsed job: {job.get('title')} at {job.get('location')}")
                            if self.validate_job_data(job):
                                # Apply location filter
                                if self.matches_location_filter(job):
                                    jobs.append(self.normalize_job_data(job))
                                else:
                                    self.stats["jobs_filtered"] += 1
                                    logger.debug(f'Filtered out job: {job.get("title")} at {job.get("location")}')
                            else:
                                logger.warning(f"Job failed validation: {job}")
                else:
                    logger.warning(f"Unexpected all_jobs format: {type(all_jobs)}")
            else:
                logger.warning("No GraphQL jobs data captured")

            self.stats["requests_made"] += 1
            return jobs

        except Exception as e:
            logger.error(f"Error scraping Meta GraphQL: {e}")
            self.stats["errors"] += 1
            return []

