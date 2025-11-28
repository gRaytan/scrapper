#!/bin/bash
# Start Celery Beat scheduler for periodic tasks

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start Celery Beat
python3 -m celery -A src.workers.celery_app beat \
    --loglevel=info \
    --scheduler=celery.beat:PersistentScheduler \
    --schedule=/tmp/celerybeat-schedule

