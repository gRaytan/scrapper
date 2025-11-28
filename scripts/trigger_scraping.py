#!/usr/bin/env python3
"""
Manually trigger scraping tasks for testing.
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workers.tasks import (
    run_daily_scraping,
    scrape_single_company,
    process_new_jobs,
    cleanup_old_sessions,
    mark_stale_jobs_inactive,
    get_scraping_stats
)
from src.utils.logger import logger


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Trigger scraping tasks manually")
    parser.add_argument(
        '--task',
        choices=['daily', 'company', 'process', 'cleanup', 'mark-stale', 'stats'],
        required=True,
        help='Task to run'
    )
    parser.add_argument(
        '--company',
        help='Company name (for company task)'
    )
    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Run incremental scrape (last 24 hours only)'
    )
    parser.add_argument(
        '--async',
        dest='async_mode',
        action='store_true',
        help='Run task asynchronously (queue it)'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Hours to look back (for process task)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Days to keep (for cleanup task) or days without updates (for mark-stale task)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.task == 'daily':
            logger.info("Triggering daily scraping task...")
            if args.async_mode:
                result = run_daily_scraping.delay()
                logger.info(f"Task queued: {result.id}")
                logger.info("Use 'celery -A src.workers.celery_app result <task_id>' to check status")
            else:
                result = run_daily_scraping()
                logger.success(f"Task completed: {result}")
        
        elif args.task == 'company':
            if not args.company:
                logger.error("--company is required for company task")
                sys.exit(1)
            
            logger.info(f"Triggering scrape for {args.company}...")
            if args.async_mode:
                result = scrape_single_company.delay(args.company, args.incremental)
                logger.info(f"Task queued: {result.id}")
            else:
                result = scrape_single_company(args.company, args.incremental)
                logger.success(f"Task completed: {result}")
        
        elif args.task == 'process':
            logger.info(f"Triggering job processing (last {args.hours} hours)...")
            if args.async_mode:
                result = process_new_jobs.delay(args.hours)
                logger.info(f"Task queued: {result.id}")
            else:
                result = process_new_jobs(args.hours)
                logger.success(f"Task completed: {result}")
        
        elif args.task == 'cleanup':
            logger.info(f"Triggering cleanup (keeping last {args.days} days)...")
            if args.async_mode:
                result = cleanup_old_sessions.delay(args.days)
                logger.info(f"Task queued: {result.id}")
            else:
                result = cleanup_old_sessions(args.days)
                logger.success(f"Task completed: {result}")
        
        elif args.task == 'mark-stale':
            logger.info(f"Triggering mark stale jobs (not updated in {args.days} days)...")
            if args.async_mode:
                result = mark_stale_jobs_inactive.delay(args.days)
                logger.info(f"Task queued: {result.id}")
            else:
                result = mark_stale_jobs_inactive(args.days)
                logger.success(f"Task completed: {result}")
        
        elif args.task == 'stats':
            logger.info(f"Getting scraping stats (last {args.days} days)...")
            result = get_scraping_stats(args.days)
            
            logger.info("=" * 80)
            logger.info(f"Scraping Statistics (Last {result['days']} days)")
            logger.info("=" * 80)
            logger.info(f"Total sessions: {result['total_sessions']}")
            logger.info(f"Successful: {result['successful_sessions']}")
            logger.info(f"Failed: {result['failed_sessions']}")
            logger.info(f"Success rate: {result['success_rate']:.1f}%")
            logger.info(f"Total new jobs: {result['total_new_jobs']}")
            logger.info(f"Total updated jobs: {result['total_updated_jobs']}")
            logger.info("")
            logger.info("By Company:")
            for company, stats in result['by_company'].items():
                logger.info(f"  {company}:")
                logger.info(f"    Sessions: {stats['sessions']} (✓ {stats['successful']}, ✗ {stats['failed']})")
                logger.info(f"    New jobs: {stats['new_jobs']}, Updated: {stats['updated_jobs']}")
            logger.info("=" * 80)
    
    except Exception as e:
        logger.error(f"Task failed: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()

