"""
Google Calendar tools for the AI Agent.
"""

import traceback
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
                description="Use this to see upcoming events with their start time, end time, and duration. Input can be empty string.",
            ),
            Tool(
                name="get_event_by_id",
                func=self._get_event_by_id,
                description="Get details of a specific event by its ID. Input should be the event ID.",
            ),
        ]

    def _create_calendar_event(self, input_str: str | list) -> str:
        """
        Create a calendar event.
        Input format: "Title | Start Time (ISO format) | End Time (ISO format, optional)"
        Example: "Meeting | 2024-11-22T14:00:00 | 2024-11-22T15:00:00"
        """
        try:
            # Handle both string and list inputs from LangChain
            if isinstance(input_str, list):
                input_str = " | ".join(str(item) for item in input_str)

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
            traceback.print_exc()
            return f"Error creating event: {e!s}"

    def _list_calendar_events(self, input_str: str | list) -> str:
        """List upcoming calendar events with duration information."""
        try:
            events = self.calendar_service.list_events()
            if not events:
                return "No upcoming events found."

            result = "Upcoming events:\n"
            for event in events:
                start_str = event["start"].get("dateTime", event["start"].get("date"))
                end_str = event["end"].get("dateTime", event["end"].get("date"))

                # Calculate duration if both start and end are datetime
                duration_info = ""
                if "dateTime" in event["start"] and "dateTime" in event["end"]:
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    duration = end_dt - start_dt
                    hours = duration.total_seconds() / 3600
                    duration_info = f" (Duration: {hours:.1f} hours, ends at {end_str})"

                result += (
                    f"- {event['summary']} at {start_str}{duration_info} [ID: {event['id']}]\n"
                )
            return result
        except Exception as e:
            traceback.print_exc()
            return f"Error listing events: {e!s}"

    def _get_event_by_id(self, event_id: str | list) -> str:
        """Get details of a specific event."""
        try:
            if isinstance(event_id, list):
                event_id = str(event_id[0])

            event = self.calendar_service.get_event(event_id)
            start_str = event["start"].get("dateTime", event["start"].get("date"))
            end_str = event["end"].get("dateTime", event["end"].get("date"))

            result = f"Event: {event['summary']}\n"
            result += f"Start: {start_str}\n"
            result += f"End: {end_str}\n"

            if "dateTime" in event["start"] and "dateTime" in event["end"]:
                start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                duration = end_dt - start_dt
                hours = duration.total_seconds() / 3600
                result += f"Duration: {hours:.1f} hours\n"

            if event.get("description"):
                result += f"Description: {event['description']}\n"

            return result
        except Exception as e:
            return f"Error getting event: {e!s}"
