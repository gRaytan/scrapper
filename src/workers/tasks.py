"""
Celery tasks for background job processing.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID

from celery import Task
from sqlalchemy import and_, or_

from src.workers.celery_app import celery_app
from src.orchestrator.scraper_orchestrator import ScraperOrchestrator
from src.storage.database import db
from src.models.job_position import JobPosition
from src.models.company import Company
from src.models.scraping_session import ScrapingSession
from src.storage.repositories.company_repo import CompanyRepository
from src.storage.repositories.job_repo import JobPositionRepository
from src.scrapers.playwright_scraper import PlaywrightScraper
from src.services.company_matching_service import CompanyMatchingService
from src.services.deduplication_service import JobDeduplicationService
from src.services.location_filter_service import location_filter
from src.utils.logger import logger
from config.settings import settings


@celery_app.task(bind=True, name='src.workers.tasks.run_daily_scraping', max_retries=3)
def run_daily_scraping(self: Task) -> Dict[str, Any]:
    """
    Daily scraping task - scrapes all active companies.

    This task runs at 2:00 AM UTC daily and scrapes all companies
    configured in companies.yaml with is_active=true.

    Returns:
        Dictionary with scraping statistics
    """
    try:
        logger.info("=" * 80)
        logger.info("Starting daily scraping job...")
        logger.info("=" * 80)

        start_time = datetime.utcnow()

        # Create orchestrator
        orchestrator = ScraperOrchestrator()

        # Run scraping for all active companies
        # Note: scrape_all_companies is async, so we need to run it in event loop
        results = asyncio.run(orchestrator.scrape_all_companies(incremental=False))

        # Calculate statistics
        total_companies = len(results)
        total_new = sum(r.get('jobs_new', 0) for r in results.values())
        total_updated = sum(r.get('jobs_updated', 0) for r in results.values())
        total_found = sum(r.get('jobs_found', 0) for r in results.values())
        total_removed = sum(r.get('jobs_removed', 0) for r in results.values())

        duration = (datetime.utcnow() - start_time).total_seconds()

        result = {
            'status': 'success',
            'started_at': start_time.isoformat(),
            'completed_at': datetime.utcnow().isoformat(),
            'duration_seconds': duration,
            'companies_scraped': total_companies,
            'total_jobs_found': total_found,
            'total_jobs_new': total_new,
            'total_jobs_updated': total_updated,
            'total_jobs_removed': total_removed,
            'company_results': results
        }

        logger.success("=" * 80)
        logger.success(f"Daily scraping completed successfully!")
        logger.success(f"  Companies: {total_companies}")
        logger.success(f"  Jobs found: {total_found}")
        logger.success(f"  New jobs: {total_new}")
        logger.success(f"  Updated jobs: {total_updated}")
        logger.success(f"  Removed jobs: {total_removed}")
        logger.success(f"  Duration: {duration:.2f}s")
        logger.success("=" * 80)

        # Trigger job processing task
        process_new_jobs.delay()

        return result

    except Exception as exc:
        logger.error(f"Daily scraping failed: {exc}")
        logger.exception(exc)

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))


@celery_app.task(bind=True, name='src.workers.tasks.scrape_single_company', max_retries=3)
def scrape_single_company(self: Task, company_name: str, incremental: bool = False) -> Dict[str, Any]:
    """
    Scrape a single company.

    Args:
        company_name: Name of the company to scrape
        incremental: If True, only fetch jobs from last 24 hours

    Returns:
        Dictionary with scraping statistics
    """
    try:
        logger.info(f"Starting scrape for {company_name} (incremental={incremental})")

        start_time = datetime.utcnow()
        orchestrator = ScraperOrchestrator()

        # Run scraping
        with db.get_session() as session:
            scraping_session = asyncio.run(
                orchestrator.scrape_company(company_name, session, incremental)
            )

            # Extract data while session is still active
            session_id = str(scraping_session.id)
            jobs_found = scraping_session.jobs_found
            jobs_new = scraping_session.jobs_new
            jobs_updated = scraping_session.jobs_updated
            jobs_removed = scraping_session.jobs_removed

        duration = (datetime.utcnow() - start_time).total_seconds()

        result = {
            'status': 'success',
            'company_name': company_name,
            'session_id': session_id,
            'started_at': start_time.isoformat(),
            'completed_at': datetime.utcnow().isoformat(),
            'duration_seconds': duration,
            'jobs_found': jobs_found,
            'jobs_new': jobs_new,
            'jobs_updated': jobs_updated,
            'jobs_removed': jobs_removed,
        }

        logger.success(
            f"Scraping completed for {company_name}: "
            f"{jobs_new} new, "
            f"{jobs_updated} updated, "
            f"{jobs_removed} removed"
        )

        return result

    except Exception as exc:
        logger.error(f"Scraping failed for {company_name}: {exc}")
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))


@celery_app.task(bind=True, name='src.workers.tasks.process_new_jobs', max_retries=3)
def process_new_jobs(self: Task, hours: int = 24) -> Dict[str, Any]:
    """
    Process new jobs from the last N hours.

    This task is called after scraping completes. It matches new jobs
    against user alerts and creates notifications.

    Args:
        hours: Number of hours to look back for new jobs

    Returns:
        Dictionary with processing statistics
    """
    from sqlalchemy.orm import joinedload
    from src.services.job_matching_service import JobMatchingService

    try:
        logger.info(f"Processing new jobs from last {hours} hours...")

        with db.get_session() as session:
            # Get jobs created in the last N hours
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            new_jobs = session.query(JobPosition).filter(
                and_(
                    JobPosition.created_at >= cutoff,
                    JobPosition.is_active == True
                )
            ).options(joinedload(JobPosition.company)).all()

            if not new_jobs:
                logger.info("No new jobs to process")
                return {
                    'status': 'success',
                    'new_jobs_count': 0,
                    'hours': hours
                }

            # Group jobs by company for logging
            jobs_by_company = {}
            for job in new_jobs:
                company_name = job.company.name if job.company else 'Unknown'
                if company_name not in jobs_by_company:
                    jobs_by_company[company_name] = []
                jobs_by_company[company_name].append(job)

            # Log statistics
            logger.info(f"Found {len(new_jobs)} new jobs from {len(jobs_by_company)} companies:")
            for company_name, jobs in jobs_by_company.items():
                logger.info(f"  - {company_name}: {len(jobs)} jobs")

            # Match jobs against user alerts and create notifications
            matching_service = JobMatchingService(session)
            matching_result = matching_service.process_new_jobs(new_jobs)

            result = {
                'status': 'success',
                'new_jobs_count': len(new_jobs),
                'companies_count': len(jobs_by_company),
                'hours': hours,
                'jobs_by_company': {
                    company: len(jobs)
                    for company, jobs in jobs_by_company.items()
                },
                'matching': matching_result
            }

            logger.success(
                f"Processed {len(new_jobs)} new jobs, "
                f"created {matching_result.get('notifications_created', 0)} notifications "
                f"for {matching_result.get('users_notified', 0)} users"
            )
            return result

    except Exception as exc:
        logger.error(f"Job processing failed: {exc}")
        raise self.retry(exc=exc, countdown=600 * (2 ** self.request.retries))


@celery_app.task(bind=True, name='src.workers.tasks.cleanup_old_sessions', max_retries=2)
def cleanup_old_sessions(self: Task, days: int = 90) -> Dict[str, Any]:
    """
    Clean up old scraping sessions from the database.

    Removes scraping sessions older than N days to prevent database bloat.

    Args:
        days: Number of days to keep (default: 90)

    Returns:
        Dictionary with cleanup statistics
    """
    try:
        logger.info(f"Cleaning up scraping sessions older than {days} days...")

        with db.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)

            # Delete old sessions
            deleted_count = session.query(ScrapingSession).filter(
                ScrapingSession.created_at < cutoff
            ).delete()

            session.commit()

            result = {
                'status': 'success',
                'deleted_sessions': deleted_count,
                'cutoff_date': cutoff.isoformat(),
                'days': days
            }

            logger.success(f"Cleaned up {deleted_count} old scraping sessions")
            return result

    except Exception as exc:
        logger.error(f"Cleanup failed: {exc}")
        raise self.retry(exc=exc, countdown=600)


@celery_app.task(bind=True, name='src.workers.tasks.mark_stale_jobs_inactive', max_retries=2)
def mark_stale_jobs_inactive(
    self: Task,
    stale_days: Optional[int] = None,
    posted_cutoff_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    Mark jobs as inactive if they haven't been seen in recent scrapes OR if posted_date is older than cutoff.

    Jobs that haven't been updated in N days are likely no longer available
    and should be marked as inactive.

    Additionally, jobs with posted_date older than the cutoff are marked inactive.
    Jobs without posted_date are kept active (only deactivated based on last_seen_at).

    Args:
        stale_days: Number of days without updates before marking inactive (default: from config)
        posted_cutoff_days: Number of days since posted_date before marking inactive (default: from config)

    Returns:
        Dictionary with statistics
    """
    try:
        # Use config values if not provided
        stale_days = stale_days or settings.job_stale_days
        posted_cutoff_days = posted_cutoff_days or settings.job_posted_cutoff_days

        logger.info(
            f"Marking jobs inactive that haven't been updated in {stale_days} days "
            f"or posted >{posted_cutoff_days} days ago..."
        )

        with db.get_session() as session:
            cutoff_updated = datetime.utcnow() - timedelta(days=stale_days)
            cutoff_posted = datetime.utcnow() - timedelta(days=posted_cutoff_days)

            # Find active jobs that should be marked inactive:
            # 1. Haven't been seen recently (last_seen_at < cutoff)
            # 2. OR have posted_date older than cutoff
            # Note: Jobs without posted_date are only deactivated based on last_seen_at
            stale_jobs = session.query(JobPosition).filter(
                and_(
                    JobPosition.is_active == True,
                    or_(
                        JobPosition.last_seen_at < cutoff_updated,
                        and_(
                            JobPosition.posted_date.isnot(None),
                            JobPosition.posted_date < cutoff_posted
                        )
                    )
                )
            ).all()

            # Mark them as inactive
            for job in stale_jobs:
                job.is_active = False

            session.commit()

            result = {
                'status': 'success',
                'marked_inactive': len(stale_jobs),
                'cutoff_last_seen_date': cutoff_updated.isoformat(),
                'cutoff_posted_date': cutoff_posted.isoformat(),
                'stale_days': stale_days,
                'posted_cutoff_days': posted_cutoff_days
            }

            logger.success(f"Marked {len(stale_jobs)} stale jobs as inactive")
            return result

    except Exception as exc:
        logger.error(f"Mark stale jobs failed: {exc}")
        raise self.retry(exc=exc, countdown=600)


