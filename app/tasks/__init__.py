"""
Celery tasks for Chronus AI.
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Initialize Celery
celery_app = Celery(
    "chronus",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Sync all users' Gmail every 1 minute
    "sync-all-gmail-users": {
        "task": "app.tasks.gmail_sync_tasks.sync_all_users",
        "schedule": crontab(minute="*"),  # Every minute
    },
    # Clean up old emails every day at 2 AM
    "cleanup-old-emails": {
        "task": "app.tasks.gmail_sync_tasks.cleanup_old_emails",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        "kwargs": {"days": 90},  # Delete emails older than 90 days
    },
}

# Auto-discover tasks from all modules
celery_app.autodiscover_tasks(["app.tasks"])

# Import tasks to ensure they're registered
from app.tasks import gmail_sync_tasks  # noqa: F401, E402
