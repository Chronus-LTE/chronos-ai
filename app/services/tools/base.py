"""
Base class for AI Agent tools.
"""

from abc import ABC, abstractmethod

from langchain.tools import Tool


class BaseToolSet(ABC):
    """Abstract base class for tool sets."""

    def __init__(self, user_token: str | None = None):
        """
        Initialize the tool set.

        Args:
            user_token: User's access token for the service (if required)
        """
        self.user_token = user_token

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """
        Get the list of LangChain tools provided by this set.

        Returns:
            List of Tool objects
        """
