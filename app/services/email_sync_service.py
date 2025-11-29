"""
Email Sync Service - Handles syncing Gmail data to local database.

This service provides:
1. Initial full sync (first-time setup)
2. Incremental sync (using Gmail History API)
3. Real-time updates via webhooks
4. Efficient batch processing
5. Error handling and retry logic
"""

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from sqlalchemy import and_, desc
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.email import Email, GmailLabel, GmailSyncState
from app.models.user import User
from app.services.google.gmail_service import GoogleGmailService

logger = logging.getLogger(__name__)


class EmailSyncService:
    """Service for syncing Gmail data to local database."""

    def __init__(self, db: Session, user: User):
        """
        Initialize sync service.

        Args:
            db: Database session
            user: User to sync emails for
        """
        self.db = db
        self.user = user
        self.gmail_service = GoogleGmailService(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
        )

    # SYNC STATE MANAGEMENT

    def get_or_create_sync_state(self) -> GmailSyncState:
        """Get or create sync state for user."""
        sync_state = self.db.query(GmailSyncState).filter_by(user_id=self.user.id).first()

        if not sync_state:
            sync_state = GmailSyncState(
                user_id=self.user.id,
                status="pending",
            )
            self.db.add(sync_state)
            self.db.commit()
            self.db.refresh(sync_state)

        return sync_state

    def update_sync_state(
        self,
        status: str | None = None,
        sync_type: str | None = None,
        total_messages: int | None = None,
        synced_messages: int | None = None,
        failed_messages: int | None = None,
        history_id: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update sync state."""
        sync_state = self.get_or_create_sync_state()

        if status:
            sync_state.status = status
            if status == "syncing":
                sync_state.started_at = datetime.now(timezone.utc)
            elif status in ["completed", "failed"]:
                sync_state.completed_at = datetime.now(timezone.utc)
                if status == "completed":
                    sync_state.last_sync_date = datetime.now(timezone.utc)

        if sync_type:
            sync_state.sync_type = sync_type
        if total_messages is not None:
            sync_state.total_messages = total_messages
        if synced_messages is not None:
            sync_state.synced_messages = synced_messages
        if failed_messages is not None:
            sync_state.failed_messages = failed_messages
        if history_id:
            sync_state.history_id = history_id
        if error:
            sync_state.last_error = error
            sync_state.error_count += 1

        self.db.commit()

    # INITIAL FULL SYNC

    def perform_initial_sync(
        self,
        max_messages: int = 100,
        batch_size: int = 50,
    ) -> dict[str, Any]:
        """
        Perform initial full sync of Gmail mailbox.

        This is called when user first connects Gmail.
        Syncs most recent emails up to max_messages.

        Args:
            max_messages: Maximum number of messages to sync
            batch_size: Number of messages to process per batch

        Returns:
            Sync summary with stats
        """
        logger.info(f"Starting initial sync for user {self.user.id}")

        try:
            self.update_sync_state(status="syncing", sync_type="initial")

            # Get profile to get history_id
            profile = self.gmail_service.get_profile()
            history_id = profile.get("history_id")

            # Sync labels first
            self._sync_labels()

            # Get message IDs from Gmail
            logger.info(f"Fetching message list (max {max_messages})...")

            message_ids = []
            next_page_token = None

            while len(message_ids) < max_messages:
                # Calculate how many more we need
                remaining = max_messages - len(message_ids)
                # Gmail max per page is 500
                fetch_count = min(remaining, 500)

                response = (
                    self.gmail_service.service.users()
                    .messages()
                    .list(userId="me", maxResults=fetch_count, pageToken=next_page_token)
                    .execute()
                )

                batch_ids = [msg["id"] for msg in response.get("messages", [])]
                message_ids.extend(batch_ids)

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

                logger.info(f"Fetched {len(message_ids)} messages so far...")

            total = len(message_ids)

            logger.info(f"Found {total} messages to sync")
            self.update_sync_state(total_messages=total)

            # Process in batches
            synced = 0
            failed = 0

            for i in range(0, total, batch_size):
                batch = message_ids[i : i + batch_size]
                logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} messages)")

                for msg_id in batch:
                    try:
                        self._sync_single_message(msg_id)
                        synced += 1
                    except Exception as e:
                        logger.error(f"Failed to sync message {msg_id}: {e}")
                        failed += 1

                    self.update_sync_state(synced_messages=synced, failed_messages=failed)

                # Commit after each batch
                self.db.commit()

            # Update final state
            self.update_sync_state(
                status="completed",
                history_id=history_id,
            )

            logger.info(f"Initial sync completed: {synced} synced, {failed} failed out of {total}")

            return {
                "status": "completed",
                "total": total,
                "synced": synced,
                "failed": failed,
                "history_id": history_id,
            }

        except Exception as e:
            logger.error(f"Initial sync failed: {e}")
            self.update_sync_state(status="failed", error=str(e))
            raise

    # INCREMENTAL SYNC (Using Gmail History API)

    def perform_incremental_sync(self) -> dict[str, Any]:
        """
        Perform incremental sync using Gmail History API.

        This is much faster than full sync - only fetches changes since last sync.
        Should be called periodically (e.g., every 5-10 minutes).

        Returns:
            Sync summary
        """
        logger.info(f"Starting incremental sync for user {self.user.id}")

        try:
            sync_state = self.get_or_create_sync_state()

            if not sync_state.history_id:
                logger.warning("No history_id found, performing initial sync instead")
                return self.perform_initial_sync()

            self.update_sync_state(status="syncing", sync_type="incremental")

            # Get history changes
            history = (
                self.gmail_service.service.users()
                .history()
                .list(
                    userId="me",
                    startHistoryId=sync_state.history_id,
                )
                .execute()
            )

            changes = history.get("history", [])
            new_history_id = history.get("historyId")

            logger.info(f"Found {len(changes)} history changes")

            # Process changes
            synced = 0
            for change in changes:
                # Messages added
                for msg in change.get("messagesAdded", []):
                    try:
                        self._sync_single_message(msg["message"]["id"])
                        synced += 1
                    except Exception as e:
                        logger.error(f"Failed to sync added message: {e}")

                # Messages deleted
                for msg in change.get("messagesDeleted", []):
                    try:
                        self._delete_local_message(msg["message"]["id"])
                        synced += 1
                    except Exception as e:
                        logger.error(f"Failed to delete message: {e}")

                # Labels changed
                for msg in change.get("labelsAdded", []) + change.get("labelsRemoved", []):
                    try:
                        self._update_message_labels(msg["message"]["id"])
                        synced += 1
                    except Exception as e:
                        logger.error(f"Failed to update labels: {e}")

            # Update sync state
            self.update_sync_state(
                status="completed",
                history_id=new_history_id,
                synced_messages=synced,
            )

            logger.info(f"Incremental sync completed: {synced} changes processed")

            return {
                "status": "completed",
                "changes": len(changes),
                "synced": synced,
                "history_id": new_history_id,
            }

        except Exception as e:
            logger.error(f"Incremental sync failed: {e}")
            self.update_sync_state(status="failed", error=str(e))
            raise

    # SYNC INDIVIDUAL MESSAGE

    def _sync_single_message(self, gmail_id: str) -> Email:
        """
        Sync a single message from Gmail to database.

        Uses UPSERT (INSERT ... ON CONFLICT DO UPDATE) to handle duplicates.

        Args:
            gmail_id: Gmail message ID

        Returns:
            Email object
        """
        # Get message from Gmail
        message_data = self.gmail_service.get_message(gmail_id)

        # Parse date
        date_str = message_data.get("date", "")
        try:
            # Gmail date format: "Thu, 28 Nov 2024 10:30:00 +0700"
            date = parsedate_to_datetime(date_str)
        except Exception:
            date = datetime.now(timezone.utc)

        # Extract labels
        labels = message_data.get("labels", [])
        now = datetime.now(timezone.utc)

        # Prepare email data
        email_data = {
            "gmail_id": gmail_id,
            "thread_id": message_data.get("threadId", ""),
            "user_id": self.user.id,
            "subject": message_data.get("subject", ""),
            "from_email": message_data.get("from", ""),
            "to_email": message_data.get("to", ""),
            "cc": message_data.get("cc"),
            "bcc": message_data.get("bcc"),
            "reply_to": message_data.get("reply_to"),
            "snippet": message_data.get("snippet", ""),
            "body_plain": message_data.get("body", ""),
            "body_html": message_data.get("body_html"),
            "date": date,
            "internal_date": message_data.get("internal_date"),
            "size_estimate": message_data.get("size_estimate"),
            "labels": labels,
            "is_unread": "UNREAD" in labels,
            "is_starred": "STARRED" in labels,
            "is_important": "IMPORTANT" in labels,
            "is_draft": "DRAFT" in labels,
            "has_attachments": message_data.get("has_attachments", False),
            "last_synced_at": now,
        }

        # Use PostgreSQL UPSERT: INSERT ... ON CONFLICT DO UPDATE
        stmt = pg_insert(Email).values(**email_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["gmail_id"],  # Conflict on unique gmail_id
            set_={
                "subject": stmt.excluded.subject,
                "from_email": stmt.excluded.from_email,
                "to_email": stmt.excluded.to_email,
                "cc": stmt.excluded.cc,
                "bcc": stmt.excluded.bcc,
                "reply_to": stmt.excluded.reply_to,
                "snippet": stmt.excluded.snippet,
                "body_plain": stmt.excluded.body_plain,
                "body_html": stmt.excluded.body_html,
                "date": stmt.excluded.date,
                "internal_date": stmt.excluded.internal_date,
                "size_estimate": stmt.excluded.size_estimate,
                "labels": stmt.excluded.labels,
                "is_unread": stmt.excluded.is_unread,
                "is_starred": stmt.excluded.is_starred,
                "is_important": stmt.excluded.is_important,
                "is_draft": stmt.excluded.is_draft,
                "has_attachments": stmt.excluded.has_attachments,
                "last_synced_at": stmt.excluded.last_synced_at,
            },
        )

        self.db.execute(stmt)
        self.db.commit()

        # Fetch the email back from database
        return self.db.query(Email).filter_by(gmail_id=gmail_id).first()

    def _delete_local_message(self, gmail_id: str) -> None:
        """Delete message from local database."""
        email = self.db.query(Email).filter_by(gmail_id=gmail_id, user_id=self.user.id).first()
        if email:
            self.db.delete(email)
            self.db.commit()

    def _update_message_labels(self, gmail_id: str) -> None:
        """Update message labels from Gmail."""
        email = self.db.query(Email).filter_by(gmail_id=gmail_id, user_id=self.user.id).first()
        if email:
            message_data = self.gmail_service.get_message(gmail_id)
            labels = message_data.get("labels", [])
            email.labels = labels
            email.is_unread = "UNREAD" in labels
            email.is_starred = "STARRED" in labels
            email.is_important = "IMPORTANT" in labels
            self.db.commit()

    # SYNC LABELS

    def _sync_labels(self) -> None:
        """Sync Gmail labels to database."""
        logger.info("Syncing labels...")

        labels = self.gmail_service.get_labels()

        for label_data in labels:
            existing = (
                self.db.query(GmailLabel)
                .filter_by(
                    user_id=self.user.id,
                    gmail_label_id=label_data["id"],
                )
                .first()
            )

            if existing:
                existing.name = label_data["name"]
                existing.type = label_data.get("type")
            else:
                label = GmailLabel(
                    user_id=self.user.id,
                    gmail_label_id=label_data["id"],
                    name=label_data["name"],
                    type=label_data.get("type"),
                )
                self.db.add(label)

        self.db.commit()
        logger.info(f"Synced {len(labels)} labels")

    # QUERY HELPERS

    def get_emails(
        self,
        limit: int = 20,
        offset: int = 0,
        label: str | None = None,
        unread_only: bool = False,
        starred_only: bool = False,
    ) -> list[Email]:
        """
        Get emails from local database (fast!).

        Args:
            limit: Number of emails to return
            offset: Offset for pagination
            label: Filter by label (e.g., "INBOX", "SENT")
            unread_only: Only return unread emails
            starred_only: Only return starred emails

        Returns:
            List of Email objects
        """
        query = self.db.query(Email).filter_by(user_id=self.user.id)

        if label:
            # Normalize label to handle common system labels
            label_upper = label.upper()
            system_labels = {"INBOX", "SENT", "TRASH", "DRAFT", "STARRED", "IMPORTANT", "SPAM"}

            # If it's a known system label, use the uppercase version
            # Otherwise use the label as provided (but also try uppercase just in case)
            search_label = label_upper if label_upper in system_labels else label

            query = query.filter(Email.labels.contains([search_label]))

        if unread_only:
            query = query.filter_by(is_unread=True)
        if starred_only:
            query = query.filter_by(is_starred=True)

        query = query.order_by(desc(Email.date))
        query = query.limit(limit).offset(offset)

        return query.all()

    def get_unread_count(self) -> int:
        """Get unread count from local database (instant!)."""
        return self.db.query(Email).filter_by(user_id=self.user.id, is_unread=True).count()

    def search_emails(self, query: str, limit: int = 20) -> list[Email]:
        """
        Search emails in local database.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of matching emails
        """
        # Simple search in subject, from, to, body
        search_pattern = f"%{query}%"

        return (
            self.db.query(Email)
            .filter(
                and_(
                    Email.user_id == self.user.id,
                    (
                        Email.subject.ilike(search_pattern)
                        | Email.from_email.ilike(search_pattern)
                        | Email.to_email.ilike(search_pattern)
                        | Email.body_plain.ilike(search_pattern)
                    ),
                )
            )
            .order_by(desc(Email.date))
            .limit(limit)
            .all()
        )
