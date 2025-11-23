"""
Calendar API endpoints for CRUD operations using Unix timestamps.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.auth import get_current_user
from app.models.user import User
from app.services.google.calendar_service import GoogleCalendarService

router = APIRouter(prefix="/calendar", tags=["Calendar"])


class CreateEventRequest(BaseModel):
    """Request model for creating an event using Unix timestamps."""

    summary: str = Field(..., description="Event title")
    start_timestamp: int = Field(
        ..., description="Start time as Unix timestamp (seconds since epoch)"
    )
    end_timestamp: int | None = Field(
        None, description="End time as Unix timestamp (optional, defaults to start + 1 hour)"
    )
    description: str | None = Field(None, description="Event description")


class UpdateEventRequest(BaseModel):
    """Request model for updating an event using Unix timestamps."""

    summary: str | None = Field(None, description="New event title")
    start_timestamp: int | None = Field(None, description="New start time as Unix timestamp")
    end_timestamp: int | None = Field(None, description="New end time as Unix timestamp")
    description: str | None = Field(None, description="New event description")


class EventResponse(BaseModel):
    """Response model for event data using Unix timestamps."""

    id: str
    summary: str
    start_timestamp: int = Field(..., description="Start time as Unix timestamp")
    end_timestamp: int = Field(..., description="End time as Unix timestamp")
    description: str | None = None
    html_link: str | None = None


class EventListResponse(BaseModel):
    """Response model for list of events."""

    events: list[EventResponse]


def get_calendar_service(current_user: User = Depends(get_current_user)) -> GoogleCalendarService:
    """Get calendar service for the current user."""
    if not current_user.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Calendar access not found. Please login with Google again.",
        )
    return GoogleCalendarService(
        token=current_user.google_access_token,
        refresh_token=current_user.google_refresh_token,
    )


def parse_google_event_time(time_dict: dict) -> int:
    """Parse Google Calendar event time to Unix timestamp."""
    if "dateTime" in time_dict:
        dt = datetime.fromisoformat(time_dict["dateTime"].replace("Z", "+00:00"))
        return int(dt.timestamp())
    # For all-day events
    dt = datetime.fromisoformat(time_dict["date"])
    return int(dt.replace(tzinfo=timezone.utc).timestamp())


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    request: CreateEventRequest,
    calendar_service: GoogleCalendarService = Depends(get_calendar_service),
):
    """
    Create a new calendar event.

    Times should be provided as Unix timestamps (seconds since epoch).
    Example: 1700000000 represents 2023-11-14 22:13:20 UTC
    """
    try:
        start_time = datetime.fromtimestamp(request.start_timestamp, tz=timezone.utc)
        end_time = None
        if request.end_timestamp:
            end_time = datetime.fromtimestamp(request.end_timestamp, tz=timezone.utc)

        event = calendar_service.create_event(
            summary=request.summary,
            start_time=start_time,
            end_time=end_time,
            description=request.description,
        )

        return EventResponse(
            id=event["id"],
            summary=event["summary"],
            start_timestamp=parse_google_event_time(event["start"]),
            end_timestamp=parse_google_event_time(event["end"]),
            description=event.get("description"),
            html_link=event.get("htmlLink"),
        )
    except (ValueError, OSError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid timestamp: {e!s}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {e!s}",
        ) from e


@router.get("/events", response_model=EventListResponse)
async def list_events(
    max_results: int = 10,
    calendar_service: GoogleCalendarService = Depends(get_calendar_service),
):
    """List upcoming calendar events with Unix timestamps."""
    try:
        events = calendar_service.list_events(max_results=max_results)
        return EventListResponse(
            events=[
                EventResponse(
                    id=event["id"],
                    summary=event["summary"],
                    start_timestamp=parse_google_event_time(event["start"]),
                    end_timestamp=parse_google_event_time(event["end"]),
                    description=event.get("description"),
                    html_link=event.get("htmlLink"),
                )
                for event in events
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list events: {e!s}",
        ) from e


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    calendar_service: GoogleCalendarService = Depends(get_calendar_service),
):
    """Get a specific calendar event by ID with Unix timestamps."""
    try:
        event = calendar_service.get_event(event_id)
        return EventResponse(
            id=event["id"],
            summary=event["summary"],
            start_timestamp=parse_google_event_time(event["start"]),
            end_timestamp=parse_google_event_time(event["end"]),
            description=event.get("description"),
            html_link=event.get("htmlLink"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Event not found: {e!s}"
        ) from e


@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    request: UpdateEventRequest,
    calendar_service: GoogleCalendarService = Depends(get_calendar_service),
):
    """
    Update an existing calendar event.

    Times should be provided as Unix timestamps (seconds since epoch).
    """
    try:
        start_time = None
        end_time = None

        if request.start_timestamp is not None:
            start_time = datetime.fromtimestamp(request.start_timestamp, tz=timezone.utc)
        if request.end_timestamp is not None:
            end_time = datetime.fromtimestamp(request.end_timestamp, tz=timezone.utc)

        event = calendar_service.update_event(
            event_id=event_id,
            summary=request.summary,
            start_time=start_time,
            end_time=end_time,
            description=request.description,
        )

        return EventResponse(
            id=event["id"],
            summary=event["summary"],
            start_timestamp=parse_google_event_time(event["start"]),
            end_timestamp=parse_google_event_time(event["end"]),
            description=event.get("description"),
            html_link=event.get("htmlLink"),
        )
    except (ValueError, OSError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid timestamp: {e!s}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event: {e!s}",
        ) from e


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    calendar_service: GoogleCalendarService = Depends(get_calendar_service),
):
    """Delete a calendar event."""
    try:
        calendar_service.delete_event(event_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {e!s}",
        ) from e
