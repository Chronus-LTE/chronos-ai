"""
Email models for storing Gmail data locally.

This enables:
- Fast queries without hitting Gmail API
- Offline access to email data
- Advanced search and filtering
- Analytics and insights
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Email(Base):
    """Email message model - stores individual emails."""

    __tablename__ = "emails"

    # Primary keys
    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String, unique=True, nullable=False, index=True)  # Gmail message ID
    thread_id = Column(String, nullable=False, index=True)  # Gmail thread ID

    # Ownership
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)

    # Email headers
    subject = Column(String, nullable=False, index=True)
    from_email = Column(String, nullable=False, index=True)
    to_email = Column(String, nullable=False)
    cc = Column(String, nullable=True)
    bcc = Column(String, nullable=True)
    reply_to = Column(String, nullable=True)

    # Content
    snippet = Column(String, nullable=True)  # Short preview
    body_plain = Column(Text, nullable=True)  # Plain text body
    body_html = Column(Text, nullable=True)  # HTML body

    # Metadata
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    internal_date = Column(DateTime(timezone=True), nullable=True)  # Gmail internal date
    size_estimate = Column(Integer, nullable=True)  # Size in bytes

    # Labels (stored as JSONB array for flexibility and better indexing)
    labels = Column(JSONB, nullable=True, default=list)  # ["INBOX", "UNREAD", etc.]

    # Flags
    is_unread = Column(Boolean, default=True, index=True)
    is_starred = Column(Boolean, default=False, index=True)
    is_important = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=False)
    has_attachments = Column(Boolean, default=False, index=True)

    # Full message data (for backup/reference)
    raw_headers = Column(JSON, nullable=True)  # All headers as JSON
    raw_payload = Column(JSON, nullable=True)  # Full Gmail payload (optional)

    # Sync tracking
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now())

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="emails")
    attachments = relationship(
        "EmailAttachment", back_populates="email", cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_user_date", "user_id", "date"),
        Index("idx_user_unread", "user_id", "is_unread"),
        Index("idx_user_thread", "user_id", "thread_id"),
        Index("idx_labels", "labels", postgresql_using="gin", postgresql_ops={"labels": "jsonb_path_ops"}),
    )

    def __repr__(self):
        return f"<Email {self.gmail_id} - {self.subject[:50]}>"


class EmailAttachment(Base):
    """Email attachment model - stores attachment metadata."""

    __tablename__ = "email_attachments"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False, index=True)
    gmail_attachment_id = Column(String, nullable=False)  # Gmail attachment ID

    # Attachment info
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True)  # Size in bytes

    # Storage (optional - can download and store locally)
    file_path = Column(String, nullable=True)  # Local file path if downloaded
    is_downloaded = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    email = relationship("Email", back_populates="attachments")

    def __repr__(self):
        return f"<Attachment {self.filename}>"


class EmailThread(Base):
    """Email thread model - groups related emails."""

    __tablename__ = "email_threads"

    id = Column(Integer, primary_key=True, index=True)
    gmail_thread_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)

    # Thread metadata
    subject = Column(String, nullable=False)  # Thread subject (from first email)
    snippet = Column(String, nullable=True)  # Latest snippet
    message_count = Column(Integer, default=0)

    # Participants (JSON array of email addresses)
    participants = Column(JSON, nullable=True, default=list)

    # Flags
    is_unread = Column(Boolean, default=True, index=True)
    is_starred = Column(Boolean, default=False)
    has_attachments = Column(Boolean, default=False)

    # Dates
    first_message_date = Column(DateTime(timezone=True), nullable=True)
    last_message_date = Column(DateTime(timezone=True), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="email_threads")

    __table_args__ = (Index("idx_user_last_message", "user_id", "last_message_date"),)

    def __repr__(self):
        return f"<Thread {self.gmail_thread_id} - {self.subject[:50]}>"


class GmailSyncState(Base):
    """Tracks Gmail sync state per user."""

    __tablename__ = "gmail_sync_states"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), unique=True, nullable=False, index=True)

    # Sync status
    status = Column(
        String,
        nullable=False,
        default="pending",
        index=True,
    )  # pending, syncing, completed, failed
    sync_type = Column(String, nullable=True)  # initial, incremental, manual

    # Progress tracking
    total_messages = Column(Integer, default=0)
    synced_messages = Column(Integer, default=0)
    failed_messages = Column(Integer, default=0)

    # Gmail history tracking (for incremental sync)
    history_id = Column(String, nullable=True)  # Gmail historyId for incremental sync
    last_sync_date = Column(DateTime(timezone=True), nullable=True)

    # Error tracking
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="gmail_sync_state", uselist=False)

    def __repr__(self):
        return f"<SyncState user={self.user_id} status={self.status}>"


class GmailLabel(Base):
    """Stores Gmail labels for each user."""

    __tablename__ = "gmail_labels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    gmail_label_id = Column(String, nullable=False)  # Gmail label ID

    # Label info
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)  # system, user
    message_list_visibility = Column(String, nullable=True)
    label_list_visibility = Column(String, nullable=True)

    # Stats
    total_messages = Column(Integer, default=0)
    unread_messages = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="gmail_labels")

    __table_args__ = (Index("idx_user_label", "user_id", "gmail_label_id", unique=True),)

    def __repr__(self):
        return f"<Label {self.name}>"
