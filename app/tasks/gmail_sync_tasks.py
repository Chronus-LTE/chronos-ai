"""
Celery tasks for Gmail sync operations.

These tasks run in the background to:
1. Perform initial sync when user connects Gmail
2. Periodically sync new emails (incremental)
3. Handle webhook notifications from Gmail
"""

import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task

from app.database import SessionLocal
from app.models.email import Email
from app.models.user import User
from app.services.email_sync_service import EmailSyncService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def initial_gmail_sync(self, user_id: str, max_messages: int = 100):
    """
    Perform initial Gmail sync for a user.

    This is triggered when user first connects their Gmail account.
    Runs in background to avoid blocking the API request.

    Args:
        user_id: User ID to sync
        max_messages: Maximum number of messages to sync (default: 100)

    Returns:
        Sync summary dict
    """
    logger.info(f"Starting initial Gmail sync task for user {user_id}")

    db = SessionLocal()
    try:
        # Get user
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            msg = f"User {user_id} not found"
            raise ValueError(msg)

        if not user.google_access_token:
            msg = f"User {user_id} has no Gmail access token"
            raise ValueError(msg)

        # Create sync service
        sync_service = EmailSyncService(db=db, user=user)

        # Perform sync
        result = sync_service.perform_initial_sync(max_messages=max_messages)

        logger.info(f"Initial sync completed for user {user_id}: {result}")
        return result

    except Exception as e:
        logger.error(f"Initial sync failed for user {user_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def incremental_gmail_sync(self, user_id: str):
    """
    Perform incremental Gmail sync for a user.

    This is triggered periodically (e.g., every 5-10 minutes) to fetch new emails.
    Uses Gmail History API for efficiency.

    Args:
        user_id: User ID to sync

    Returns:
        Sync summary dict
    """
    logger.info(f"Starting incremental Gmail sync task for user {user_id}")

    db = SessionLocal()
    try:
        # Get user
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            msg = f"User {user_id} not found"
            raise ValueError(msg)

        if not user.google_access_token:
            logger.warning(f"User {user_id} has no Gmail access token, skipping sync")
            return {"status": "skipped", "reason": "no_token"}

        # Create sync service
        sync_service = EmailSyncService(db=db, user=user)

        # Perform incremental sync
        result = sync_service.perform_incremental_sync()

        logger.info(f"Incremental sync completed for user {user_id}: {result}")
        return result

    except Exception as e:
        logger.error(f"Incremental sync failed for user {user_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=30 * (2**self.request.retries))

    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def sync_single_email(self, user_id: str, gmail_message_id: str):
    """
    Sync a single email message to the database.

    This is useful for immediately syncing a sent email or a specific message.

    Args:
        user_id: User ID
        gmail_message_id: Gmail message ID to sync

    Returns:
        Sync result
    """
    logger.info(f"Syncing single email {gmail_message_id} for user {user_id}")

    db = SessionLocal()
    try:
        # Get user
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            msg = f"User {user_id} not found"
            raise ValueError(msg)

        if not user.google_access_token:
            logger.warning(f"User {user_id} has no Gmail access token, skipping sync")
            return {"status": "skipped", "reason": "no_token"}

        # Create sync service
        sync_service = EmailSyncService(db=db, user=user)

        # Sync the specific message
        email = sync_service._sync_single_message(gmail_message_id)

        logger.info(f"Successfully synced email {gmail_message_id} for user {user_id}")
        return {
            "status": "completed",
            "gmail_id": gmail_message_id,
            "email_id": email.id if email else None,
        }

    except Exception as e:
        logger.error(f"Failed to sync email {gmail_message_id} for user {user_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=10 * (2**self.request.retries))

    finally:
        db.close()


@shared_task
def sync_all_users():
    """
    Sync all users with Gmail connected.

    This is triggered by Celery Beat periodically (e.g., every 10 minutes).
    """
    logger.info("Starting sync for all users")

    db = SessionLocal()
    try:
        # Get all users with Gmail connected
        users = db.query(User).filter(User.google_access_token.isnot(None)).all()

        logger.info(f"Found {len(users)} users with Gmail connected")

        # Trigger incremental sync for each user
        for user in users:
            logger.info(f"Triggering incremental sync for user {user.id}")
            incremental_gmail_sync.delay(user.id)

        return {"status": "completed", "users_synced": len(users)}

    except Exception as e:
        logger.error(f"Failed to sync all users: {e}")
        raise

    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def handle_gmail_webhook(self, user_id: str, history_id: str):
    """
    Handle Gmail push notification webhook.

    Gmail can send push notifications when mailbox changes.
    This is the most real-time option.

    Args:
        user_id: User ID
        history_id: Gmail history ID from webhook

    Returns:
        Processing result
    """
    logger.info(f"Handling Gmail webhook for user {user_id}, history_id={history_id}")

    db = SessionLocal()
    try:
        # Get user
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            msg = f"User {user_id} not found"
            raise ValueError(msg)

        # Create sync service
        sync_service = EmailSyncService(db=db, user=user)

        # Perform incremental sync
        result = sync_service.perform_incremental_sync()

        logger.info(f"Webhook processed for user {user_id}: {result}")
        return result

    except Exception as e:
        logger.error(f"Webhook processing failed for user {user_id}: {e}")
        raise self.retry(exc=e, countdown=10 * (2**self.request.retries))

    finally:
        db.close()


@shared_task
def cleanup_old_emails(days: int = 90):
    """
    Clean up old emails from database to save space.

    Args:
        days: Delete emails older than this many days

    Returns:
        Cleanup summary
    """
    logger.info(f"Starting cleanup of emails older than {days} days")

    db = SessionLocal()
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Delete old emails
        deleted = db.query(Email).filter(Email.date < cutoff_date).delete()

        db.commit()

        logger.info(f"Cleanup completed: {deleted} emails deleted")
        return {"status": "completed", "deleted": deleted}

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        db.rollback()
        raise

    finally:
        db.close()
