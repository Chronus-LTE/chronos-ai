"""
Unified Gmail API - Clean and Simple.

Provides basic Gmail functionality:
- List/read emails (from local DB - fast!)
- Send emails
- Mark as read/unread
- Star/unstar
- Delete emails
- Sync management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.database import get_sync_db
from app.models.email import Email, GmailSyncState
from app.models.user import User
from app.schemas.gmail import (
    EmailListResponse,
    EmailResponse,
    SendEmailRequest,
    SendEmailResponse,
    SyncRequest,
    SyncStatusResponse,
    UnreadCountResponse,
)
from app.services.email_sync_service import EmailSyncService
from app.services.google.gmail_service import GoogleGmailService
from app.tasks.gmail_sync_tasks import incremental_gmail_sync, initial_gmail_sync

router = APIRouter(prefix="/gmail", tags=["Gmail"])


# DEPENDENCIES


def get_gmail_service(current_user: User = Depends(get_current_user)) -> GoogleGmailService:
    """Get Gmail service for the current user."""
    if not current_user.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail not connected. Please login with Google first.",
        )
    return GoogleGmailService(
        token=current_user.google_access_token,
        refresh_token=current_user.google_refresh_token,
    )


def get_sync_service(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
) -> EmailSyncService:
    """Get email sync service."""
    if not current_user.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail not connected. Please login with Google first.",
        )
    return EmailSyncService(db=db, user=current_user)


# SYNC MANAGEMENT


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
def start_sync(
    request: SyncRequest = SyncRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """
    Start Gmail sync (initial or incremental).

    - First time: Performs full sync
    - Subsequent times: Performs incremental sync (faster)
    - Set force_full=true to force a full sync

    Returns immediately with 202 Accepted.
    Check /gmail/sync/status for progress.
    """
    # Check if sync is already running
    sync_state = db.query(GmailSyncState).filter_by(user_id=current_user.id).first()

    if sync_state and sync_state.status == "syncing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sync already in progress",
        )

    # Determine sync type
    if request.force_full or not sync_state or not sync_state.history_id:
        # Initial full sync
        initial_gmail_sync.delay(current_user.id, max_messages=request.max_messages)
        sync_type = "initial"
    else:
        # Incremental sync
        incremental_gmail_sync.delay(current_user.id)
        sync_type = "incremental"

    return {
        "message": f"{sync_type.capitalize()} sync started",
        "sync_type": sync_type,
        "status": "syncing",
    }


@router.get("/sync/status", response_model=SyncStatusResponse)
def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Get current sync status."""
    sync_state = db.query(GmailSyncState).filter_by(user_id=current_user.id).first()

    if not sync_state:
        return SyncStatusResponse(
            status="pending",
            sync_type=None,
            total_messages=0,
            synced_messages=0,
            failed_messages=0,
            progress_percentage=0.0,
        )

    # Calculate progress
    progress = 0.0
    if sync_state.total_messages > 0:
        progress = (sync_state.synced_messages / sync_state.total_messages) * 100

    return SyncStatusResponse(
        status=sync_state.status,
        sync_type=sync_state.sync_type,
        total_messages=sync_state.total_messages,
        synced_messages=sync_state.synced_messages,
        failed_messages=sync_state.failed_messages,
        progress_percentage=round(progress, 2),
        last_sync_date=sync_state.last_sync_date,
        last_error=sync_state.last_error,
    )


# READ EMAILS (from local DB - FAST!)