@celery_app.task(name='src.workers.tasks.get_scraping_stats')
def get_scraping_stats(days: int = 7) -> Dict[str, Any]:
    """
    Get scraping statistics for the last N days.

    Args:
        days: Number of days to look back (default: 7)

    Returns:
        Dictionary with statistics
    """
    try:
        with db.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)

            # Get all sessions from the last N days
            sessions = session.query(ScrapingSession).filter(
                ScrapingSession.created_at >= cutoff
            ).all()

            # Calculate statistics
            total_sessions = len(sessions)
            successful_sessions = sum(1 for s in sessions if s.status == 'completed')
            failed_sessions = sum(1 for s in sessions if s.status == 'failed')
            total_new_jobs = sum(s.jobs_new for s in sessions)
            total_updated_jobs = sum(s.jobs_updated for s in sessions)

            # Group by company
            by_company = {}
            for session in sessions:
                company_name = session.company.name
                if company_name not in by_company:
                    by_company[company_name] = {
                        'sessions': 0,
                        'successful': 0,
                        'failed': 0,
                        'new_jobs': 0,
                        'updated_jobs': 0
                    }

                by_company[company_name]['sessions'] += 1
                if session.status == 'completed':
                    by_company[company_name]['successful'] += 1
                elif session.status == 'failed':
                    by_company[company_name]['failed'] += 1
                by_company[company_name]['new_jobs'] += session.jobs_new
                by_company[company_name]['updated_jobs'] += session.jobs_updated

            result = {
                'days': days,
                'total_sessions': total_sessions,
                'successful_sessions': successful_sessions,
                'failed_sessions': failed_sessions,
                'success_rate': (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0,
                'total_new_jobs': total_new_jobs,
                'total_updated_jobs': total_updated_jobs,
                'by_company': by_company
            }

            return result

    except Exception as exc:
        logger.error(f"Failed to get scraping stats: {exc}")
        raise



@celery_app.task(bind=True, name='src.workers.tasks.scrape_linkedin_jobs', max_retries=3)
def scrape_linkedin_jobs(
    self: Task,
    keywords: Optional[str] = None,
    location: Optional[str] = None,
    max_pages: Optional[int] = None
) -> Dict[str, Any]:
    """
    Scrape LinkedIn jobs for all active companies or specific keywords.

    This task searches LinkedIn for jobs matching company names and/or keywords,
    then stores the results in the database. Unlike company-specific scrapers,
    this aggregates jobs from LinkedIn's job board.

    Args:
        keywords: Optional job title/keywords to search for (e.g., "Software Engineer")
                 If None, will use positions from LINKEDIN_JOB_POSITIONS env variable
        location: Location to filter jobs (default: from LINKEDIN_SEARCH_LOCATION env)
        max_pages: Maximum pages to scrape per search (default: from LINKEDIN_MAX_PAGES env)

    Returns:
        Dictionary with scraping statistics

    Example:
        # Search for all configured positions
        scrape_linkedin_jobs.delay()

        # Search for specific role
        scrape_linkedin_jobs.delay(keywords="Software Engineer", location="Israel")
    """
    try:
        # Import settings
        from config.settings import settings

        # Use environment variables as defaults
        if location is None:
            location = settings.linkedin_search_location
        if max_pages is None:
            max_pages = settings.linkedin_max_pages

        logger.info("=" * 80)
        logger.info(f"Starting LinkedIn scraping job...")
        logger.info(f"Keywords: {keywords or 'Configured positions from env'}")
        logger.info(f"Location: {location}")
        logger.info(f"Max pages: {max_pages}")
        logger.info("=" * 80)

        start_time = datetime.utcnow()

        # Import here to avoid circular dependencies
        from src.storage.repositories.company_repo import CompanyRepository
        # JobPositionRepository not needed - we'll use direct model access
        from src.scrapers.playwright_scraper import PlaywrightScraper
        from src.models.scraping_session import ScrapingSession
        from src.models.company import Company
        import httpx
        from bs4 import BeautifulSoup

        # Define search queries - use job roles from settings if no keywords specified
        search_queries = []
        if keywords:
            search_queries.append(keywords)
        else:
            # Get positions from environment variable
            search_queries = settings.linkedin_positions_list
            if not search_queries:
                # Fallback to default positions from Settings class default value
                logger.warning("LINKEDIN_JOB_POSITIONS is empty, using default positions from settings")
                # Get default value from Settings class definition
                from config.settings import Settings
                default_positions = Settings.model_fields['linkedin_job_positions'].default
                search_queries = [pos.strip() for pos in default_positions.split(',') if pos.strip()]

        logger.info(f"Will search LinkedIn for {len(search_queries)} queries: {', '.join(search_queries[:5])}...")

        # LinkedIn API configuration
        linkedin_config = {
            "scraper_type": "linkedin",
            "api_endpoint": "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
            "pagination_params": {
                "offset_param": "start",
                "page_size": 25,
                "max_pages": max_pages
            },
            "timeout": 30.0,
            "wait_time": 2  # Be respectful with rate limiting
        }

        # Create a pseudo-company config for LinkedIn
        linkedin_company_config = {
            "name": "LinkedIn",
            "website": "https://www.linkedin.com",
            "careers_url": "https://www.linkedin.com/jobs",
            "location_filter": {
                "enabled": True,
                "countries": [location],
                "match_keywords": [
                    location,
                    "Tel Aviv",
                    "Herzliya",
                    "Haifa",
                    "Jerusalem",
                    "Petach Tikva",
                    "Raanana",
                    "IL"
                ] if location == "Israel" else [location]
            }
        }

        total_jobs_found = 0
        total_jobs_new = 0
        total_jobs_updated = 0
        results_by_query = {}

        # Search for each query
        for query in search_queries:
            try:
                logger.info(f"Searching LinkedIn for: {query}")

                # Update query params
                linkedin_config["query_params"] = {
                    "keywords": query,
                    "location": location
                }

                # Create scraper
                scraper = PlaywrightScraper(
                    company_config=linkedin_company_config,
                    scraping_config=linkedin_config
                )

                # Scrape jobs (this is async, so we need to run it in event loop)
                jobs = asyncio.run(scraper.scrape())

                logger.info(f"Found {len(jobs)} jobs for query: {query}")

                # Filter jobs by location before processing
                allowed_jobs, filtered_jobs = location_filter.filter_jobs(jobs)
                if filtered_jobs:
                    logger.info(f"Filtered out {len(filtered_jobs)} jobs due to location restrictions")

                # Store jobs in database with company matching and de-duplication
                with db.get_session() as session:
                    company_repo = CompanyRepository(session)
                    job_repo = JobPositionRepository(session)
                    company_matcher = CompanyMatchingService(session)
                    dedup_service = JobDeduplicationService(session)

                    jobs_new = 0
                    jobs_updated = 0
                    jobs_skipped_duplicate = 0
                    jobs_flagged_review = 0
                    jobs_filtered_location = len(filtered_jobs)

                    for job in allowed_jobs:
                        # Extract company name from LinkedIn data
                        linkedin_company_name = job.get('company', '')
                        if not linkedin_company_name:
                            logger.warning(f"Job missing company name: {job.get('title', 'Unknown')}")
                            continue

                        # Try to match with existing company in database
                        matched_company, confidence = company_matcher.find_matching_company(linkedin_company_name)

                        if matched_company:
                            # Use matched company
                            company = matched_company
                            logger.debug(f"Matched '{linkedin_company_name}' to '{company.name}' (confidence: {confidence:.2f})")
                        else:
                            # Create new company for unmatched LinkedIn companies
                            company = company_repo.get_by_name(linkedin_company_name)
                            if not company:
                                company = Company(
                                    name=linkedin_company_name,
                                    website=f"https://www.linkedin.com/company/{linkedin_company_name.lower().replace(' ', '-')}",
                                    careers_url=job.get('job_url', ''),
                                    industry="Unknown",
                                    is_active=False,  # Don't auto-activate LinkedIn-discovered companies
                                    location=job.get('location', ''),
                                    scraping_config={}
                                )
                                session.add(company)
                                session.flush()  # Get the ID
                                logger.info(f"Created new company from LinkedIn: {linkedin_company_name}")

                        # Check for duplicate jobs using de-duplication service
                        duplicate_job, dup_score, needs_review = dedup_service.check_for_duplicate(
                            company_id=str(company.id),
                            title=job.get('title', ''),
                            location=job.get('location', '')
                        )

                        # Check if job already exists by external_id
                        existing_job = job_repo.get_by_external_id(job.get('external_id', ''), company.id)

                        if existing_job:
                            # Update existing job
                            existing_job.title = job.get('title', '')
                            existing_job.location = job.get('location', '')
                            existing_job.job_url = job.get('job_url', '')
                            existing_job.remote_type = 'remote' if job.get('is_remote', False) else 'onsite'
                            existing_job.last_seen_at = datetime.utcnow()
                            existing_job.scraped_at = datetime.utcnow()
                            jobs_updated += 1
                        elif duplicate_job and dup_score >= dedup_service.HIGH_CONFIDENCE_THRESHOLD:
                            # High confidence duplicate - skip creating new job
                            logger.info(f"Skipping duplicate job: '{job.get('title')}' (matches existing job ID: {duplicate_job.id})")
                            jobs_skipped_duplicate += 1
                        else:
                            # Create new job
                            now = datetime.utcnow()

                            # Build duplicate metadata if there's a potential duplicate
                            dup_metadata = None
                            if duplicate_job:
                                dup_metadata = {
                                    'potential_duplicate_of_id': str(duplicate_job.id),
                                    'confidence_score': dup_score,
                                    'needs_manual_review': needs_review,
                                    'checked_at': now.isoformat()
                                }

                            new_job = JobPosition(
                                company_id=company.id,
                                external_id=job.get('external_id', ''),
                                title=job.get('title', ''),
                                location=job.get('location', ''),
                                job_url=job.get('job_url', ''),
                                remote_type='remote' if job.get('is_remote', False) else 'onsite',
                                posted_date=job.get('posted_date'),
                                scraped_at=now,
                                first_seen_at=now,
                                last_seen_at=now,
                                status='active',
                                is_active=True,
                                source_type='linkedin_aggregator',
                                duplicate_metadata=dup_metadata
                            )
                            session.add(new_job)
                            jobs_new += 1

                            if needs_review:
                                jobs_flagged_review += 1
                                logger.warning(f"Job flagged for review: '{job.get('title')}' (possible duplicate, score: {dup_score:.2f})")

                    session.commit()

                    total_jobs_found += len(jobs)
                    total_jobs_new += jobs_new
                    total_jobs_updated += jobs_updated

                    results_by_query[query] = {
                        'jobs_found': len(jobs),
                        'jobs_new': jobs_new,
                        'jobs_updated': jobs_updated,
                        'jobs_skipped_duplicate': jobs_skipped_duplicate,
                        'jobs_flagged_review': jobs_flagged_review
                    }

                    logger.success(
                        f"Processed {query}: {jobs_new} new, {jobs_updated} updated, "
                        f"{jobs_skipped_duplicate} skipped (duplicates), {jobs_flagged_review} flagged for review"
                    )

                # Small delay between queries to be respectful
                import time
                time.sleep(3)

            except Exception as e:
                logger.error(f"Failed to scrape LinkedIn for query '{query}': {e}")
                results_by_query[query] = {
                    'error': str(e),
                    'jobs_found': 0,
                    'jobs_new': 0,
                    'jobs_updated': 0
                }
                continue

        duration = (datetime.utcnow() - start_time).total_seconds()

        result = {
            'status': 'success',
            'started_at': start_time.isoformat(),
            'completed_at': datetime.utcnow().isoformat(),
            'duration_seconds': duration,
            'queries_searched': len(search_queries),
            'total_jobs_found': total_jobs_found,
            'total_jobs_new': total_jobs_new,
            'total_jobs_updated': total_jobs_updated,
            'results_by_query': results_by_query
        }

        logger.success("=" * 80)
        logger.success(f"LinkedIn scraping completed successfully!")
        logger.success(f"  Queries: {len(search_queries)}")
        logger.success(f"  Jobs found: {total_jobs_found}")
        logger.success(f"  New jobs: {total_jobs_new}")
        logger.success(f"  Updated jobs: {total_jobs_updated}")
        logger.success(f"  Duration: {duration:.2f}s")
        logger.success("=" * 80)

        return result

    except Exception as exc:
        logger.error(f"LinkedIn scraping failed: {exc}")
        logger.exception(exc)

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))


