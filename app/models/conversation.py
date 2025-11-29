"""
Chat conversation models for storing chat history.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base
from app.utils.id_utils import generate_short_id


class Conversation(Base):
    """Model for storing chat conversations."""

    __tablename__ = "conversations"

    id = Column(String(50), primary_key=True, index=True, default=generate_short_id)
    user_id = Column(String(50), index=True, nullable=False)

    # Conversation metadata
    title = Column(String(255), nullable=True)  # Auto-generated from first message
    session_id = Column(String(100), index=True, nullable=True)  # For grouping related chats

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata (JSON)
    meta_data = Column(JSONB, nullable=True)  # Store context, tags, etc.

    def __repr__(self):
        """String representation."""
        return f"<Conversation {self.id}: {self.title}>"


class Message(Base):
    """Model for storing individual chat messages."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(50), index=True, nullable=False)
    user_id = Column(String(50), index=True, nullable=False)

    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Vector embedding ID (reference to Qdrant)
    vector_id = Column(String(100), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Metadata (JSON) - store tool calls, function results, etc.
    meta_data = Column(JSONB, nullable=True)

    def __repr__(self):
        """String representation."""
        return f"<Message {self.id}: {self.role}>"


class KnowledgeBase(Base):
    """Model for storing knowledge base documents."""

    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), index=True, nullable=True)  # None = global knowledge

    # Document metadata
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)  # URL, file path, etc.
    category = Column(String(100), nullable=True, index=True)

    # Vector embedding ID (reference to Qdrant)
    vector_id = Column(String(100), nullable=True, index=True)

    # Status
    is_active = Column(Integer, default=1)  # 1 = active, 0 = archived

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata (JSON)
    meta_data = Column(JSONB, nullable=True)

    def __repr__(self):
        """String representation."""
        return f"<KnowledgeBase {self.id}: {self.title}>"