@router.get("/emails", response_model=EmailListResponse)
def list_emails(
    limit: int = Query(20, ge=1, le=100, description="Number of emails to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    label: str | None = Query(None, description="Filter by label (e.g., INBOX, SENT)"),
    unread_only: bool = Query(False, description="Only return unread emails"),
    starred_only: bool = Query(False, description="Only return starred emails"),
    sync_service: EmailSyncService = Depends(get_sync_service),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user),
    response: Response = None,
):
    """
    List emails from local database (FAST!).

    This queries the local database instead of Gmail API.
    Much faster and no rate limits!
    """
    # Prevent caching
    if response:
        response.headers["Cache-Control"] = "no-store"

    # Get emails from local DB
    emails = sync_service.get_emails(
        limit=limit,
        offset=offset,
        label=label,
        unread_only=unread_only,
        starred_only=starred_only,
    )

    # Get total count
    query = db.query(Email).filter_by(user_id=current_user.id)
    if label:
        # Normalize label to handle common system labels
        label_upper = label.upper()
        system_labels = {"INBOX", "SENT", "TRASH", "DRAFT", "STARRED", "IMPORTANT", "SPAM"}
        search_label = label_upper if label_upper in system_labels else label

        query = query.filter(Email.labels.contains([search_label]))
    if unread_only:
        query = query.filter_by(is_unread=True)
    if starred_only:
        query = query.filter_by(is_starred=True)
    total = query.count()

    # Convert to response
    email_responses = [EmailResponse.model_validate(email) for email in emails]

    return EmailListResponse(
        emails=email_responses,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.get("/emails/{email_id}", response_model=EmailResponse)
def get_email(
    email_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Get email detail from local database."""
    email = db.query(Email).filter_by(id=email_id, user_id=current_user.id).first()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )

    return EmailResponse.model_validate(email)


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    sync_service: EmailSyncService = Depends(get_sync_service),
):
    """Get unread count from local database (instant!)."""
    count = sync_service.get_unread_count()
    return UnreadCountResponse(unread_count=count)


# SEND EMAIL


@router.post("/send", status_code=status.HTTP_201_CREATED, response_model=SendEmailResponse)
def send_email(
    request: SendEmailRequest,
    gmail_service: GoogleGmailService = Depends(get_gmail_service),
    sync_service: EmailSyncService = Depends(get_sync_service),
    current_user: User = Depends(get_current_user),
):
    """Send an email message directly."""
    try:
        result = gmail_service.send_message(
            to=request.to,
            subject=request.subject,
            body=request.body,
        )

        # Sync the sent message immediately so it appears in the UI with correct details
        try:
            sync_service._sync_single_message(result["id"])
        except Exception:
            # If immediate sync fails, fallback to background sync
            incremental_gmail_sync.delay(current_user.id)

        return SendEmailResponse(
            message="Email sent successfully",
            id=result.get("id"),
            threadId=result.get("threadId"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {e!s}",
        ) from e


# EMAIL ACTIONS (Update both Gmail & Local DB)


@router.post("/emails/{email_id}/mark-read")
def mark_as_read(
    email_id: int,
    sync_service: EmailSyncService = Depends(get_sync_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Mark email as read (updates both Gmail and local DB)."""
    # Get email
    email = db.query(Email).filter_by(id=email_id, user_id=current_user.id).first()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )

    # Update Gmail
    sync_service.gmail_service.mark_as_read(email.gmail_id)

    # Update local DB
    email.is_unread = False
    if "UNREAD" in email.labels:
        email.labels.remove("UNREAD")
    db.commit()

    return {"message": "Email marked as read", "id": email_id}


@router.post("/emails/{email_id}/mark-unread")
def mark_as_unread(
    email_id: int,
    sync_service: EmailSyncService = Depends(get_sync_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Mark email as unread (updates both Gmail and local DB)."""
    email = db.query(Email).filter_by(id=email_id, user_id=current_user.id).first()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )

    # Update Gmail
    sync_service.gmail_service.mark_as_unread(email.gmail_id)

    # Update local DB
    email.is_unread = True
    if "UNREAD" not in email.labels:
        email.labels.append("UNREAD")
    db.commit()

    return {"message": "Email marked as unread", "id": email_id}


@router.post("/emails/{email_id}/star")
def star_email(
    email_id: int,
    sync_service: EmailSyncService = Depends(get_sync_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Star email (updates both Gmail and local DB)."""
    email = db.query(Email).filter_by(id=email_id, user_id=current_user.id).first()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )

    # Update Gmail
    sync_service.gmail_service.star_message(email.gmail_id)

    # Update local DB
    email.is_starred = True
    if "STARRED" not in email.labels:
        email.labels.append("STARRED")
    db.commit()

    return {"message": "Email starred", "id": email_id}


@router.post("/emails/{email_id}/unstar")
def unstar_email(
    email_id: int,
    sync_service: EmailSyncService = Depends(get_sync_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Unstar email (updates both Gmail and local DB)."""
    email = db.query(Email).filter_by(id=email_id, user_id=current_user.id).first()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )

    # Update Gmail
    sync_service.gmail_service.unstar_message(email.gmail_id)

    # Update local DB
    email.is_starred = False
    if "STARRED" in email.labels:
        email.labels.remove("STARRED")
    db.commit()

    return {"message": "Email unstarred", "id": email_id}


@router.delete("/emails/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email(
    email_id: int,
    sync_service: EmailSyncService = Depends(get_sync_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Delete email (move to trash in Gmail, remove from local DB)."""
    email = db.query(Email).filter_by(id=email_id, user_id=current_user.id).first()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )

    # Delete from Gmail (move to trash)
    sync_service.gmail_service.delete_message(email.gmail_id)

    if "TRASH" not in email.labels:
        email.labels.append("TRASH")

    if "INBOX" in email.labels:
        email.labels.remove("INBOX")

    db.commit()