@celery_app.task(
    bind=True,
    name='scrape_linkedin_jobs_by_company',
    max_retries=2,
    default_retry_delay=300,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=3600,
    acks_late=True,
    reject_on_worker_lost=True
)
def scrape_linkedin_jobs_by_company(self) -> Dict[str, Any]:
    """
    Scrape LinkedIn for jobs from all companies in the database.

    This task fetches all companies from the DB and searches LinkedIn
    for each company name, saving any matching jobs found.

    Unlike scrape_linkedin_jobs which searches by job position/keyword,
    this task searches by company name to ensure comprehensive coverage
    of jobs from known companies.

    Returns:
        Dict with scraping results
    """
    import asyncio
    from datetime import datetime
    from src.storage.database import db
    from src.models.company import Company
    from src.models.job_position import JobPosition
    from src.scrapers.playwright_scraper import PlaywrightScraper
    from src.services.deduplication_service import JobDeduplicationService

    logger.info("=" * 80)
    logger.info("STARTING LINKEDIN SCRAPING BY COMPANY")
    logger.info("=" * 80)

    start_time = datetime.utcnow()

    try:
        # Get all companies from DB
        with db.get_session() as session:
            all_companies = session.query(Company).order_by(Company.name).all()
            company_data = [(str(c.id), c.name) for c in all_companies]

        logger.info(f"Found {len(company_data)} companies to search on LinkedIn")

        async def scrape_companies():
            total_jobs_found = 0
            total_jobs_new = 0
            total_jobs_updated = 0
            total_jobs_skipped = 0
            companies_with_jobs = 0

            location = settings.linkedin_search_location

            for company_id, company_name in company_data:
                try:
                    # Skip generic names
                    if company_name.lower() in ['confidential', 'stealth', 'unknown', 'n/a']:
                        continue

                    linkedin_config = {
                        'scraper_type': 'linkedin',
                        'api_endpoint': 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search',
                        'query_params': {
                            'keywords': company_name,
                            'location': location
                        },
                        'pagination_params': {
                            'offset_param': 'start',
                            'page_size': 25,
                            'max_pages': 2  # Limit pages per company
                        },
                        'timeout': 30.0,
                        'wait_time': 1
                    }

                    linkedin_company_config = {
                        'name': 'LinkedIn',
                        'website': 'https://www.linkedin.com',
                        'careers_url': 'https://www.linkedin.com/jobs',
                        'location_filter': {
                            'enabled': True,
                            'countries': [location],
                            'match_keywords': ['Israel', 'Tel Aviv', 'Herzliya', 'Haifa',
                                             'Jerusalem', 'Ramat Gan', 'Petah Tikva',
                                             'Netanya', 'Kfar Saba', 'Raanana']
                        }
                    }

                    scraper = PlaywrightScraper(
                        company_config=linkedin_company_config,
                        scraping_config=linkedin_config
                    )

                    jobs = await scraper.scrape()

                    # Filter to only jobs that match this company name (case-insensitive)
                    matched_jobs = [
                        j for j in jobs
                        if j.get('company', '').lower() == company_name.lower()
                    ]

                    # Filter by location
                    matched_jobs, filtered_jobs = location_filter.filter_jobs(matched_jobs)
                    if filtered_jobs:
                        logger.debug(f"{company_name}: Filtered out {len(filtered_jobs)} jobs due to location")

                    if matched_jobs:
                        logger.info(f"{company_name}: Found {len(matched_jobs)} jobs")
                        companies_with_jobs += 1
                        total_jobs_found += len(matched_jobs)

                        # Save to DB
                        with db.get_session() as session:
                            dedup_service = JobDeduplicationService(session)

                            for job in matched_jobs:
                                # Check for existing job by external_id
                                existing = session.query(JobPosition).filter(
                                    JobPosition.external_id == job.get('external_id', ''),
                                    JobPosition.company_id == company_id
                                ).first()

                                if existing:
                                    existing.last_seen_at = datetime.utcnow()
                                    existing.scraped_at = datetime.utcnow()
                                    total_jobs_updated += 1
                                else:
                                    # Check for duplicates by title
                                    duplicate_job, dup_score, _ = dedup_service.check_for_duplicate(
                                        company_id=company_id,
                                        title=job.get('title', ''),
                                        location=job.get('location', '')
                                    )

                                    if duplicate_job and dup_score >= dedup_service.HIGH_CONFIDENCE_THRESHOLD:
                                        # Update last_seen_at on the existing job
                                        duplicate_job.last_seen_at = datetime.utcnow()
                                        total_jobs_skipped += 1
                                    else:
                                        now = datetime.utcnow()
                                        new_job = JobPosition(
                                            company_id=company_id,
                                            external_id=job.get('external_id', ''),
                                            title=job.get('title', ''),
                                            location=job.get('location', ''),
                                            job_url=job.get('job_url', ''),
                                            remote_type='remote' if job.get('is_remote', False) else 'onsite',
                                            posted_date=job.get('posted_date'),
                                            scraped_at=now,
                                            first_seen_at=now,
                                            last_seen_at=now,
                                            status='active',
                                            is_active=True,
                                            source_type='linkedin_aggregator'
                                        )
                                        session.add(new_job)
                                        total_jobs_new += 1

                            session.commit()

                    # Small delay between companies
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.warning(f"{company_name}: Error - {str(e)[:100]}")
                    continue

            return {
                'companies_searched': len(company_data),
                'companies_with_jobs': companies_with_jobs,
                'total_jobs_found': total_jobs_found,
                'new_jobs': total_jobs_new,
                'updated_jobs': total_jobs_updated,
                'skipped_duplicates': total_jobs_skipped
            }

        # Run the async scraping
        result = asyncio.run(scrape_companies())

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        result['duration_seconds'] = duration
        result['status'] = 'success'

        logger.success("=" * 80)
        logger.success("LINKEDIN BY COMPANY SCRAPING COMPLETED")
        logger.success(f"  Companies searched: {result['companies_searched']}")
        logger.success(f"  Companies with jobs: {result['companies_with_jobs']}")
        logger.success(f"  Jobs found: {result['total_jobs_found']}")
        logger.success(f"  New jobs: {result['new_jobs']}")
        logger.success(f"  Updated jobs: {result['updated_jobs']}")
        logger.success(f"  Skipped (duplicates): {result['skipped_duplicates']}")
        logger.success(f"  Duration: {duration:.2f}s")
        logger.success("=" * 80)

        return result

    except Exception as exc:
        logger.error(f"LinkedIn by company scraping failed: {exc}")
        logger.exception(exc)

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))



