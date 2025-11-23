"""
Gmail API endpoints for managing emails - Complete integration like Notion/Lark.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.api.v1.auth import get_current_user
from app.models.user import User
from app.services.google.gmail_service import GoogleGmailService

router = APIRouter(prefix="/gmail", tags=["Gmail"])


# ============================================================================
# MODELS
# ============================================================================


class SendEmailRequest(BaseModel):
    """Request model for sending an email."""

    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (plain text)")


class CreateDraftRequest(BaseModel):
    """Request model for creating a draft."""

    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (plain text)")
    cc: str | None = Field(None, description="CC recipients")
    bcc: str | None = Field(None, description="BCC recipients")
    html_body: str | None = Field(None, description="HTML version of body")


class ReplyRequest(BaseModel):
    """Request model for replying to thread."""

    body: str = Field(..., description="Reply body")


class EmailResponse(BaseModel):
    """Response model for email data."""

    id: str
    thread_id: str = Field(..., alias="threadId")
    subject: str
    from_email: str = Field(..., alias="from")
    to_email: str = Field(..., alias="to")
    date: str
    snippet: str
    body: str | None = None
    labels: list[str]
    is_unread: bool = Field(..., alias="isUnread")

    class Config:
        """Pydantic config."""

        populate_by_name = True


class EmailListResponse(BaseModel):
    """Response model for list of emails."""

    emails: list[EmailResponse]
    count: int


class UnreadCountResponse(BaseModel):
    """Response model for unread count."""

    unread_count: int


class LabelResponse(BaseModel):
    """Response model for Gmail label."""

    id: str
    name: str
    type: str | None = None


class LabelsListResponse(BaseModel):
    """Response model for list of labels."""

    labels: list[LabelResponse]


# ============================================================================
# DEPENDENCIES
# ============================================================================


def get_gmail_service(current_user: User = Depends(get_current_user)) -> GoogleGmailService:
    """Get Gmail service for the current user."""
    if not current_user.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail access not found. Please login with Google again.",
        )
    return GoogleGmailService(
        token=current_user.google_access_token,
        refresh_token=current_user.google_refresh_token,
    )


# ============================================================================
# MESSAGES - Basic Operations
# ============================================================================


@router.get("/messages", response_model=EmailListResponse)
async def list_messages(
    max_results: int = 20,
    query: str = "",
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """
    List messages in user's mailbox.

    Args:
        max_results: Maximum number of messages to return (default: 20)
        query: Gmail search query (e.g., "is:unread", "from:example@gmail.com")
        gmail_service: Gmail service instance

    Returns:
        List of email messages
    """
    try:
        messages = gmail_service.list_messages(max_results=max_results, query=query)
        return EmailListResponse(
            emails=[EmailResponse(**msg) for msg in messages],
            count=len(messages),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list messages: {e!s}",
        ) from e


@router.get("/messages/search", response_model=EmailListResponse)
async def search_messages(
    query: str,
    max_results: int = 20,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """
    Search messages using Gmail search syntax.

    Args:
        query: Gmail search query
            Examples:
            - "is:unread" - unread messages
            - "from:example@gmail.com" - from specific sender
            - "subject:meeting" - subject contains "meeting"
            - "has:attachment" - has attachments
            - "after:2024/01/01" - after specific date
        max_results: Maximum number of results (default: 20)
        gmail_service: Gmail service instance

    Returns:
        List of matching email messages
    """
    try:
        messages = gmail_service.search_messages(query=query, max_results=max_results)
        return EmailListResponse(
            emails=[EmailResponse(**msg) for msg in messages],
            count=len(messages),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search messages: {e!s}",
        ) from e


@router.get("/messages/{message_id}", response_model=EmailResponse)
async def get_message(
    message_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """
    Get a specific message by ID.

    Args:
        message_id: Message ID
        gmail_service: Gmail service instance

    Returns:
        Email message details
    """
    try:
        message = gmail_service.get_message(message_id)
        return EmailResponse(**message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found: {e!s}",
        ) from e


@router.post("/messages/send", status_code=status.HTTP_201_CREATED)
async def send_message(
    request: SendEmailRequest,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """
    Send an email message directly.

    Args:
        request: Email details (to, subject, body)
        gmail_service: Gmail service instance

    Returns:
        Sent message details
    """
    try:
        result = gmail_service.send_message(
            to=request.to,
            subject=request.subject,
            body=request.body,
        )
        return {
            "message": "Email sent successfully",
            "id": result.get("id"),
            "threadId": result.get("threadId"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {e!s}",
        ) from e


@router.post("/messages/{message_id}/mark-read", status_code=status.HTTP_200_OK)
async def mark_as_read(
    message_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Mark a message as read."""
    try:
        gmail_service.mark_as_read(message_id)
        return {"message": "Message marked as read", "id": message_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark message as read: {e!s}",
        ) from e


