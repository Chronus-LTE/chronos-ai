"""
Google Calendar Service for managing calendar events.
"""

from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import settings


class GoogleCalendarService:
    """Service for interacting with Google Calendar API."""

    def __init__(self, token: str, refresh_token: str | None = None):
        """
        Initialize Calendar service with user credentials.

        Args:
            token: Access token
            refresh_token: Refresh token (optional)
        """
        self.credentials = Credentials(
            token=token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        self.service = build("calendar", "v3", credentials=self.credentials)

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime | None = None,
        description: str | None = None,
        is_task: bool = False,
    ):
        """
        Create a new calendar event or task.

        Args:
            summary: Event title
            start_time: Start datetime
            end_time: End datetime (default: start_time + 1 hour)
            description: Event description
            is_task: Whether this is a task (vs event)

        Returns:
            Created event object
        """
        if end_time is None:
            # Tasks default to 30 mins, Events to 1 hour
            duration = timedelta(minutes=30) if is_task else timedelta(hours=1)
            end_time = start_time + duration

        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": settings.TIMEZONE,
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": settings.TIMEZONE,
            },
            "extendedProperties": {"private": {"type": "task" if is_task else "event"}},
        }

        # Set color for tasks (e.g., "11" is Tomato/Red, default is usually Blue)
        if is_task:
            event["colorId"] = "11"

        return self.service.events().insert(calendarId="primary", body=event).execute()

    def list_events(self, max_results: int = 20, event_type: str | None = None):
        """
        List upcoming events.

        Args:
            max_results: Maximum number of events to return
            event_type: Filter by type ('task' or 'event'), None for all

        Returns:
            List of events
        """
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        items = events_result.get("items", [])

        if event_type:
            filtered_items = []
            for item in items:
                props = item.get("extendedProperties", {}).get("private", {})
                item_type = props.get("type", "event")  # Default to event if no prop
                if item_type == event_type:
                    filtered_items.append(item)
            return filtered_items

        return items

    def get_event(self, event_id: str):
        """
        Get a specific event by ID.

        Args:
            event_id: Event ID

        Returns:
            Event object
        """
        return self.service.events().get(calendarId="primary", eventId=event_id).execute()

    def update_event(
        self,
        event_id: str,
        summary: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        description: str | None = None,
    ):
        """
        Update an existing calendar event.

        Args:
            event_id: Event ID to update
            summary: New event title (optional)
            start_time: New start datetime (optional)
            end_time: New end datetime (optional)
            description: New event description (optional)

        Returns:
            Updated event object
        """
        # Get existing event
        event = self.get_event(event_id)

        # Update fields if provided
        if summary is not None:
            event["summary"] = summary
        if description is not None:
            event["description"] = description
        if start_time is not None:
            event["start"] = {
                "dateTime": start_time.isoformat(),
                "timeZone": settings.TIMEZONE,
            }
        if end_time is not None:
            event["end"] = {
                "dateTime": end_time.isoformat(),
                "timeZone": settings.TIMEZONE,
            }

        return (
            self.service.events()
            .update(calendarId="primary", eventId=event_id, body=event)
            .execute()
        )

    def delete_event(self, event_id: str):
        """
        Delete a calendar event.

        Args:
            event_id: Event ID to delete

        Returns:
            None
        """
        self.service.events().delete(calendarId="primary", eventId=event_id).execute()
