"""Main entry point for running the scraper."""
import argparse
import asyncio
import sys
from pathlib import Path

from loguru import logger

# Import logger setup first
from src.utils.logger import setup_logging
from src.orchestrator.scraper_orchestrator import run_scraper


def main():
    """Main function to run the scraper."""
    parser = argparse.ArgumentParser(description="Run the career page scraper")
    parser.add_argument(
        "--company",
        type=str,
        help="Specific company name to scrape (scrapes all if not specified)"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only fetch jobs from last 24 hours (for daily updates)"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database tables before scraping"
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("Career Page Scraper Starting")
    logger.info("=" * 80)
    logger.info(f"Company: {args.company or 'ALL'}")
    logger.info(f"Incremental: {args.incremental}")
    logger.info("=" * 80)

    # Initialize database if requested
    if args.init_db:
        logger.info("Initializing database...")
        from src.storage.database import db
        db.create_tables()
        logger.success("Database initialized")

    # Run scraper
    try:
        asyncio.run(run_scraper(
            company_name=args.company,
            incremental=args.incremental
        ))
        logger.success("Scraping completed successfully!")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)
    
    return 0


if __name__ == "__main__":
    exit(main())

