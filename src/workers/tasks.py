"""
Celery tasks for background job processing.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from celery import Task
from sqlalchemy import and_

from src.workers.celery_app import celery_app
from src.orchestrator.scraper_orchestrator import ScraperOrchestrator
from src.storage.database import db
from src.models.job_position import JobPosition
from src.models.scraping_session import ScrapingSession
from src.utils.logger import logger


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
    
    This task is called after scraping completes and serves as a foundation
    for future notification matching. Currently, it just logs statistics.
    
    Args:
        hours: Number of hours to look back for new jobs
        
    Returns:
        Dictionary with processing statistics
    """
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
            ).all()
            
            if not new_jobs:
                logger.info("No new jobs to process")
                return {
                    'status': 'success',
                    'new_jobs_count': 0,
                    'hours': hours
                }
            
            # Group jobs by company
            jobs_by_company = {}
            for job in new_jobs:
                company_name = job.company.name
                if company_name not in jobs_by_company:
                    jobs_by_company[company_name] = []
                jobs_by_company[company_name].append(job)
            
            # Log statistics
            logger.info(f"Found {len(new_jobs)} new jobs from {len(jobs_by_company)} companies:")
            for company_name, jobs in jobs_by_company.items():
                logger.info(f"  - {company_name}: {len(jobs)} jobs")
            
            # TODO: In the future, this is where we'll:
            # 1. Match jobs against user alerts
            # 2. Generate notifications
            # 3. Send emails/push notifications
            
            result = {
                'status': 'success',
                'new_jobs_count': len(new_jobs),
                'companies_count': len(jobs_by_company),
                'hours': hours,
                'jobs_by_company': {
                    company: len(jobs) 
                    for company, jobs in jobs_by_company.items()
                }
            }
            
            logger.success(f"Processed {len(new_jobs)} new jobs")
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
def mark_stale_jobs_inactive(self: Task, days: int = 60) -> Dict[str, Any]:
    """
    Mark jobs as inactive if they haven't been seen in recent scrapes.
    
    Jobs that haven't been updated in N days are likely no longer available
    and should be marked as inactive.
    
    Args:
        days: Number of days without updates before marking inactive (default: 60)
        
    Returns:
        Dictionary with statistics
    """
    try:
        logger.info(f"Marking jobs inactive that haven't been updated in {days} days...")
        
        with db.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Find active jobs that haven't been updated recently
            stale_jobs = session.query(JobPosition).filter(
                and_(
                    JobPosition.is_active == True,
                    JobPosition.updated_at < cutoff
                )
            ).all()
            
            # Mark them as inactive
            for job in stale_jobs:
                job.is_active = False
            
            session.commit()
            
            result = {
                'status': 'success',
                'marked_inactive': len(stale_jobs),
                'cutoff_date': cutoff.isoformat(),
                'days': days
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

