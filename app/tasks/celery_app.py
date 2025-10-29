"""
Celery application configuration and initialization.

This module sets up the Celery worker for background task processing.
Tasks are executed asynchronously and can be monitored via Flower.
"""

from celery import Celery

from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    'photography_studio',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    broker_connection_retry_on_startup=True,
    include=['app.tasks.email_tasks'],  # Auto-discover tasks
)

celery_app.config_from_object('app.tasks.celery_app')

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
)

# Optional: Result backend expiration (7 days)
celery_app.conf.result_expires = 60 * 60 * 24 * 7
