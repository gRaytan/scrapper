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
    worker_concurrency=1,  # Only run 1 task at a time to prevent thread exhaustion
    
    # Retry settings
    task_default_retry_delay=300,  # 5 minutes
    task_max_retries=3,
    
    # Beat schedule for periodic tasks
    # STAGGERED SCHEDULE to prevent thread exhaustion:
    # - 12:30 AM: Mark stale jobs (quick task)
    # - 1:00 AM: Company scraping (from companies.yaml, ~2 hours)
    # - 3:00 AM: LinkedIn by keyword (131 searches, ~2 hours)
    # - 5:00 AM: LinkedIn by company name (~2 hours)
    # - 7:00 AM: Match all new jobs to user alerts (after all scrapers done)
    beat_schedule={
        # Mark stale jobs as inactive daily - runs first, quick task
        'daily-mark-stale-jobs': {
            'task': 'src.workers.tasks.mark_stale_jobs_inactive',
            'schedule': crontab(hour=0, minute=30),  # 12:30 AM UTC daily
            'options': {
                'expires': 1800,
            }
        },

        # Daily scraping at 1:00 AM UTC - company page scrapers
        'daily-scraping': {
            'task': 'src.workers.tasks.run_daily_scraping',
            'schedule': crontab(hour=1, minute=0),  # 1:00 AM UTC daily
            'options': {
                'expires': 7200,  # 2 hours
            }
        },

        # LinkedIn job scraping daily (by job position/keyword) - 3:00 AM
        'daily-linkedin-scraping': {
            'task': 'src.workers.tasks.scrape_linkedin_jobs',
            'schedule': crontab(hour=3, minute=0),  # 3:00 AM UTC daily
            'kwargs': {
                'keywords': None,  # Search for all job roles
                'location': 'Israel',
                'max_pages': 40  # ~1000 jobs per role
            },
            'options': {
                'expires': 7200,  # 2 hours
            }
        },

        # LinkedIn job scraping by company name daily - 5:00 AM
        'daily-linkedin-by-company-scraping': {
            'task': 'scrape_linkedin_jobs_by_company',
            'schedule': crontab(hour=5, minute=0),  # 5:00 AM UTC daily
            'options': {
                'expires': 7200,  # 2 hours
            }
        },

        # Match new jobs to user alerts - runs after all scrapers complete
        'daily-job-matching': {
            'task': 'src.workers.tasks.process_new_jobs',
            'schedule': crontab(hour=7, minute=0),  # 7:00 AM UTC daily
            'kwargs': {
                'hours': 24  # Match jobs from last 24 hours
            },
            'options': {
                'expires': 3600,  # 1 hour
            }
        },

        # Cleanup old scraping sessions every week
        'weekly-cleanup': {
            'task': 'src.workers.tasks.cleanup_old_sessions',
            'schedule': crontab(hour=0, minute=30, day_of_week=5),  # Saturday 12:30 AM UTC
            'options': {
                'expires': 3600,
            }
        },

        # Cleanup stuck sessions every 30 minutes
        'cleanup-stuck-sessions': {
            'task': 'src.workers.tasks.cleanup_stuck_sessions',
            'schedule': crontab(minute='*/30'),  # Every 30 minutes
            'kwargs': {
                'stuck_hours': 2  # Sessions running > 2 hours are stuck
            },
            'options': {
                'expires': 1800,
            }
        },

        # Retry failed sessions every 15 minutes
        'retry-failed-sessions': {
            'task': 'src.workers.tasks.retry_failed_sessions',
            'schedule': crontab(minute='*/15'),  # Every 15 minutes
            'kwargs': {
                'failed_minutes': 10  # Only retry sessions that failed within 10 minutes
            },
            'options': {
                'expires': 900,
            }
        },
    },
)

# Optional: Configure logging
celery_app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s',
)


# Worker startup signal - cleanup stuck sessions when worker starts
from celery.signals import worker_ready

@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Cleanup stuck sessions when worker starts."""
    from src.workers.tasks import cleanup_stuck_sessions
    # Delay by 10 seconds to let worker fully initialize
    cleanup_stuck_sessions.apply_async(countdown=10)

