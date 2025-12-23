"""
Vector Database Service using Qdrant for semantic search.
"""

import uuid
from typing import Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import settings


class VectorDBService:
    """Service for managing vector embeddings in Qdrant."""

    def __init__(self):
        """Initialize Qdrant client and embeddings."""
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.QDRANT_API_KEY if hasattr(settings, "QDRANT_API_KEY") else None,
        )

        # Use Gemini embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
        )

        # Collection names
        self.CHAT_COLLECTION = "chat_messages"
        self.KNOWLEDGE_COLLECTION = "knowledge_base"

        # Initialize collections
        self._init_collections()

    def _init_collections(self):
        """Initialize Qdrant collections if they don't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        # Chat messages collection
        if self.CHAT_COLLECTION not in collection_names:
            self.client.create_collection(
                collection_name=self.CHAT_COLLECTION,
                vectors_config=VectorParams(
                    size=768,  # Gemini embedding dimension
                    distance=Distance.COSINE,
                ),
            )
            print(f"Created collection: {self.CHAT_COLLECTION}")

        # Knowledge base collection
        if self.KNOWLEDGE_COLLECTION not in collection_names:
            self.client.create_collection(
                collection_name=self.KNOWLEDGE_COLLECTION,
                vectors_config=VectorParams(
                    size=768,
                    distance=Distance.COSINE,
                ),
            )
            print(f"Created collection: {self.KNOWLEDGE_COLLECTION}")

    async def add_chat_message(
        self,
        message_id: int,
        user_id: str,
        conversation_id: int,
        content: str,
        role: str,
        metadata: dict | None = None,
    ) -> str:
        """
        Add a chat message to vector DB.

        Args:
            message_id: Database message ID
            user_id: User ID
            conversation_id: Conversation ID
            content: Message content
            role: Message role (user/assistant)
            metadata: Additional metadata

        Returns:
            Vector ID (UUID)
        """
        # Generate embedding
        embedding = await self.embeddings.aembed_query(content)

        # Generate unique ID
        vector_id = str(uuid.uuid4())

        # Prepare payload
        payload = {
            "message_id": message_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "content": content,
            "role": role,
            **(metadata or {}),
        }

        # Insert into Qdrant
        self.client.upsert(
            collection_name=self.CHAT_COLLECTION,
            points=[
                PointStruct(
                    id=vector_id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )

        return vector_id

    async def search_chat_history(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        conversation_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search chat history using semantic search.

        Args:
            query: Search query
            user_id: User ID to filter by
            limit: Maximum number of results
            conversation_id: Optional conversation ID to filter by

        Returns:
            List of matching messages with scores
        """
        # Generate query embedding
        query_embedding = await self.embeddings.aembed_query(query)

        # Build filter
        must_conditions = [{"key": "user_id", "match": {"value": user_id}}]
        if conversation_id:
            must_conditions.append({"key": "conversation_id", "match": {"value": conversation_id}})

        # Search
        results = self.client.search(
            collection_name=self.CHAT_COLLECTION,
            query_vector=query_embedding,
            query_filter={"must": must_conditions},
            limit=limit,
        )

        # Format results
        return [
            {
                "id": result.id,
                "score": result.score,
                "content": result.payload.get("content"),
                "role": result.payload.get("role"),
                "message_id": result.payload.get("message_id"),
                "conversation_id": result.payload.get("conversation_id"),
            }
            for result in results
        ]

    async def add_knowledge(
        self,
        knowledge_id: int,
        title: str,
        content: str,
        user_id: str | None = None,
        category: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """
        Add a knowledge base document to vector DB.

        Args:
            knowledge_id: Database knowledge ID
            title: Document title
            content: Document content
            user_id: User ID (None for global knowledge)
            category: Document category
            metadata: Additional metadata

        Returns:
            Vector ID (UUID)
        """
        # Generate embedding from title + content
        text_to_embed = f"{title}\n\n{content}"
        embedding = await self.embeddings.aembed_query(text_to_embed)

        # Generate unique ID
        vector_id = str(uuid.uuid4())

        # Prepare payload
        payload = {
            "knowledge_id": knowledge_id,
            "title": title,
            "content": content,
            "user_id": user_id,
            "category": category,
            **(metadata or {}),
        }

        # Insert into Qdrant
        self.client.upsert(
            collection_name=self.KNOWLEDGE_COLLECTION,
            points=[
                PointStruct(
                    id=vector_id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )

        return vector_id

    async def search_knowledge(
        self,
        query: str,
        user_id: str | None = None,
        category: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search knowledge base using semantic search.

        Args:
            query: Search query
            user_id: User ID to filter by (None for global only)
            category: Category to filter by
            limit: Maximum number of results

        Returns:
            List of matching documents with scores
        """
        # Generate query embedding
        query_embedding = await self.embeddings.aembed_query(query)

        # Build filter
        must_conditions = []
        should_conditions = []

        if user_id:
            # Search both user's knowledge and global knowledge
            should_conditions.append({"key": "user_id", "match": {"value": user_id}})
            should_conditions.append({"key": "user_id", "match": {"value": None}})
        else:
            # Search only global knowledge
            must_conditions.append({"key": "user_id", "match": {"value": None}})

        if category:
            must_conditions.append({"key": "category", "match": {"value": category}})

        # Build query filter
        query_filter = {}
        if must_conditions:
            query_filter["must"] = must_conditions
        if should_conditions:
            query_filter["should"] = should_conditions

        # Search
        results = self.client.search(
            collection_name=self.KNOWLEDGE_COLLECTION,
            query_vector=query_embedding,
            query_filter=query_filter if query_filter else None,
            limit=limit,
        )

        # Format results
        return [
            {
                "id": result.id,
                "score": result.score,
                "title": result.payload.get("title"),
                "content": result.payload.get("content"),
                "knowledge_id": result.payload.get("knowledge_id"),
                "category": result.payload.get("category"),
            }
            for result in results
        ]

    def delete_vector(self, collection_name: str, vector_id: str):
        """Delete a vector from collection."""
        self.client.delete(
            collection_name=collection_name,
            points_selector=[vector_id],
        )

    async def get_relevant_context(
        self,
        query: str,
        user_id: str,
        max_chat_history: int = 3,
        max_knowledge: int = 2,
    ) -> dict[str, Any]:
        """
        Get relevant context for a query (chat history + knowledge base).

        Args:
            query: User query
            user_id: User ID
            max_chat_history: Max chat history items
            max_knowledge: Max knowledge base items

        Returns:
            Dict with chat_history and knowledge
        """
        # Search chat history
        chat_results = await self.search_chat_history(
            query=query,
            user_id=user_id,
            limit=max_chat_history,
        )

        # Search knowledge base
        knowledge_results = await self.search_knowledge(
            query=query,
            user_id=user_id,
            limit=max_knowledge,
        )

        return {
            "chat_history": chat_results,
            "knowledge": knowledge_results,
        }
