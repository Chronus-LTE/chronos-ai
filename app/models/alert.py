"""
Alert model for proactive suggestions.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Alert(Base):
    """Model for storing proactive suggestions and alerts."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)

    # Alert metadata
    type = Column(String(50), nullable=False)  # scheduling, overload, task_reminder, email_followup
    priority = Column(String(20), nullable=False)  # high, medium, low
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Context data (JSON string)
    context = Column(Text, nullable=True)  # Store related IDs, dates, etc.

    # Status
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    is_actioned = Column(Boolean, default=False)  # User took action on this alert

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)
    actioned_at = Column(DateTime, nullable=True)

    # Expiry (optional - alerts can expire after certain time)
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self):
        """String representation."""
        return f"<Alert {self.id}: {self.type} - {self.priority}>"
