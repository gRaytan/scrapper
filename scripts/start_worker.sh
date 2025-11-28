#!/bin/bash
# Start Celery worker for job scraping tasks

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start Celery worker
python3 -m celery -A src.workers.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=50 \
    --time-limit=3600 \
    --soft-time-limit=3300 \
    --pool=prefork \
    --queues=celery \
    --hostname=worker@%h

