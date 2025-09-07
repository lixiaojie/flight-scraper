"""
Celery configuration for background task processing
"""

from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "flight_scraper",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.scraping_tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks (beat schedule)
celery_app.conf.beat_schedule = {
    "cleanup-old-tasks": {
        "task": "app.tasks.scraping_tasks.cleanup_old_tasks",
        "schedule": 3600.0,  # Run every hour
    },
    "update-task-status": {
        "task": "app.tasks.scraping_tasks.update_task_status",
        "schedule": 60.0,  # Run every minute
    },
}

celery_app.conf.timezone = "UTC"