@celery_app.task(bind=True, name='src.workers.tasks.scrape_vc_portfolio', max_retries=3)
def scrape_vc_portfolio(self: Task, vc_name: str = None) -> Dict[str, Any]:
    """
    Scrape jobs from VC portfolio career pages (Getro-powered).

    These pages list jobs from multiple portfolio companies. Jobs are attributed
    to the actual company, not the VC.

    Args:
        vc_name: Optional VC name to scrape. If None, scrapes all configured VCs.

    Returns:
        Dictionary with scraping statistics
    """
    import yaml
    from pathlib import Path

    try:
        logger.info("=" * 80)
        logger.info(f"Starting VC portfolio scraping: {vc_name or 'ALL'}")
        logger.info("=" * 80)

        start_time = datetime.utcnow()

        # Load VC portfolio config
        config_path = Path(__file__).parent.parent.parent / "config" / "vc_portfolios.yaml"
        if not config_path.exists():
            logger.warning(f"VC portfolios config not found: {config_path}")
            return {"error": "VC portfolios config not found"}

        with open(config_path, 'r') as f:
            vc_config = yaml.safe_load(f)

        vc_portfolios = vc_config.get('vc_portfolios', [])

        # Filter by VC name if specified
        if vc_name:
            vc_portfolios = [vc for vc in vc_portfolios if vc.get('name') == vc_name]
            if not vc_portfolios:
                return {"error": f"VC not found: {vc_name}"}

        result = {
            'vcs_scraped': 0,
            'total_jobs_found': 0,
            'new_jobs': 0,
            'updated_jobs': 0,
            'skipped_duplicates': 0,
            'filtered_location': 0,
            'companies_created': 0,
            'errors': []
        }

        for vc in vc_portfolios:
            vc_display_name = vc.get('name', 'Unknown VC')
            careers_url = vc.get('careers_url')
            scraper_type = vc.get('scraper_type', 'getro')

            if not careers_url:
                logger.warning(f"No careers_url for VC: {vc_display_name}")
                continue

            logger.info(f"Scraping VC portfolio: {vc_display_name}")

            try:
                # Create scraper config
                company_config = {
                    'name': vc_display_name,
                    'careers_url': careers_url,
                }
                scraping_config = {
                    'scraper_type': scraper_type,
                    'api_endpoint': careers_url,
                }

                # Create and run scraper
                scraper = PlaywrightScraper(company_config, scraping_config)
                jobs = asyncio.run(scraper.scrape())

                logger.info(f"Found {len(jobs)} jobs from {vc_display_name}")
                result['total_jobs_found'] += len(jobs)

                # Filter jobs by location
                allowed_jobs, filtered_jobs = location_filter.filter_jobs(jobs)
                result['filtered_location'] += len(filtered_jobs)

                # Store jobs with company matching
                with db.get_session() as session:
                    company_repo = CompanyRepository(session)
                    job_repo = JobPositionRepository(session)
                    company_matcher = CompanyMatchingService(session)
                    dedup_service = JobDeduplicationService(session)

                    for job in allowed_jobs:
                        company_name = job.get('company', '')
                        if not company_name:
                            logger.warning(f"Job missing company name: {job.get('title')}")
                            continue

                        # Match or create company
                        matched_company, confidence = company_matcher.find_matching_company(company_name)

                        if matched_company:
                            company = matched_company
                        else:
                            company = company_repo.get_by_name(company_name)
                            if not company:
                                company = Company(
                                    name=company_name,
                                    website=job.get('job_url', '').split('/careers')[0] if '/careers' in job.get('job_url', '') else '',
                                    careers_url=job.get('job_url', ''),
                                    industry=job.get('industry', 'Unknown'),
                                    is_active=False,
                                    location=job.get('location', ''),
                                    scraping_config={}
                                )
                                session.add(company)
                                session.flush()
                                result['companies_created'] += 1
                                logger.info(f"Created company from VC portfolio: {company_name}")

                        # Check for duplicates
                        duplicate_job, dup_score, needs_review = dedup_service.check_for_duplicate(
                            company_id=str(company.id),
                            title=job.get('title', ''),
                            location=job.get('location', '')
                        )

                        existing_job = job_repo.get_by_external_id(job.get('external_id', ''), company.id)

                        if existing_job:
                            existing_job.title = job.get('title', '')
                            existing_job.location = job.get('location', '')
                            existing_job.job_url = job.get('job_url', '')
                            existing_job.remote_type = 'remote' if job.get('is_remote', False) else 'onsite'
                            existing_job.last_seen_at = datetime.utcnow()
                            result['updated_jobs'] += 1
                        elif duplicate_job and dup_score >= dedup_service.HIGH_CONFIDENCE_THRESHOLD:
                            result['skipped_duplicates'] += 1
                        else:
                            new_job = JobPosition(
                                company_id=company.id,
                                external_id=job.get('external_id', ''),
                                title=job.get('title', ''),
                                location=job.get('location', ''),
                                job_url=job.get('job_url', ''),
                                remote_type='remote' if job.get('is_remote', False) else 'onsite',
                                posted_date=job.get('posted_date'),
                                scraped_at=datetime.utcnow(),
                                last_seen_at=datetime.utcnow(),
                                is_active=True,
                                source='vc_portfolio',
                                metadata={'vc_source': vc_display_name}
                            )
                            session.add(new_job)
                            result['new_jobs'] += 1

                    session.commit()

                result['vcs_scraped'] += 1

            except Exception as e:
                logger.error(f"Error scraping VC {vc_display_name}: {e}")
                result['errors'].append({'vc': vc_display_name, 'error': str(e)})

        duration = (datetime.utcnow() - start_time).total_seconds()
        result['duration_seconds'] = duration

        logger.success("=" * 80)
        logger.success("VC PORTFOLIO SCRAPING COMPLETED")
        logger.success(f"  VCs scraped: {result['vcs_scraped']}")
        logger.success(f"  Jobs found: {result['total_jobs_found']}")
        logger.success(f"  New jobs: {result['new_jobs']}")
        logger.success(f"  Updated jobs: {result['updated_jobs']}")
        logger.success(f"  Companies created: {result['companies_created']}")
        logger.success(f"  Duration: {duration:.2f}s")
        logger.success("=" * 80)

        return result

    except Exception as exc:
        logger.error(f"VC portfolio scraping failed: {exc}")
        logger.exception(exc)
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))