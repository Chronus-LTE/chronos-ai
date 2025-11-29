"""
Chat History Service with Vector DB integration.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.services.vector_db import VectorDBService


class ChatHistoryService:
    """Service for managing chat history with vector DB."""

    def __init__(self, db: AsyncSession, user_id: int):
        """
        Initialize chat history service.

        Args:
            db: Database session
            user_id: User ID
        """
        self.db = db
        self.user_id = user_id
        self.vector_db = VectorDBService()

    async def create_conversation(
        self,
        title: str | None = None,
        session_id: str | None = None,
        metadata: dict | None = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            title: Conversation title
            session_id: Session ID for grouping
            metadata: Additional metadata

        Returns:
            Created conversation
        """
        conversation = Conversation(
            user_id=self.user_id,
            title=title,
            session_id=session_id,
            meta_data=metadata,
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
        save_to_vector: bool = True,
    ) -> Message:
        """
        Add a message to conversation.

        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Additional metadata
            save_to_vector: Whether to save to vector DB

        Returns:
            Created message
        """
        # Create message in DB
        message = Message(
            conversation_id=conversation_id,
            user_id=self.user_id,
            role=role,
            content=content,
            meta_data=metadata,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        # Save to vector DB for semantic search
        if save_to_vector and content.strip():
            try:
                vector_id = await self.vector_db.add_chat_message(
                    message_id=message.id,
                    user_id=self.user_id,
                    conversation_id=conversation_id,
                    content=content,
                    role=role,
                    metadata=metadata,
                )
                message.vector_id = vector_id
                await self.db.commit()
            except Exception as e:
                print(f"Failed to save message to vector DB: {e}")

        # Update conversation timestamp
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.updated_at = datetime.utcnow()

            # Auto-generate title from first user message
            if not conversation.title and role == "user":
                conversation.title = content[:100] + ("..." if len(content) > 100 else "")

            await self.db.commit()

        return message

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> list[Message]:
        """
        Get conversation history.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages

        Returns:
            List of messages
        """
        result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.user_id == self.user_id,
            )
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def search_conversations(
        self,
        query: str,
        limit: int = 10,
    ) -> list[Conversation]:
        """
        Search conversations by title or content.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of conversations
        """
        # Use vector DB for semantic search
        try:
            search_results = await self.vector_db.search_chat_history(
                query=query,
                user_id=self.user_id,
                limit=limit,
            )

            # Get unique conversation IDs
            conversation_ids = list({r["conversation_id"] for r in search_results})

            # Fetch conversations
            result = await self.db.execute(
                select(Conversation)
                .where(Conversation.id.in_(conversation_ids))
                .order_by(Conversation.updated_at.desc())
            )
            return result.scalars().all()

        except Exception as e:
            print(f"Vector search failed, falling back to DB search: {e}")

            # Fallback to simple DB search
            result = await self.db.execute(
                select(Conversation)
                .where(
                    Conversation.user_id == self.user_id,
                    Conversation.title.ilike(f"%{query}%"),
                )
                .order_by(Conversation.updated_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    async def get_recent_conversations(self, limit: int = 20) -> list[Conversation]:
        """
        Get recent conversations.

        Args:
            limit: Maximum number of conversations

        Returns:
            List of conversations
        """
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == self.user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def delete_conversation(self, conversation_id: str):
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: Conversation ID
        """
        # Delete messages from vector DB
        result = await self.db.execute(
            select(Message).where(
                Message.conversation_id == conversation_id,
                Message.user_id == self.user_id,
            )
        )
        messages = result.scalars().all()

        for message in messages:
            if message.vector_id:
                try:
                    self.vector_db.delete_vector(
                        collection_name=self.vector_db.CHAT_COLLECTION,
                        vector_id=message.vector_id,
                    )
                except Exception as e:
                    print(f"Failed to delete vector {message.vector_id}: {e}")

            await self.db.delete(message)

        # Delete conversation
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == self.user_id,
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            await self.db.delete(conversation)

        await self.db.commit()

    async def get_relevant_context(
        self,
        query: str,
        current_conversation_id: str | None = None,
        max_messages: int = 5,
    ) -> str:
        """
        Get relevant context from chat history for current query.

        Args:
            query: Current user query
            current_conversation_id: Current conversation ID
            max_messages: Maximum messages to retrieve

        Returns:
            Formatted context string
        """
        try:
            # Search relevant messages
            results = await self.vector_db.search_chat_history(
                query=query,
                user_id=self.user_id,
                limit=max_messages,
                conversation_id=current_conversation_id,
            )

            if not results:
                return ""

            # Format context
            context_parts = ["## Relevant Context from Previous Conversations:\n"]
            for result in results:
                role = result["role"].capitalize()
                content = result["content"]
                context_parts.append(f"**{role}**: {content}\n")

            return "\n".join(context_parts)

        except Exception as e:
            print(f"Failed to get relevant context: {e}")
            return ""
