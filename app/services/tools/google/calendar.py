"""
Google Calendar tools for the AI Agent.
"""

import traceback
from datetime import datetime, timedelta, timezone

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
                description="Use this to create a new calendar event. Input should be 'Title | Start Timestamp (Unix Integer) | End Timestamp (Unix Integer, optional)'",
            ),
            Tool(
                name="create_task",
                func=self._create_task,
                description="Use this to create a new task (stored as a special calendar event). Input should be 'Title | Due Timestamp (Unix Integer) | Notes (optional)'",
            ),
            Tool(
                name="list_calendar_events",
                func=self._list_calendar_events,
                description="Use this to see upcoming standard events. Input can be empty string.",
            ),
            Tool(
                name="list_tasks",
                func=self._list_tasks,
                description="Use this to see upcoming tasks. Input can be empty string.",
            ),
            Tool(
                name="get_event_by_id",
                func=self._get_event_by_id,
                description="Get details of a specific event or task by its ID. Input should be the ID.",
            ),
        ]

    def _create_calendar_event(self, input_str: str | list) -> str:
        """Create a standard calendar event."""
        return self._create_item(input_str, is_task=False)

    def _create_task(self, input_str: str | list) -> str:
        """Create a task (special calendar event)."""
        return self._create_item(input_str, is_task=True)

    def _create_item(self, input_str: str | list, is_task: bool) -> str:
        """Helper to create event or task."""
        try:
            # Handle both string and list inputs from LangChain
            if isinstance(input_str, list):
                input_str = " | ".join(str(item) for item in input_str)

            parts = [p.strip() for p in input_str.split("|")]

            if len(parts) < 2:
                return "ERROR: Missing required information. Please provide: Title | Timestamp"

            title = parts[0]
            if not title:
                return "ERROR: Title cannot be empty."

            start_time_str = parts[1]
            try:
                start_ts = int(float(start_time_str))
                start_time = datetime.fromtimestamp(start_ts, tz=timezone.utc)
            except ValueError:
                return f"ERROR: Invalid timestamp '{start_time_str}'. Please use Unix timestamp integer."

            end_time = None
            description = None

            if is_task:
                # For tasks: Title | Due Time | Notes
                if len(parts) > 2:
                    description = parts[2]
            elif len(parts) > 2 and parts[2]:
                # For events: Title | Start Time | End Time
                try:
                    end_ts = int(float(parts[2]))
                    end_time = datetime.fromtimestamp(end_ts, tz=timezone.utc)
                except ValueError:
                    pass  # Ignore invalid end time

            # Create the item
            item = self.calendar_service.create_event(
                summary=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                is_task=is_task,
            )

            type_str = "Task" if is_task else "Event"
            return (
                f"✅ {type_str} created successfully: {item.get('htmlLink', 'Saved to calendar')}"
            )
        except Exception as e:
            traceback.print_exc()
            return f"Error creating {type_str}: {e!s}"

    def _list_calendar_events(self, input_str: str | list) -> str:
        """List standard calendar events."""
        return self._list_items(event_type="event")

    def _list_tasks(self, input_str: str | list) -> str:
        """List tasks."""
        return self._list_items(event_type="task")

    def _list_items(self, event_type: str) -> str:
        """Helper to list items by type."""
        try:
            items = self.calendar_service.list_events(event_type=event_type)
            if not items:
                return f"No upcoming {event_type}s found."

            icon = "📝" if event_type == "task" else "📅"
            title = "Tasks" if event_type == "task" else "Events"

            result = f"{icon} Upcoming {title}:\n"
            for item in items:
                start_str = item["start"].get("dateTime", item["start"].get("date"))

                # Format time nicely
                try:
                    dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    # Convert to UTC+7 for display
                    tz = timezone(timedelta(hours=7))
                    dt_local = dt.astimezone(tz)
                    time_str = dt_local.strftime("%H:%M %d/%m/%Y")
                except Exception:
                    time_str = start_str

                result += f"- {item['summary']} at {time_str} [ID: {item['id']}]"

                if item.get("description"):
                    result += f"\n  Note: {item['description']}"

                result += "\n"

            return result
        except Exception as e:
            traceback.print_exc()
            return f"Error listing {event_type}s: {e!s}"

    def _get_event_by_id(self, event_id: str | list) -> str:
        """Get details of a specific event."""
        try:
            if isinstance(event_id, list):
                event_id = str(event_id[0])

            event = self.calendar_service.get_event(event_id)

            props = event.get("extendedProperties", {}).get("private", {})
            item_type = props.get("type", "event")

            start_str = event["start"].get("dateTime", event["start"].get("date"))

            result = f"{item_type.title()}: {event['summary']}\n"
            result += f"Time: {start_str}\n"

            if event.get("description"):
                result += f"Description: {event['description']}\n"

            return result
        except Exception as e:
            return f"Error getting item: {e!s}"
