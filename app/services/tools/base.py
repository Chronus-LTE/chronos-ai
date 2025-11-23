"""
Base class for AI Agent tools.
"""

from abc import ABC, abstractmethod

from langchain.tools import Tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class BaseToolSet(ABC):
    """Abstract base class for tool sets."""

    def __init__(
        self,
        user_token: str | None = None,
        user: User | None = None,
        db: AsyncSession | None = None,
    ):
        """
        Initialize the tool set.

        Args:
            user_token: User's access token for the service (if required)
            user: User object (for database operations)
            db: Database session (for metadata storage)
        """
        self.user_token = user_token
        self.user = user
        self.db = db

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """
        Get the list of LangChain tools provided by this set.

        Returns:
            List of Tool objects
        """
