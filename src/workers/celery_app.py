"""
Celery application configuration for background task processing.
"""
from celery import Celery
from celery.schedules import crontab

from config.settings import settings

# Create Celery app
celery_app = Celery(
    'job_scraper',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['src.workers.tasks']  # Auto-discover tasks
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,
    
    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Only fetch one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
    
    # Retry settings
    task_default_retry_delay=300,  # 5 minutes
    task_max_retries=3,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Daily scraping at 2:00 AM UTC
        'daily-scraping': {
            'task': 'src.workers.tasks.run_daily_scraping',
            'schedule': crontab(hour=7, minute=0),  # 7:00 AM UTC daily
            'options': {
                'expires': 3600,  # Task expires after 1 hour if not picked up
            }
        },
        
        # Cleanup old scraping sessions every week
        'weekly-cleanup': {
            'task': 'src.workers.tasks.cleanup_old_sessions',
            'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3:00 AM UTC
            'options': {
                'expires': 3600,
            }
        },
        
        # Mark stale jobs as inactive daily
        'daily-mark-stale-jobs': {
            'task': 'src.workers.tasks.mark_stale_jobs_inactive',
            'schedule': crontab(hour=4, minute=0),  # 4:00 AM UTC daily
            'options': {
                'expires': 3600,
            }
        },
    },
)

# Optional: Configure logging
celery_app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s',
)

