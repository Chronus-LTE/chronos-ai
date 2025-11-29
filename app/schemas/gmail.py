"""
Pydantic schemas for Gmail API.

These schemas provide:
- Request/response validation
- API documentation
- Type safety
- Serialization
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# REQUEST SCHEMAS


class SendEmailRequest(BaseModel):
    """Request to send an email."""

    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    body: str = Field(..., min_length=1, description="Email body (plain text)")
    cc: str | None = Field(None, description="CC recipients (comma-separated)")
    bcc: str | None = Field(None, description="BCC recipients (comma-separated)")
    html_body: str | None = Field(None, description="HTML version of body")


class CreateDraftRequest(BaseModel):
    """Request to create a draft."""

    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    body: str = Field(..., min_length=1, description="Email body (plain text)")
    cc: str | None = Field(None, description="CC recipients")
    bcc: str | None = Field(None, description="BCC recipients")
    html_body: str | None = Field(None, description="HTML version of body")


class ReplyRequest(BaseModel):
    """Request to reply to a thread."""

    body: str = Field(..., min_length=1, description="Reply body")
    html_body: str | None = Field(None, description="HTML version of reply")


class ForwardRequest(BaseModel):
    """Request to forward an email."""

    to: EmailStr = Field(..., description="Forward to email address")
    body: str | None = Field(None, description="Additional message")


class UpdateLabelsRequest(BaseModel):
    """Request to update email labels."""

    add_labels: list[str] = Field(default_factory=list, description="Labels to add")
    remove_labels: list[str] = Field(default_factory=list, description="Labels to remove")


class SearchRequest(BaseModel):
    """Request to search emails."""

    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(20, ge=1, le=100, description="Max results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class SyncRequest(BaseModel):
    """Request to start sync."""

    force_full: bool = Field(False, description="Force full sync instead of incremental")
    max_messages: int = Field(100, ge=1, le=10000, description="Max messages for initial sync")


# RESPONSE SCHEMAS


class AttachmentResponse(BaseModel):
    """Attachment metadata."""

    id: int
    filename: str
    mime_type: str | None = None
    size: int | None = None
    is_downloaded: bool = False

    class Config:
        from_attributes = True


class EmailResponse(BaseModel):
    """Email response model."""

    id: int
    gmail_id: str
    thread_id: str
    subject: str
    from_email: str = Field(..., alias="from")
    to_email: str = Field(..., alias="to")
    cc: str | None = None
    date: datetime
    snippet: str
    body_plain: str | None = None
    labels: list[str] = Field(default_factory=list)
    is_unread: bool = Field(..., alias="isUnread")
    is_starred: bool = Field(..., alias="isStarred")
    is_important: bool = False
    has_attachments: bool = False
    attachments: list[AttachmentResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
        populate_by_name = True


class EmailListResponse(BaseModel):
    """Response for email list."""

    emails: list[EmailResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class ThreadMessageResponse(BaseModel):
    """Single message in a thread."""

    id: int
    gmail_id: str
    subject: str
    from_email: str = Field(..., alias="from")
    date: datetime
    snippet: str
    body_plain: str | None = None
    is_unread: bool

    class Config:
        from_attributes = True
        populate_by_name = True


class ThreadResponse(BaseModel):
    """Email thread response."""

    id: str
    subject: str
    snippet: str
    message_count: int
    messages: list[ThreadMessageResponse]
    participants: list[str] = Field(default_factory=list)
    is_unread: bool
    has_attachments: bool
    first_message_date: datetime | None = None
    last_message_date: datetime | None = None

    class Config:
        from_attributes = True


class LabelResponse(BaseModel):
    """Gmail label response."""

    id: str
    name: str
    type: str | None = None
    total_messages: int = 0
    unread_messages: int = 0

    class Config:
        from_attributes = True


class LabelsListResponse(BaseModel):
    """Response for labels list."""

    labels: list[LabelResponse]
    count: int


class UnreadCountResponse(BaseModel):
    """Response for unread count."""

    unread_count: int


class SyncStatusResponse(BaseModel):
    """Response for sync status."""

    status: str  # pending, syncing, completed, failed
    sync_type: str | None = None
    total_messages: int = 0
    synced_messages: int = 0
    failed_messages: int = 0
    progress_percentage: float = 0.0
    last_sync_date: datetime | None = None
    last_error: str | None = None

    class Config:
        from_attributes = True


class SendEmailResponse(BaseModel):
    """Response after sending email."""

    message: str
    id: str
    thread_id: str = Field(..., alias="threadId")

    class Config:
        populate_by_name = True


class DraftResponse(BaseModel):
    """Draft response."""

    id: str
    message_id: str
    to: str
    subject: str
    snippet: str

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    """Gmail profile response."""

    email: str
    messages_total: int
    threads_total: int
    history_id: str | None = None


class SearchResponse(BaseModel):
    """Search results response."""

    query: str
    results: list[EmailResponse]
    count: int
    total: int
    has_more: bool


class EmailStatsResponse(BaseModel):
    """Email statistics response."""

    total_emails: int
    unread_emails: int
    starred_emails: int
    total_threads: int
    emails_sent_today: int
    emails_received_today: int
    top_senders: list[dict[str, int]]  # [{"email": "...", "count": 10}]
    labels_distribution: dict[str, int]  # {"INBOX": 100, "SENT": 50}


# WEBHOOK SCHEMAS


class GmailWebhookNotification(BaseModel):
    """Gmail push notification webhook payload."""

    email_address: str = Field(..., alias="emailAddress")
    history_id: str = Field(..., alias="historyId")

    class Config:
        populate_by_name = True


class WebhookMessage(BaseModel):
    """Pub/Sub message wrapper."""

    message: dict
    subscription: str