@router.post("/messages/{message_id}/mark-unread", status_code=status.HTTP_200_OK)
async def mark_as_unread(
    message_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Mark a message as unread."""
    try:
        gmail_service.mark_as_unread(message_id)
        return {"message": "Message marked as unread", "id": message_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark message as unread: {e!s}",
        ) from e


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Delete a message (move to trash)."""
    try:
        gmail_service.delete_message(message_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {e!s}",
        ) from e


# ============================================================================
# DRAFT MANAGEMENT (like Notion/Lark)
# ============================================================================


@router.post("/drafts", status_code=status.HTTP_201_CREATED)
async def create_draft(
    request: CreateDraftRequest,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """
    Create an email draft (not sent yet).

    This allows users to preview and confirm before sending - like Notion/Lark.
    """
    try:
        draft = gmail_service.create_draft(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            html_body=request.html_body,
        )
        return {
            "message": "Draft created successfully",
            **draft,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create draft: {e!s}",
        ) from e


@router.get("/drafts")
async def list_drafts(
    max_results: int = 20,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """List all draft emails."""
    try:
        drafts = gmail_service.list_drafts(max_results=max_results)
        return {"drafts": drafts, "count": len(drafts)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list drafts: {e!s}",
        ) from e


@router.get("/drafts/{draft_id}")
async def get_draft(
    draft_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Get a specific draft by ID."""
    try:
        return gmail_service.get_draft(draft_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Draft not found: {e!s}",
        ) from e


@router.post("/drafts/{draft_id}/send")
async def send_draft(
    draft_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Send a draft email after user confirms."""
    try:
        result = gmail_service.send_draft(draft_id)
        return {
            "message": "Draft sent successfully",
            "id": result.get("id"),
            "threadId": result.get("threadId"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send draft: {e!s}",
        ) from e


@router.delete("/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft(
    draft_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Delete a draft."""
    try:
        gmail_service.delete_draft(draft_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete draft: {e!s}",
        ) from e


# ============================================================================
# THREADING & CONVERSATION (like Notion/Lark)
# ============================================================================


@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Get all messages in a thread/conversation."""
    try:
        return gmail_service.get_thread(thread_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread not found: {e!s}",
        ) from e


@router.post("/threads/{thread_id}/reply")
async def reply_to_thread(
    thread_id: str,
    request: ReplyRequest,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Reply to an email thread."""
    try:
        result = gmail_service.reply_to_thread(thread_id, request.body)
        return {
            "message": "Reply sent successfully",
            "id": result.get("id"),
            "threadId": result.get("threadId"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reply to thread: {e!s}",
        ) from e


# ============================================================================
# ADVANCED FEATURES (like Notion/Lark)
# ============================================================================


@router.post("/messages/{message_id}/star")
async def star_message(
    message_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Star/favorite a message."""
    try:
        gmail_service.star_message(message_id)
        return {"message": "Message starred", "id": message_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to star message: {e!s}",
        ) from e


@router.post("/messages/{message_id}/unstar")
async def unstar_message(
    message_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Unstar a message."""
    try:
        gmail_service.unstar_message(message_id)
        return {"message": "Message unstarred", "id": message_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unstar message: {e!s}",
        ) from e


@router.post("/messages/{message_id}/archive")
async def archive_message(
    message_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Archive a message (remove from inbox)."""
    try:
        gmail_service.archive_message(message_id)
        return {"message": "Message archived", "id": message_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive message: {e!s}",
        ) from e


@router.get("/messages/{message_id}/attachments")
async def get_attachments(
    message_id: str,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Get list of attachments in a message."""
    try:
        attachments = gmail_service.get_attachments(message_id)
        return {"attachments": attachments, "count": len(attachments)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attachments: {e!s}",
        ) from e


# ============================================================================
# LABELS & PROFILE
# ============================================================================


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Get count of unread messages."""
    try:
        count = gmail_service.get_unread_count()
        return UnreadCountResponse(unread_count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread count: {e!s}",
        ) from e


@router.get("/labels", response_model=LabelsListResponse)
async def get_labels(
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Get all labels in user's mailbox."""
    try:
        labels = gmail_service.get_labels()
        return LabelsListResponse(
            labels=[
                LabelResponse(
                    id=label["id"],
                    name=label["name"],
                    type=label.get("type"),
                )
                for label in labels
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get labels: {e!s}",
        ) from e


@router.get("/profile")
async def get_profile(
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
):
    """Get user's Gmail profile information."""
    try:
        return gmail_service.get_profile()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {e!s}",
        ) from e
