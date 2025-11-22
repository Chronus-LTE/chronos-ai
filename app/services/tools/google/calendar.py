"""
Google Calendar tools for the AI Agent.
"""

from datetime import datetime

from langchain.tools import Tool

from app.services.google.calendar_service import GoogleCalendarService
from app.services.tools.base import BaseToolSet


class GoogleCalendarToolSet(BaseToolSet):
    """Tool set for Google Calendar operations."""

    def __init__(self, user_token: str):
        super().__init__(user_token)
        self.calendar_service = GoogleCalendarService(token=user_token)

    def get_tools(self) -> list[Tool]:
        """Get Google Calendar tools."""
        return [
            Tool(
                name="create_calendar_event",
                func=self._create_calendar_event,
                description="Use this to create a new calendar event. Input should be 'Title | Start Time (ISO) | End Time (ISO)'",
            ),
            Tool(
                name="list_calendar_events",
                func=self._list_calendar_events,
                description="Use this to see upcoming events. Input can be empty string.",
            ),
        ]

    def _create_calendar_event(self, input_str: str) -> str:
        """
        Create a calendar event.
        Input format: "Title | Start Time (ISO format) | End Time (ISO format, optional)"
        Example: "Meeting | 2024-11-22T14:00:00 | 2024-11-22T15:00:00"
        """
        try:
            parts = [p.strip() for p in input_str.split("|")]

            # Validate that we have at least title and start time
            validation_errors = []
            if len(parts) < 2:
                validation_errors.append(
                    "Missing required information. Please provide: Title | Start Time (ISO format) | Optional End Time"
                )

            if not validation_errors:
                title = parts[0]
                if not title:
                    validation_errors.append(
                        "Event title cannot be empty. Please provide a title for the event."
                    )

            if not validation_errors:
                start_time_str = parts[1]
                if not start_time_str:
                    validation_errors.append(
                        "Start time cannot be empty. Please provide a start time in ISO format (e.g., 2024-11-23T14:00:00)."
                    )

            if validation_errors:
                return f"ERROR: {validation_errors[0]}"

            # Parse times
            try:
                start_time = datetime.fromisoformat(start_time_str)
            except ValueError:
                return f"ERROR: Invalid start time format '{start_time_str}'. Please use ISO format (e.g., 2024-11-23T14:00:00)."

            end_time = None
            if len(parts) > 2 and parts[2]:
                try:
                    end_time = datetime.fromisoformat(parts[2])
                except ValueError:
                    return f"ERROR: Invalid end time format '{parts[2]}'. Please use ISO format (e.g., 2024-11-23T15:00:00)."

            # Create the event
            event = self.calendar_service.create_event(title, start_time, end_time)
            return f"Event created successfully: {event.get('htmlLink', 'Event saved to calendar')}"
        except Exception as e:
            return f"Error creating event: {e!s}"

    def _list_calendar_events(self, input_str: str) -> str:
        """List upcoming calendar events."""
        try:
            events = self.calendar_service.list_events()
            if not events:
                return "No upcoming events found."

            result = "Upcoming events:\n"
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                result += f"- {event['summary']} at {start}\n"
            return result
        except Exception as e:
            return f"Error listing events: {e!s}"
