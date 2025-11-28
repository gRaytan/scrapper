"""
Consolidated test suite for all company scrapers.
Tests Monday.com, Wiz, Island, and EON scrapers.
"""
import asyncio
import sys
import os
import requests
import yaml
# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
from src.utils.logger import setup_logging
from src.scrapers.playwright_scraper import PlaywrightScraper
from src.scrapers.parsers.microsoft_parser import MicrosoftParser
from src.scrapers.parsers.apple_parser import AppleParser
from src.scrapers.parsers.google_parser import GoogleParser
from src.scrapers.parsers.workday_parser import WorkdayParser

setup_logging()


class CompanyScraperTests:

    def load_company_config(self, company_name: str):
        """Load company configuration from companies.yaml file."""
        import yaml
        
        with open('config/companies.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        company_config = next(
            (c for c in config['companies'] if c['name'] == company_name),
            None
        )
        
        if not company_config:
            raise ValueError(f"Company '{company_name}' not found in config")
        
        return company_config.get('location_filter', {}), company_config.get('scraping_config', {})

    """Test suite for company scrapers."""
    
    def __init__(self):
        self.results = {}
    
    async def test_monday_scraper(self):
        """Test Monday.com scraper using Comeet API."""
        logger.info("=" * 80)
        logger.info("Testing Monday.com Scraper (Comeet API)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "Monday.com",
            "website": "https://monday.com",
            "careers_url": "https://monday.com/careers",
        }
        
        scraping_config = {
            "scraper_type": "api",
            "pagination_type": "none",
            "requires_js": False,
            "api_endpoint": "https://www.comeet.co/careers-api/2.0/company/41.00B/positions?token=14B52C52C67790D3E1296BA37C20",
            "api_method": "GET",
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            success = len(jobs) > 0
            self.results['Monday.com'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            
            if success:
                logger.success(f"✓ Monday.com: Found {len(jobs)} jobs")
            else:
                logger.error("✗ Monday.com: No jobs found")
            
            return success
            
        finally:
            await scraper.teardown()
    
    async def test_wiz_scraper(self):
        """Test Wiz scraper using Greenhouse API."""
        logger.info("=" * 80)
        logger.info("Testing Wiz Scraper (Greenhouse API)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "Wiz",
            "website": "https://www.wiz.io",
            "careers_url": "https://boards.greenhouse.io/wizinc",
        }
        
        scraping_config = {
            "scraper_type": "api",
            "pagination_type": "none",
            "requires_js": False,
            "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/wizinc/jobs",
            "api_method": "GET",
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            success = len(jobs) > 0
            self.results['Wiz'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            
            if success:
                logger.success(f"✓ Wiz: Found {len(jobs)} jobs")
            else:
                logger.error("✗ Wiz: No jobs found")
            
            return success
            
        finally:
            await scraper.teardown()
    
    async def test_island_scraper(self):
        """Test Island scraper using HTML scraping."""
        logger.info("=" * 80)
        logger.info("Testing Island Scraper (HTML Scraping)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "Island",
            "website": "https://www.island.io",
            "careers_url": "https://www.island.io/careers",
        }
        
        scraping_config = {
            "scraper_type": "requests",
            "pagination_type": "none",
            "requires_js": False,
            "selectors": {
                "job_link": "a[href*='comeet.com/jobs']",
                "job_title": "[data-position]",
                "job_location": "[data-location]",
                "job_department": "[data-team]",
            }
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            success = len(jobs) > 0
            self.results['Island'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            
            if success:
                logger.success(f"✓ Island: Found {len(jobs)} jobs")
            else:
                logger.error("✗ Island: No jobs found")
            
            return success
            
        finally:
            await scraper.teardown()
    
    async def test_eon_scraper(self):
        """Test EON scraper using Greenhouse API."""
        logger.info("=" * 80)
        logger.info("Testing EON Scraper (Greenhouse API)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "EON",
            "website": "https://www.eon.io",
            "careers_url": "https://boards.eu.greenhouse.io/eonio",
        }
        
        scraping_config = {
            "scraper_type": "api",
            "pagination_type": "none",
            "requires_js": False,
            "api_endpoint": "https://api.greenhouse.io/v1/boards/eonio/jobs",
            "api_method": "GET",
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            success = len(jobs) > 0
            self.results['EON'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            
            if success:
                logger.success(f"✓ EON: Found {len(jobs)} jobs")
            else:
                logger.error("✗ EON: No jobs found")
            
            return success
            
        finally:
            await scraper.teardown()
    
    async def test_palo_alto_scraper(self):
        """Test Palo Alto Networks scraper with RSS feed."""
        logger.info("=" * 80)
        logger.info("Testing Palo Alto Networks Scraper (TalentBrew RSS)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "Palo Alto Networks",
            "website": "https://www.paloaltonetworks.com",
            "careers_url": "https://jobs.paloaltonetworks.com",
            "industry": "Cybersecurity"
        }
        
        scraping_config = {
            "scraper_type": "rss",
            "rss_url": "https://jobs.paloaltonetworks.com/en/rss",
            "wait_time": 2
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            logger.success(f"✓ Palo Alto Networks: Found {len(jobs)} jobs")
            
            # Show sample jobs
            if jobs:
                logger.info("\n=== Sample Jobs ===")
                for i, job in enumerate(jobs[:3], 1):
                    logger.info(f"\nJob {i}:")
                    logger.info(f"  Title: {job.get('title')}")
                    logger.info(f"  Location: {job.get('location')}")
                    logger.info(f"  Department: {job.get('department')}")
            
            # Validate
            assert len(jobs) > 0, "No jobs found"
            assert all(job.get('title') for job in jobs), "Some jobs missing title"
            assert all(job.get('job_url') for job in jobs), "Some jobs missing URL"
            
            self.results['Palo Alto Networks'] = {
                'success': True,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            return True
            
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            self.results['Palo Alto Networks'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False
            
        finally:
            await scraper.teardown()
    async def test_amazon_scraper(self):
        """Test Amazon scraper with direct API."""
        logger.info("=" * 80)
        logger.info("Testing Amazon Scraper (Direct API)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "Amazon",
            "website": "https://www.amazon.com",
            "careers_url": "https://www.amazon.jobs",
            "industry": "Technology"
        }
        
        scraping_config = {
            "scraper_type": "api",  # Direct API scraping
            "api_endpoint": "https://www.amazon.jobs/en/search.json",
            "api_method": "GET",
            "pagination_type": "offset",
            "pagination_params": {
                "offset_param": "offset",
                "limit_param": "result_limit",
                "page_size": 100,
                "max_pages": 3  # Limit to 3 pages for testing (300 jobs)
            },
            "wait_time": 1
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            logger.success(f"✓ Amazon: Found {len(jobs)} jobs")
            
            # Show sample jobs
            if jobs:
                logger.info("\n=== Sample Jobs ===")
                for i, job in enumerate(jobs[:3], 1):
                    logger.info(f"\nJob {i}:")
                    logger.info(f"  Title: {job.get('title')}")
                    logger.info(f"  Location: {job.get('location')}")
                    logger.info(f"  Department: {job.get('department')}")
            
            # Validate
            assert len(jobs) > 0, "No jobs found"
            assert all(job.get('title') for job in jobs), "Some jobs missing title"
            assert all(job.get('job_url') for job in jobs), "Some jobs missing URL"
            
            self.results['Amazon'] = {
                'success': True,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            return True
            
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            self.results['Amazon'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False
            
        finally:
            await scraper.teardown()
    
    async def test_meta_scraper(self):
        """Test Meta scraper using GraphQL API."""
        logger.info("=" * 80)
        logger.info("Testing Meta Scraper (GraphQL API)")
        logger.info("=" * 80)
        
        # Load config from companies.yaml
        with open('config/companies.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        meta_config = next(
            (c for c in config['companies'] if c['name'] == 'Meta'),
            None
        )
        
        if not meta_config:
            logger.error("Meta not found in config")
            return False
        
        company_config = {
            "name": meta_config['name'],
            "website": meta_config['website'],
            "careers_url": meta_config['careers_url'],
            "industry": meta_config.get('industry', 'Technology'),
            "location_filter": meta_config.get('location_filter', {})
        }
        
        scraping_config = meta_config.get('scraping', {})

        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            success = len(jobs) > 0
            self.results['Meta'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            
            if success:
                logger.success(f"✓ Meta: Found {len(jobs)} jobs")
            else:
                logger.error("✗ Meta: No jobs found")
            
            return success
            
        except Exception as e:
            logger.error(f"✗ Meta test failed: {e}")
            self.results['Meta'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False
            
        finally:
            await scraper.teardown()
    
    async def test_nvidia_scraper(self):
        """Test Nvidia scraper using Eightfold API."""
        logger.info("=" * 80)
        logger.info("Testing Nvidia Scraper (Eightfold API)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "Nvidia",
            "website": "https://www.nvidia.com",
            "careers_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
            "industry": "Technology"
        }
        
        scraping_config = {
            "scraper_type": "api",
            "api_endpoint": "https://nvidia.eightfold.ai/api/pcsx/search",
            "api_method": "GET",
            "pagination_type": "offset",
            "pagination_params": {
                "offset_param": "start",
                "limit_param": None,
                "page_size": 10,
                "max_pages": 5
            },
            "query_params": {
                "domain": "nvidia.com",
                "query": "",
                "location": "Israel"
            },
            "response_structure": {
                "jobs_key": "data.positions",
                "total_key": None
            },
            "wait_time": 1
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            success = len(jobs) > 0
            self.results['Nvidia'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            
            if success:
                logger.success(f"✓ Nvidia: Found {len(jobs)} jobs")
            else:
                logger.error("✗ Nvidia: No jobs found")
            
            return success
            
        except Exception as e:
            logger.error(f"✗ Nvidia test failed: {e}")
            self.results['Nvidia'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False
            
        finally:
            await scraper.teardown()
    
    async def test_wix_scraper(self):
        """Test Wix scraper using SmartRecruiters API."""
        logger.info("=" * 80)
        logger.info("Testing Wix Scraper (SmartRecruiters API)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "Wix",
            "website": "https://www.wix.com",
            "careers_url": "https://www.wix.com/jobs",
            "industry": "Technology"
        }
        
        scraping_config = {
            "scraper_type": "api",
            "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Wix2/postings",
            "api_method": "GET",
            "pagination_type": "offset",
            "pagination_params": {
                "offset_param": "offset",
                "limit_param": "limit",
                "page_size": 100,
                "max_pages": 3
            },
            "response_structure": {
                "jobs_key": "content",
                "total_key": "totalFound"
            },
            "wait_time": 1
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            success = len(jobs) > 0
            self.results['Wix'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            
            if success:
                logger.success(f"✓ Wix: Found {len(jobs)} jobs")
            else:
                logger.error("✗ Wix: No jobs found")
            
            return success
            
        except Exception as e:
            logger.error(f"✗ Wix test failed: {e}")
            self.results['Wix'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False
            
        finally:
            await scraper.teardown()
    
    async def test_salesforce_scraper(self):
        """Test Salesforce scraper using Workday API."""
        logger.info("=" * 80)
        logger.info("Testing Salesforce Scraper (Workday API)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "Salesforce",
            "website": "https://www.salesforce.com",
            "careers_url": "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site",
            "industry": "Technology"
        }
        
        scraping_config = {
            "scraper_type": "workday",
            "api_endpoint": "https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/External_Career_Site/jobs",
            "api_method": "POST",
            "pagination_type": "offset",
            "pagination_params": {
                "offset_param": "offset",
                "limit_param": "limit",
                "page_size": 20,
                "max_pages": 3
            },
            "wait_time": 1
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            success = len(jobs) > 0
            self.results['Salesforce'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            
            if success:
                logger.success(f"✓ Salesforce: Found {len(jobs)} jobs")
            else:
                logger.error("✗ Salesforce: No jobs found")
            
            return success
            
        except Exception as e:
            logger.error(f"✗ Salesforce test failed: {e}")
            self.results['Salesforce'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False
            
        finally:
            await scraper.teardown()
    
    async def test_datadog_scraper(self):
        """Test Datadog scraper using Greenhouse API."""
        logger.info("=" * 80)
        logger.info("Testing Datadog Scraper (Greenhouse API)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "Datadog",
            "website": "https://www.datadoghq.com",
            "careers_url": "https://www.datadoghq.com/careers",
            "industry": "Technology"
        }
        
        scraping_config = {
            "scraper_type": "api",
            "pagination_type": "none",
            "requires_js": False,
            "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/datadog/jobs",
            "api_method": "GET",
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            success = len(jobs) > 0
            self.results['Datadog'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            
            if success:
                logger.success(f"✓ Datadog: Found {len(jobs)} jobs")
            else:
                logger.error("✗ Datadog: No jobs found")
            
            return success
            
        except Exception as e:
            logger.error(f"✗ Datadog test failed: {e}")
            self.results['Datadog'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False
            
        finally:
            await scraper.teardown()
    
    async def test_unity_scraper(self):
        """Test Unity scraper using Greenhouse API."""
        logger.info("=" * 80)
        logger.info("Testing Unity Scraper (Greenhouse API)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "Unity",
            "website": "https://unity.com",
            "careers_url": "https://careers.unity.com",
            "industry": "Technology"
        }
        
        scraping_config = {
            "scraper_type": "api",
            "pagination_type": "none",
            "requires_js": False,
            "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/unity3d/jobs",
            "api_method": "GET",
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            
            success = len(jobs) > 0
            self.results['Unity'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }
            
            if success:
                logger.success(f"✓ Unity: Found {len(jobs)} jobs")
            else:
                logger.error("✗ Unity: No jobs found")
            
            return success
            
        except Exception as e:
            logger.error(f"✗ Unity test failed: {e}")
            self.results['Unity'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False
            
        finally:
            await scraper.teardown()
    
    async def test_appsflyer_scraper(self):
        """Test AppsFlyer scraper (Greenhouse API)."""
        logger.info("=" * 80)
        logger.info("Testing AppsFlyer Scraper (Greenhouse API)")
        logger.info("=" * 80)
        
        company_config = {
            "name": "AppsFlyer",
            "website": "https://www.appsflyer.com",
            "careers_url": "https://careers.appsflyer.com/",
            "industry": "Technology",
            "location_filter": {
                "enabled": True,
                "countries": ["Israel"],
                "match_keywords": ["Israel", "Tel Aviv", "Herzliya", "Haifa", "Jerusalem", "Raanana", "Beer Sheva", "IL,"]
            }
        }
        
        scraping_config = {
            "scraper_type": "api",
            "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/appsflyer/jobs",
            "api_method": "GET",
            "pagination_type": "none",
            "response_structure": {
                "jobs_key": "jobs",
                "total_key": None
            },
            "wait_time": 1
        }
        
        scraper = PlaywrightScraper(company_config, scraping_config)
        
        try:
            await scraper.setup()
            jobs = await scraper.scrape()
            logger.success(f"AppsFlyer: Scraped {len(jobs)} jobs")
            
            if jobs:
                logger.info(f"Sample job: {jobs[0].get('title')} - {jobs[0].get('location')}")
            
            self.results['AppsFlyer'] = {
                'success': len(jobs) > 0,
                'jobs_count': len(jobs),
            }
            return len(jobs) > 0
        except Exception as e:
            logger.error(f"AppsFlyer scraper failed: {e}")
            self.results['AppsFlyer'] = {
                'success': False,
                'jobs_count': 0,
            }
            return False
        finally:
            await scraper.teardown()

    async def test_jfrog_scraper(self):
        """Test JFrog scraper (Greenhouse API)."""
        logger.info("=" * 80)
        logger.info("Testing JFrog Scraper (Greenhouse API)")
        logger.info("=" * 80)

        # Load config from companies.yaml
        with open('config/companies.yaml', 'r') as f:
            config = yaml.safe_load(f)

        jfrog_config = next(
            (c for c in config['companies'] if c['name'] == 'JFrog'),
            None
        )

        if not jfrog_config:
            logger.error("JFrog not found in config")
            return False

        company_config = {
            "name": jfrog_config['name'],
            "website": jfrog_config['website'],
            "careers_url": jfrog_config['careers_url'],
            "industry": jfrog_config.get('industry', 'Technology'),
            "location_filter": jfrog_config.get('location_filter', {})
        }

        scraping_config = jfrog_config.get('scraping_config', {})

        scraper = PlaywrightScraper(company_config, scraping_config)

        try:
            await scraper.setup()
            jobs = await scraper.scrape()

            success = len(jobs) > 0
            self.results['JFrog'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }

            if success:
                logger.success(f"✓ JFrog: Found {len(jobs)} jobs")
                if jobs:
                    logger.info(f"Sample job: {jobs[0].get('title')} - {jobs[0].get('location')}")
            else:
                logger.error("✗ JFrog: No jobs found")

            return success

        except Exception as e:
            logger.error(f"✗ JFrog test failed: {e}")
            self.results['JFrog'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False

        finally:
            await scraper.teardown()

    async def test_riskified_scraper(self):
        """Test Riskified scraper (Greenhouse API)."""
        logger.info("=" * 80)
        logger.info("Testing Riskified Scraper (Greenhouse API)")
        logger.info("=" * 80)

        company_config = {
            "name": "Riskified",
            "website": "https://www.riskified.com",
            "careers_url": "https://www.riskified.com/careers/",
            "industry": "Technology",
            "location_filter": {
                "enabled": True,
                "countries": ["Israel", "United States"],
                "match_keywords": ["Israel", "Tel Aviv", "Jerusalem", "Haifa", "IL,", "Remote", "New York"]
            }
        }

        scraping_config = {
            "scraper_type": "api",
            "pagination_type": "none",
            "requires_js": False,
            "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/riskified/jobs",
            "api_method": "GET",
        }

        scraper = PlaywrightScraper(company_config, scraping_config)

        try:
            await scraper.setup()
            jobs = await scraper.scrape()

            success = len(jobs) > 0
            self.results['Riskified'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }

            if success:
                logger.success(f"✓ Riskified: Found {len(jobs)} jobs")
                if jobs:
                    logger.info(f"Sample job: {jobs[0].get('title')} - {jobs[0].get('location')}")
            else:
                logger.error("✗ Riskified: No jobs found")

            return success

        except Exception as e:
            logger.error(f"✗ Riskified test failed: {e}")
            self.results['Riskified'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False

        finally:
            await scraper.teardown()

    async def test_papaya_gaming_scraper(self):
        """Test Papaya Gaming scraper (Comeet API)."""
        logger.info("=" * 80)
        logger.info("Testing Papaya Gaming Scraper (Comeet API)")
        logger.info("=" * 80)

        company_config = {
            "name": "Papaya Gaming",
            "website": "https://www.papaya.com",
            "careers_url": "https://www.papaya.com/contact-us",
            "industry": "Technology",
            "location_filter": {
                "enabled": True,
                "countries": ["Israel", "Poland"],
                "match_keywords": ["Israel", "Tel Aviv", "Tel-Aviv", "Jerusalem", "Haifa", "IL,", "Poland", "Warsaw"]
            }
        }

        scraping_config = {
            "scraper_type": "api",
            "pagination_type": "none",
            "requires_js": True,
            "api_endpoint": "https://www.comeet.co/careers-api/2.0/company/46.00B/positions?token=64B25C264B12E112E102C0D2C0D64B25C2",
            "api_method": "GET",
        }

        scraper = PlaywrightScraper(company_config, scraping_config)

        try:
            await scraper.setup()
            jobs = await scraper.scrape()

            success = len(jobs) > 0
            self.results['Papaya Gaming'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }

            if success:
                logger.success(f"✓ Papaya Gaming: Found {len(jobs)} jobs")
                if jobs:
                    logger.info(f"Sample job: {jobs[0].get('title')} - {jobs[0].get('location')}")
            else:
                logger.error("✗ Papaya Gaming: No jobs found")

            return success

        except Exception as e:
            logger.error(f"✗ Papaya Gaming test failed: {e}")
            self.results['Papaya Gaming'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False

        finally:
            await scraper.teardown()

    async def test_checkpoint_scraper(self):
        """Test Check Point scraper (Custom System)."""
        logger.info("=" * 80)
        logger.info("Testing Check Point Scraper (Custom System)")
        logger.info("=" * 80)

        company_config = {
            "name": "Check Point",
            "website": "https://www.checkpoint.com",
            "careers_url": "https://careers.checkpoint.com/",
            "industry": "Cybersecurity",
            "location_filter": {
                "enabled": True,
                "countries": ["Israel", "United States"],
                "match_keywords": ["Israel", "Tel Aviv", "Ramat Gan", "Haifa", "Jerusalem", "IL,", "Remote", "United States", "US"]
            }
        }

        scraping_config = {
            "scraper_type": "playwright",
            "pagination_type": "custom",
            "requires_js": True,
            "careers_url": "https://careers.checkpoint.com/index.php?m=cpcareers&a=search",
            "wait_time": 3,
            "selectors": {
                "job_list": ".job-item, .position-item",
                "job_item": ".job-link, .position-link"
            }
        }

        scraper = PlaywrightScraper(company_config, scraping_config)

        try:
            await scraper.setup()
            jobs = await scraper.scrape()

            success = len(jobs) > 0
            self.results['Check Point'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }

            if success:
                logger.success(f"✓ Check Point: Found {len(jobs)} jobs")
                if jobs:
                    logger.info(f"Sample job: {jobs[0].get('title')} - {jobs[0].get('location')}")
            else:
                logger.warning("⚠ Check Point: No jobs found (may need custom scraper implementation)")

            return success

        except Exception as e:
            logger.error(f"✗ Check Point test failed: {e}")
            self.results['Check Point'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False

        finally:
            await scraper.teardown()

    async def test_lumen_scraper(self):
        """Test Lumen scraper (Custom JSON API - Comeet-based)."""
        logger.info("=" * 80)
        logger.info("Testing Lumen Scraper (Custom JSON API)")
        logger.info("=" * 80)

        company_config = {
            "name": "Lumen",
            "website": "https://www.lumen.me",
            "careers_url": "https://www.lumen.me/careers",
            "industry": "Health Tech",
            "location_filter": {
                "enabled": True,
                "countries": ["Israel"],
                "match_keywords": ["Israel", "Tel Aviv", "IL"]
            }
        }

        scraping_config = {
            "scraper_type": "api",
            "pagination_type": "none",
            "requires_js": False,
            "api_endpoint": "https://www.lumen.me/careers.json",
            "api_method": "GET",
        }

        scraper = PlaywrightScraper(company_config, scraping_config)

        try:
            await scraper.setup()
            jobs = await scraper.scrape()

            success = len(jobs) > 0
            self.results['Lumen'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }

            if success:
                logger.success(f"✓ Lumen: Found {len(jobs)} jobs")
                if jobs:
                    logger.info(f"Sample job: {jobs[0].get('title')} - {jobs[0].get('location')}")
            else:
                logger.error("✗ Lumen: No jobs found")

            return success

        except Exception as e:
            logger.error(f"✗ Lumen test failed: {e}")
            self.results['Lumen'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False

        finally:
            await scraper.teardown()

    async def test_gong_scraper(self):
        """Test Gong scraper (Greenhouse API)."""
        logger.info("=" * 80)
        logger.info("Testing Gong Scraper (Greenhouse API)")
        logger.info("=" * 80)

        # Load config from companies.yaml

        with open('config/companies.yaml', 'r') as f:
            config = yaml.safe_load(f)

        gong_config = next(
            (c for c in config['companies'] if c['name'] == 'Gong'),
            None
        )

        if not gong_config:
            logger.error("Gong not found in config")
            return False

        company_config = {
            "name": gong_config['name'],
            "website": gong_config['website'],
            "careers_url": gong_config['careers_url'],
            "industry": gong_config.get('industry', 'Technology'),
            "location_filter": gong_config.get('location_filter', {})
        }
    
        scraping_config = gong_config.get('scraping_config', {})

        scraper = PlaywrightScraper(company_config, scraping_config)

        try:
            await scraper.setup()
            jobs = await scraper.scrape()

            success = len(jobs) > 0
            self.results['Gong'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }

            if success:
                logger.success(f"✓ Gong: Found {len(jobs)} jobs")
                if jobs:
                    logger.info(f"Sample job: {jobs[0].get('title')} - {jobs[0].get('location')}")
            else:
                logger.error("✗ Gong: No jobs found")

            return success

        except Exception as e:
            logger.error(f"✗ Gong test failed: {e}")
            self.results['Gong'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False

        finally:
            await scraper.teardown()


    async def test_booking_scraper(self):
        """Test Booking.com scraper (Jibe API)."""
        logger.info("=" * 80)
        logger.info("Testing Booking.com Scraper (Jibe API)")
        logger.info("=" * 80)

        company_config = {
            "name": "Booking.com",
            "website": "https://www.booking.com",
            "careers_url": "https://jobs.booking.com/booking/jobs",
            "industry": "Travel Technology",
            "location_filter": {
                "enabled": True,
                "countries": ["Israel", "United States"],
                "match_keywords": ["Israel", "Tel Aviv", "Ramat Gan", "Haifa", "Jerusalem", "IL", "Remote", "United States", "US", "New York", "San Francisco", "Austin", "Chicago", "Seattle"]
            }
        }

        scraping_config = {
            "scraper_type": "api",
            "pagination_type": "none",
            "requires_js": False,
            "api_endpoint": "https://jobs.booking.com/api/jobs",
            "api_method": "GET",
            "api_params": {
                "page": 1,
                "limit": 100
            }
        }

        scraper = PlaywrightScraper(company_config, scraping_config)

        try:
            await scraper.setup()
            jobs = await scraper.scrape()

            success = len(jobs) > 0
            self.results['Booking.com'] = {
                'success': success,
                'jobs_count': len(jobs),
                'sample_jobs': jobs[:3] if jobs else []
            }

            if success:
                logger.success(f"✓ Booking.com: Found {len(jobs)} jobs")
                if jobs:
                    logger.info(f"Sample job: {jobs[0].get('title')} - {jobs[0].get('location')}")
            else:
                logger.error("✗ Booking.com: No jobs found")

            return success

        except Exception as e:
            logger.error(f"✗ Booking.com test failed: {e}")
            self.results['Booking.com'] = {
                'success': False,
                'jobs_count': 0,
                'sample_jobs': []
            }
            return False

        finally:
            await scraper.teardown()


    async def test_apple_scraper(self):
        """Test Apple scraper (Embedded JSON extraction)."""
        logger.info("=" * 80)
        logger.info("Testing Apple Scraper (Embedded JSON)")
        logger.info("=" * 80)

        
        url = "https://jobs.apple.com/en-il/search?location=israel-ISR"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        try:
            # Fetch HTML
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse jobs
            parser = AppleParser()
            jobs = parser.parse(response.text)
            
            logger.info(f"Total jobs found: {len(jobs)}")
            
            # Apply location filter
            location_keywords = ["Israel", "Herzliya", "Haifa", "Tel Aviv", "IL", "Remote", 
                                "United States", "US", "California", "Texas", "New York", 
                                "Washington", "Cupertino", "Austin", "Seattle"]
            
            filtered_jobs = []
            for job in jobs:
                location = job.get('location', '')
                if any(keyword.lower() in location.lower() for keyword in location_keywords):
                    filtered_jobs.append(job)
            
            logger.info(f"Jobs after location filter: {len(filtered_jobs)}")
            
            success = len(filtered_jobs) > 0
            self.results['Apple'] = {
                'success': success,
                'jobs_count': len(jobs),
                'filtered_count': len(filtered_jobs)
            }
            
            if filtered_jobs:
                logger.info("\nSample jobs:")
                for i, job in enumerate(filtered_jobs[:5], 1):
                    logger.info(f"{i}. {job.get('title', 'N/A')} - {job.get('location', 'N/A')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Apple scraper failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['Apple'] = {
                'success': False,
                'jobs_count': 0,
                'filtered_count': 0
            }
            return False


    async def test_microsoft_scraper(self):
        """Test Microsoft scraper (API-based with pagination)."""
        logger.info("=" * 80)
        logger.info("Testing Microsoft Scraper (API)")
        logger.info("=" * 80)
        
        base_url = "https://apply.careers.microsoft.com/api/pcsx/search"
        params = {
            'domain': 'microsoft.com',
            'query': '',
            'location': 'israel',
            'start': 0
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        try:
            all_jobs = []
            parser = MicrosoftParser()
            page = 0
            page_size = 10
            
            while True:
                params['start'] = page * page_size
                
                logger.info(f"Fetching page {page + 1} (start={params['start']})")
                response = requests.get(base_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Parse jobs from this page
                jobs = parser.parse(response.text)
                
                if not jobs:
                    break
                
                all_jobs.extend(jobs)
                logger.info(f"  Found {len(jobs)} jobs on page {page + 1}")
                
                # Check if there are more pages
                import json
                data = json.loads(response.text)
                total_count = data.get('data', {}).get('count', 0)
                
                if len(all_jobs) >= total_count:
                    break
                
                page += 1
                
                # Safety limit
                if page >= 10:
                    logger.warning("Reached page limit (10)")
                    break
            
            logger.info(f"\nTotal jobs found: {len(all_jobs)}")
            
            success = len(all_jobs) > 0
            self.results['Microsoft'] = {
                'success': success,
                'jobs_count': len(all_jobs),
                'filtered_count': len(all_jobs)
            }
            
            if all_jobs:
                logger.info("\nSample jobs:")
                for i, job in enumerate(all_jobs[:5], 1):
                    logger.info(f"{i}. {job.get('title', 'N/A')}")
                    logger.info(f"   Location: {job.get('location', 'N/A')}")
                    logger.info(f"   Department: {job.get('department', 'N/A')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Microsoft scraper failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['Microsoft'] = {
                'success': False,
                'jobs_count': 0,
                'filtered_count': 0
            }
            return False


    async def test_google_scraper(self):
        """Test Google scraper (AF_initDataCallback extraction)."""
        logger.info("=" * 80)
        logger.info("Testing Google Scraper (Embedded Data)")
        logger.info("=" * 80)
        

        url = "https://www.google.com/about/careers/applications/jobs/results/?location=Israel"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        try:
            # Fetch HTML
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse jobs
            parser = GoogleParser()
            jobs = parser.parse(response.text)
            
            logger.info(f"Total jobs found: {len(jobs)}")
            
            success = len(jobs) > 0
            self.results['Google'] = {
                'success': success,
                'jobs_count': len(jobs),
                'filtered_count': len(jobs)
            }
            
            if jobs:
                logger.info("\nSample jobs:")
                for i, job in enumerate(jobs[:5], 1):
                    logger.info(f"{i}. {job.get('title', 'N/A')}")
                    logger.info(f"   Location: {job.get('location', 'N/A')}")
                    logger.info(f"   Company: {job.get('company', 'N/A')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Google scraper failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['Google'] = {
                'success': False,
                'jobs_count': 0,
                'filtered_count': 0
            }
            return False

    
    async def test_intel_scraper(self):
        """Test Intel scraper (Workday API)."""
        logger.info("=" * 80)
        logger.info("Testing Intel Scraper (Workday API)")
        logger.info("=" * 80)

        
        api_url = "https://intel.wd1.myworkdayjobs.com/wday/cxs/intel/External/jobs"
        base_url = "https://intel.wd1.myworkdayjobs.com/en-US/External"
        
        try:
            # Fetch jobs
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            payload = {
                "limit": 20,
                "offset": 0,
                "searchText": ""
            }
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            job_postings = data.get('jobPostings', [])
            
            # Parse jobs
            parser = WorkdayParser(base_url=base_url)
            jobs = []
            for job_data in job_postings:
                parsed_job = parser.parse(job_data)
                if parsed_job:
                    jobs.append(parsed_job)
            
            # Filter for Israel
            israel_jobs = [
                job for job in jobs 
                if 'israel' in job.get('location', '').lower()
            ]
            
            logger.info(f"Total jobs found: {len(jobs)}")
            logger.info(f"Israel jobs found: {len(israel_jobs)}")
            
            success = len(jobs) > 0
            self.results['Intel'] = {
                'success': success,
                'jobs_count': len(jobs),
                'filtered_count': len(israel_jobs)
            }
            
            if israel_jobs:
                logger.info("\nSample Israel jobs:")
                for i, job in enumerate(israel_jobs[:5], 1):
                    logger.info(f"{i}. {job.get('title', 'N/A')}")
                    logger.info(f"   Location: {job.get('location', 'N/A')}")
                    logger.info(f"   URL: {job.get('job_url', 'N/A')[:80]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"Intel scraper failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['Intel'] = {
                'success': False,
                'jobs_count': 0,
                'filtered_count': 0
            }
            return False


    async def test_fiverr_scraper(self):
        """Test Fiverr scraper with stealth mode for bot protection."""
        logger.info("\n" + "=" * 80)
        logger.info("Testing Fiverr Scraper (with stealth mode)")
        logger.info("=" * 80)
        
        try:
            # Load company config
            with open('config/companies.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            fiverr_config = next(
                (c for c in config['companies'] if c['name'] == 'Fiverr'),
                None
            )
            
            if not fiverr_config:
                logger.error("Fiverr configuration not found")
                self.results['Fiverr'] = {
                    'success': False,
                    'jobs_count': 0,
                    'filtered_count': 0
                }
                return False
            
            logger.info(f"Scraping: {fiverr_config['careers_url']}")
            logger.info("Note: Using stealth mode to bypass bot protection")
            
            # Create scraper with stealth mode
            scraper = PlaywrightScraper(
                company_config=fiverr_config,
                scraping_config=fiverr_config['scraping_config']
            )
            
            # Setup Playwright and scrape jobs
            await scraper.setup()
            jobs = await scraper.scrape()
            await scraper.teardown()
            
            # Filter for Israel
            israel_jobs = [
                job for job in jobs 
                if any(keyword.lower() in job.get('location', '').lower() 
                      for keyword in ['israel', 'tel aviv', 'herzliya', 'haifa'])
            ]
            
            logger.info(f"Total jobs found: {len(jobs)}")
            logger.info(f"Israel jobs found: {len(israel_jobs)}")
            
            success = len(jobs) > 0
            self.results['Fiverr'] = {
                'success': success,
                'jobs_count': len(jobs),
                'filtered_count': len(israel_jobs)
            }
            
            if israel_jobs:
                logger.info("\nSample Israel jobs:")
                for i, job in enumerate(israel_jobs[:5], 1):
                    logger.info(f"{i}. {job.get('title', 'N/A')}")
                    logger.info(f"   Location: {job.get('location', 'N/A')}")
                    logger.info(f"   Company: {job.get('company', 'N/A')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Fiverr scraper failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['Fiverr'] = {
                'success': False,
                'jobs_count': 0,
                'filtered_count': 0
            }
            return False

    async def test_sentinelone_scraper(self):

        """Test SentinelOne scraper (Greenhouse API)."""
        logger.info("\n" + "=" * 80)
        logger.info("Testing SentinelOne Scraper (Greenhouse API)")
        logger.info("=" * 80)

        try:
            # Load company config
            with open('config/companies.yaml', 'r') as f:
                config = yaml.safe_load(f)

            sentinelone_config = next(
                (c for c in config['companies'] if c['name'] == 'SentinelOne'),
                None
            )

            if not sentinelone_config:
                logger.error("SentinelOne configuration not found")
                self.results['SentinelOne'] = {
                    'success': False,
                    'jobs_count': 0,
                    'filtered_count': 0
                }
                return False

            logger.info(f"Scraping: {sentinelone_config['careers_url']}")

            # Create scraper
            scraper = PlaywrightScraper(
                company_config=sentinelone_config,
                scraping_config=sentinelone_config['scraping_config']
            )

            # Scrape jobs (API-based, no setup needed)
            jobs = await scraper.scrape()

            # Filter for Israel and US
            israel_jobs = [
                job for job in jobs
                if any(keyword.lower() in job.get('location', '').lower()
                       for keyword in ['israel', 'tel aviv'])
            ]

            us_jobs = [
                job for job in jobs
                if any(keyword.lower() in job.get('location', '').lower()
                       for keyword in ['united states', 'california', 'new york', 'remote'])
            ]

            logger.info(f"Total jobs found: {len(jobs)}")
            logger.info(f"Israel jobs found: {len(israel_jobs)}")
            logger.info(f"US jobs found: {len(us_jobs)}")

            success = len(jobs) > 0
            self.results['SentinelOne'] = {
                'success': success,
                'jobs_count': len(jobs),
                'filtered_count': len(israel_jobs) + len(us_jobs)
            }

            if israel_jobs:
                logger.info("\nSample Israel jobs:")
                for i, job in enumerate(israel_jobs[:5], 1):
                    logger.info(f"{i}. {job.get('title', 'N/A')}")
                    logger.info(f"   Location: {job.get('location', 'N/A')}")
                    logger.info(f"   URL: {job.get('url', 'N/A')}")

            return success

        except Exception as e:
            logger.error(f"SentinelOne scraper failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['SentinelOne'] = {
                'success': False,
                'jobs_count': 0,
                'filtered_count': 0
            }
            return False


    async def test_redis_scraper(self):
        """Test Redis scraper (Greenhouse API)."""
        logger.info("\n" + "=" * 80)
        logger.info("Testing Redis Scraper (Greenhouse API)")
        logger.info("=" * 80)

        try:
            # Load company config
            with open('config/companies.yaml', 'r') as f:
                config = yaml.safe_load(f)

            redis_config = next(
                (c for c in config['companies'] if c['name'] == 'Redis'),
                None
            )

            if not redis_config:
                logger.error("Redis configuration not found")
                self.results['Redis'] = {
                    'success': False,
                    'jobs_count': 0,
                    'filtered_count': 0
                }
                return False

            logger.info(f"Scraping: {redis_config['careers_url']}")

            # Create scraper
            scraper = PlaywrightScraper(
                company_config=redis_config,
                scraping_config=redis_config['scraping_config']
            )

            # Scrape jobs (API-based, no setup needed)
            jobs = await scraper.scrape()

            # Filter for Israel and US
            israel_jobs = [
                job for job in jobs
                if any(keyword.lower() in job.get('location', '').lower()
                       for keyword in ['israel', 'tel aviv'])
            ]

            us_jobs = [
                job for job in jobs
                if any(keyword.lower() in job.get('location', '').lower()
                       for keyword in ['united states', 'california', 'new york', 'remote'])
            ]

            logger.info(f"Total jobs found: {len(jobs)}")
            logger.info(f"Israel jobs found: {len(israel_jobs)}")
            logger.info(f"US jobs found: {len(us_jobs)}")

            success = len(jobs) > 0
            self.results['Redis'] = {
                'success': success,
                'jobs_count': len(jobs),
                'filtered_count': len(israel_jobs) + len(us_jobs)
            }

            if israel_jobs:
                logger.info("\nSample Israel jobs:")
                for i, job in enumerate(israel_jobs[:5], 1):
                    logger.info(f"{i}. {job.get('title', 'N/A')}")
                    logger.info(f"   Location: {job.get('location', 'N/A')}")
                    logger.info(f"   URL: {job.get('url', 'N/A')}")

            return success

        except Exception as e:
            logger.error(f"Redis scraper failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['Redis'] = {
                'success': False,
                'jobs_count': 0,
                'filtered_count': 0
            }
            return False


    async def test_samsung_scraper(self):
        """Test Samsung scraper (Workday API)."""
        logger.info("\n" + "=" * 80)
        logger.info("Testing Samsung Scraper (Workday API)")
        logger.info("=" * 80)
        
        try:
            # Load company config
            with open('config/companies.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            samsung_config = next(
                (c for c in config['companies'] if c['name'] == 'Samsung'),
                None
            )
            
            if not samsung_config:
                logger.error("Samsung configuration not found")
                self.results['Samsung'] = {
                    'success': False,
                    'jobs_count': 0,
                    'filtered_count': 0
                }
                return False
            
            logger.info(f"Scraping: {samsung_config['careers_url']}")
            
            # Create scraper
            scraper = PlaywrightScraper(
                company_config=samsung_config,
                scraping_config=samsung_config['scraping_config']
            )
            
            # Scrape jobs (API-based, no setup needed)
            jobs = await scraper.scrape()
            
            # Filter for Israel and US
            israel_jobs = [
                job for job in jobs 
                if any(keyword.lower() in job.get('location', '').lower() 
                      for keyword in ['israel', 'tel aviv', 'petah tikva'])
            ]
            
            us_jobs = [
                job for job in jobs 
                if any(keyword.lower() in job.get('location', '').lower() 
                      for keyword in ['united states', 'california', 'new york', 'texas', 'remote'])
            ]
            
            logger.info(f"Total jobs found: {len(jobs)}")
            logger.info(f"Israel jobs found: {len(israel_jobs)}")
            logger.info(f"US jobs found: {len(us_jobs)}")
            
            success = len(jobs) > 0
            self.results['Samsung'] = {
                'success': success,
                'jobs_count': len(jobs),
                'filtered_count': len(israel_jobs) + len(us_jobs)
            }
            
            if israel_jobs:
                logger.info("\nSample Israel jobs:")
                for i, job in enumerate(israel_jobs[:5], 1):
                    logger.info(f"{i}. {job.get('title', 'N/A')}")
                    logger.info(f"   Location: {job.get('location', 'N/A')}")
                    logger.info(f"   URL: {job.get('url', 'N/A')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Samsung scraper failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['Samsung'] = {
                'success': False,
                'jobs_count': 0,
                'filtered_count': 0
            }
            return False

    async def test_intuit_scraper(self):
        """Test Intuit scraper (Phenom People platform)."""
        logger.info("\n" + "=" * 80)
        logger.info("Testing Intuit Scraper (Phenom People)")
        logger.info("=" * 80)
        
        try:
            # Load company config
            with open('config/companies.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            intuit_config = next(
                (c for c in config['companies'] if c['name'] == 'Intuit'),
                None
            )
            
            if not intuit_config:
                logger.error("Intuit configuration not found")
                self.results['Intuit'] = {
                    'success': False,
                    'jobs_count': 0,
                    'filtered_count': 0
                }
                return False
            
            logger.info(f"Scraping: {intuit_config['careers_url']}")
            
            # Create scraper
            scraper = PlaywrightScraper(
                company_config=intuit_config,
                scraping_config=intuit_config['scraping_config']
            )
            
            # Setup and scrape jobs
            await scraper.setup()
            jobs = await scraper.scrape()
            await scraper.teardown()
            
            # Filter for Israel and US
            israel_jobs = [
                job for job in jobs 
                if any(keyword.lower() in job.get('location', '').lower() 
                      for keyword in ['israel', 'tel aviv', 'petah tikva'])
            ]
            
            us_jobs = [
                job for job in jobs 
                if any(keyword.lower() in job.get('location', '').lower() 
                      for keyword in ['united states', 'california', 'new york', 'texas', 'remote'])
            ]
            
            logger.info(f"Total jobs found: {len(jobs)}")
            logger.info(f"Israel jobs found: {len(israel_jobs)}")
            logger.info(f"US jobs found: {len(us_jobs)}")
            
            success = len(jobs) > 0
            self.results['Intuit'] = {
                'success': success,
                'jobs_count': len(jobs),
                'filtered_count': len(israel_jobs) + len(us_jobs)
            }
            
            if israel_jobs:
                logger.info("\nSample Israel jobs:")
                for i, job in enumerate(israel_jobs[:5], 1):
                    logger.info(f"{i}. {job.get('title', 'N/A')}")
                    logger.info(f"   Location: {job.get('location', 'N/A')}")
                    logger.info(f"   URL: {job.get('job_url', 'N/A')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Intuit scraper failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['Intuit'] = {
                'success': False,
                'jobs_count': 0,
                'filtered_count': 0
            }
            return False

    async def test_servicenow_scraper(self):
        """Test ServiceNow scraper (Custom platform)."""
        logger.info("\n" + "=" * 80)
        logger.info("Testing ServiceNow Scraper (Custom Platform)")
        logger.info("=" * 80)
        
        try:
            # Load company config
            with open('config/companies.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            servicenow_config = next(
                (c for c in config['companies'] if c['name'] == 'ServiceNow'),
                None
            )
            
            if not servicenow_config:
                logger.error("ServiceNow configuration not found")
                self.results['ServiceNow'] = {
                    'success': False,
                    'jobs_count': 0,
                    'filtered_count': 0
                }
                return False
            
            logger.info(f"Scraping: {servicenow_config['careers_url']}")
            
            # Create scraper
            scraper = PlaywrightScraper(
                company_config=servicenow_config,
                scraping_config=servicenow_config['scraping_config']
            )
            
            # Setup and scrape jobs
            await scraper.setup()
            jobs = await scraper.scrape()
            await scraper.teardown()
            
            # Filter for Israel and US
            israel_jobs = [
                job for job in jobs 
                if any(keyword.lower() in job.get('location', '').lower() 
                      for keyword in ['israel', 'tel aviv', 'petah tikva'])
            ]
            
            us_jobs = [
                job for job in jobs 
                if any(keyword.lower() in job.get('location', '').lower() 
                      for keyword in ['united states', 'california', 'new york', 'texas', 'remote'])
            ]
            
            logger.info(f"Total jobs found: {len(jobs)}")
            logger.info(f"Israel jobs found: {len(israel_jobs)}")
            logger.info(f"US jobs found: {len(us_jobs)}")
            
            success = len(jobs) > 0
            self.results['ServiceNow'] = {
                'success': success,
                'jobs_count': len(jobs),
                'filtered_count': len(israel_jobs) + len(us_jobs)
            }
            
            if israel_jobs:
                logger.info("\nSample Israel jobs:")
                for i, job in enumerate(israel_jobs[:5], 1):
                    logger.info(f"{i}. {job.get('title', 'N/A')}")
                    logger.info(f"   Location: {job.get('location', 'N/A')}")
                    logger.info(f"   URL: {job.get('job_url', 'N/A')}")
            
            return success
            
        except Exception as e:
            logger.error(f"ServiceNow scraper failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['ServiceNow'] = {
                'success': False,
                'jobs_count': 0,
                'filtered_count': 0
            }
            return False

    async def run_all_tests(self):
        """Run all company scraper tests."""
        logger.info("\n" + "=" * 80)
        logger.info("RUNNING ALL COMPANY SCRAPER TESTS")
        logger.info("=" * 80 + "\n")
        
        # Run all tests
        monday_result = await self.test_monday_scraper()
        wiz_result = await self.test_wiz_scraper()
        island_result = await self.test_island_scraper()
        eon_result = await self.test_eon_scraper()
        palo_alto_result = await self.test_palo_alto_scraper()
        amazon_result = await self.test_amazon_scraper()
        meta_result = await self.test_meta_scraper()
        nvidia_result = await self.test_nvidia_scraper()
        wix_result = await self.test_wix_scraper()
        salesforce_result = await self.test_salesforce_scraper()
        datadog_result = await self.test_datadog_scraper()
        unity_result = await self.test_unity_scraper()
        checkpoint_result = await self.test_checkpoint_scraper()
        lumen_result = await self.test_lumen_scraper()
        gong_result = await self.test_gong_scraper()
        booking_result = await self.test_booking_scraper()
        jfrog_result = await self.test_jfrog_scraper()
        riskified_result = await self.test_riskified_scraper()
        papaya_gaming_result = await self.test_papaya_gaming_scraper()
        appsflyer_result = await self.test_appsflyer_scraper()
        apple_result = await self.test_apple_scraper()
        microsoft_result = await self.test_microsoft_scraper()
        intel_result = await self.test_intel_scraper()
        google_result = await self.test_google_scraper()
        sentinelone_result = await self.test_sentinelone_scraper()
        redis_result = await self.test_redis_scraper()
        samsung_result = await self.test_samsung_scraper()
        intuit_result = await self.test_intuit_scraper()
        servicenow_result = await self.test_servicenow_scraper()

        # Print summary
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
        
        all_passed = all([
            monday_result, wiz_result, island_result, eon_result, 
            palo_alto_result, amazon_result, meta_result, nvidia_result,
            wix_result, salesforce_result, datadog_result, unity_result, appsflyer_result,
            jfrog_result, riskified_result, papaya_gaming_result, checkpoint_result, lumen_result, gong_result,\
            booking_result, apple_result, microsoft_result, google_result, intel_result,
        sentinelone_result, redis_result, samsung_result, intuit_result, servicenow_result])
        
        if all_passed:
            logger.success("\n✓ ALL TESTS PASSED")
        else:
            logger.error("\n✗ SOME TESTS FAILED")
        
        return all_passed

async def main():
    """Main function."""
    test_suite = CompanyScraperTests()
    all_passed = await test_suite.run_all_tests()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

    
    
    
    
    
    

