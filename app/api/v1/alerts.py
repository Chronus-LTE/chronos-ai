"""
Alerts API endpoints for proactive suggestions.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.database import get_db
from app.models.alert import Alert
from app.models.user import User

router = APIRouter(prefix="/alerts", tags=["Alerts"])


# ============================================================================
# MODELS
# ============================================================================


class AlertResponse(BaseModel):
    """Response model for alert data."""

    id: int
    type: str
    priority: str
    title: str
    message: str
    context: str | None = None
    is_read: bool
    is_dismissed: bool
    is_actioned: bool
    created_at: datetime
    expires_at: datetime | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class AlertListResponse(BaseModel):
    """Response model for list of alerts."""

    alerts: list[AlertResponse]
    count: int
    unread_count: int


class AlertActionRequest(BaseModel):
    """Request model for alert actions."""

    action: str  # read, dismiss, action


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    include_read: bool = False,
    include_dismissed: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all alerts for the current user.

    Args:
        include_read: Include read alerts (default: False)
        include_dismissed: Include dismissed alerts (default: False)
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of alerts
    """
    try:
        # Build query
        query = select(Alert).where(Alert.user_id == current_user.id)

        if not include_read:
            query = query.where(Alert.is_read == False)  # noqa: E712

        if not include_dismissed:
            query = query.where(Alert.is_dismissed == False)  # noqa: E712

        # Order by priority and created_at
        query = query.order_by(
            Alert.priority.desc(),  # high > medium > low
            Alert.created_at.desc(),
        )

        result = await db.execute(query)
        alerts = result.scalars().all()

        # Count unread
        unread_query = select(Alert).where(
            Alert.user_id == current_user.id,
            Alert.is_read == False,  # noqa: E712
            Alert.is_dismissed == False,  # noqa: E712
        )
        unread_result = await db.execute(unread_query)
        unread_count = len(unread_result.scalars().all())

        return AlertListResponse(
            alerts=[AlertResponse.from_orm(alert) for alert in alerts],
            count=len(alerts),
            unread_count=unread_count,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list alerts: {e!s}",
        ) from e


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific alert by ID."""
    try:
        result = await db.execute(
            select(Alert).where(
                Alert.id == alert_id,
                Alert.user_id == current_user.id,
            )
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )

        return AlertResponse.from_orm(alert)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert: {e!s}",
        ) from e


@router.post("/{alert_id}/mark-read")
async def mark_alert_as_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an alert as read."""
    try:
        result = await db.execute(
            select(Alert).where(
                Alert.id == alert_id,
                Alert.user_id == current_user.id,
            )
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )

        alert.is_read = True
        alert.read_at = datetime.utcnow()
        await db.commit()

        return {"message": "Alert marked as read", "id": alert_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark alert as read: {e!s}",
        ) from e


@router.post("/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss an alert."""
    try:
        result = await db.execute(
            select(Alert).where(
                Alert.id == alert_id,
                Alert.user_id == current_user.id,
            )
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )

        alert.is_dismissed = True
        alert.dismissed_at = datetime.utcnow()
        await db.commit()

        return {"message": "Alert dismissed", "id": alert_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dismiss alert: {e!s}",
        ) from e


@router.post("/{alert_id}/action")
async def mark_alert_actioned(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark that user took action on this alert."""
    try:
        result = await db.execute(
            select(Alert).where(
                Alert.id == alert_id,
                Alert.user_id == current_user.id,
            )
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )

        alert.is_actioned = True
        alert.actioned_at = datetime.utcnow()
        alert.is_read = True
        alert.read_at = datetime.utcnow()
        await db.commit()

        return {"message": "Alert marked as actioned", "id": alert_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark alert as actioned: {e!s}",
        ) from e


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert."""
    try:
        result = await db.execute(
            select(Alert).where(
                Alert.id == alert_id,
                Alert.user_id == current_user.id,
            )
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )

        await db.delete(alert)
        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete alert: {e!s}",
        ) from e


@router.get("/stats/summary")
async def get_alerts_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary statistics of alerts."""
    try:
        # Total alerts
        total_result = await db.execute(select(Alert).where(Alert.user_id == current_user.id))
        total = len(total_result.scalars().all())

        # Unread alerts
        unread_result = await db.execute(
            select(Alert).where(
                Alert.user_id == current_user.id,
                Alert.is_read == False,  # noqa: E712
            )
        )
        unread = len(unread_result.scalars().all())

        # By priority
        high_result = await db.execute(
            select(Alert).where(
                Alert.user_id == current_user.id,
                Alert.priority == "high",
                Alert.is_dismissed == False,  # noqa: E712
            )
        )
        high_priority = len(high_result.scalars().all())

        return {
            "total": total,
            "unread": unread,
            "high_priority": high_priority,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts summary: {e!s}",
        ) from e
