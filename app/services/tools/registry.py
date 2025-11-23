"""
Registry for AI Agent tools.
"""

from typing import ClassVar

from app.services.tools.base import BaseToolSet
from app.services.tools.google.calendar import GoogleCalendarToolSet


class ToolRegistry:
    """Registry to manage available tool sets."""

    _tools: ClassVar[dict[str, type[BaseToolSet]]] = {
        "google_calendar": GoogleCalendarToolSet,
    }

    @classmethod
    def get_tool_class(cls, tool_name: str) -> type[BaseToolSet] | None:
        """Get a tool class by name."""
        return cls._tools.get(tool_name)

    @classmethod
    def get_all_tool_classes(cls) -> dict[str, type[BaseToolSet]]:
        """Get all registered tool classes."""
        return cls._tools
