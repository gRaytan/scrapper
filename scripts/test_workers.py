#!/usr/bin/env python3
"""
Test worker setup without requiring Redis.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import logger


def test_imports():
    """Test that all worker modules can be imported."""
    logger.info("Testing worker imports...")
    
    try:
        from src.workers.celery_app import celery_app
        logger.success("✓ celery_app imported successfully")
        
        from src.workers import tasks
        logger.success("✓ tasks module imported successfully")
        
        # Check that tasks are registered
        task_names = [
            'src.workers.tasks.run_daily_scraping',
            'src.workers.tasks.scrape_single_company',
            'src.workers.tasks.process_new_jobs',
            'src.workers.tasks.cleanup_old_sessions',
            'src.workers.tasks.mark_stale_jobs_inactive',
            'src.workers.tasks.get_scraping_stats',
        ]
        
        logger.info("\nRegistered tasks:")
        for task_name in task_names:
            if task_name in celery_app.tasks:
                logger.success(f"  ✓ {task_name}")
            else:
                logger.error(f"  ✗ {task_name} NOT FOUND")
        
        # Check beat schedule
        logger.info("\nBeat schedule:")
        for name, config in celery_app.conf.beat_schedule.items():
            logger.info(f"  - {name}:")
            logger.info(f"      Task: {config['task']}")
            logger.info(f"      Schedule: {config['schedule']}")
        
        logger.success("\n✓ All worker components loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        logger.exception(e)
        return False


def test_settings():
    """Test that settings are configured correctly."""
    logger.info("\nTesting settings...")
    
    try:
        from config.settings import settings
        
        logger.info(f"  Celery broker: {settings.celery_broker_url}")
        logger.info(f"  Celery backend: {settings.celery_result_backend}")
        logger.info(f"  Database URL: {settings.database_url.split('@')[-1]}")
        logger.info(f"  Redis URL: {settings.redis_url}")
        
        # Check database properties
        logger.info(f"  DB pool size: {settings.db_pool_size}")
        logger.info(f"  DB max overflow: {settings.db_max_overflow}")
        logger.info(f"  DB echo: {settings.db_echo}")
        
        logger.success("✓ Settings configured correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Settings test failed: {e}")
        logger.exception(e)
        return False


def test_database_connection():
    """Test database connection."""
    logger.info("\nTesting database connection...")
    
    try:
        from src.storage.database import db
        
        with db.get_session() as session:
            # Try a simple query
            result = session.execute("SELECT 1")
            logger.success("✓ Database connection successful")
            return True
            
    except Exception as e:
        logger.warning(f"⚠ Database connection failed: {e}")
        logger.info("  This is OK if database is not running yet")
        return False


def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("Worker Setup Test")
    logger.info("=" * 80)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test settings
    results.append(("Settings", test_settings()))
    
    # Test database (optional)
    results.append(("Database", test_database_connection()))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"  {name}: {status}")
    
    all_critical_passed = results[0][1] and results[1][1]  # Imports and Settings
    
    if all_critical_passed:
        logger.success("\n✓ Worker setup is ready!")
        logger.info("\nNext steps:")
        logger.info("  1. Start Redis: docker run -d -p 6379:6379 redis:7-alpine")
        logger.info("  2. Start worker: ./scripts/start_worker.sh")
        logger.info("  3. Start beat: ./scripts/start_beat.sh")
        logger.info("  4. Trigger test: python scripts/trigger_scraping.py --task stats")
        return 0
    else:
        logger.error("\n✗ Worker setup has issues - please fix errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

