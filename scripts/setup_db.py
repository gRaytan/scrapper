"""Database setup and initialization script."""
import sys
from loguru import logger

from src.utils.logger import setup_logging
from src.storage.database import db


def main():
    """Initialize the database."""
    logger.info("=" * 80)
    logger.info("Database Setup")
    logger.info("=" * 80)

    try:
        # Create all tables
        logger.info("Creating database tables...")
        db.create_tables()
        logger.success("Database tables created successfully!")

        logger.info("\nCreated tables:")
        logger.info("  - companies")
        logger.info("  - job_positions")
        logger.info("  - scraping_sessions")

        logger.info("\nDatabase is ready to use!")
        return 0

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())

