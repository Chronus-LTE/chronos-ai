from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.database import get_db
from app.models.conversation import Conversation
from app.models.user import User
from app.services.ai.agent_service import AIAgentService
from app.services.chat_history import ChatHistoryService

router = APIRouter(prefix="/chat", tags=["Chat"])

# Store agent instances per user to maintain conversation history
_agent_instances: dict[int, AIAgentService] = {}


async def _verify_conversation_access(
    db: AsyncSession,
    conversation_id: str,
    user_id: int,
) -> None:
    """Verify conversation exists and belongs to user."""
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if conversation.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this conversation",
        )


async def _load_rag_context(
    chat_service: ChatHistoryService,
    conversation_id: str,
    message: str,
    user_id: int,
) -> tuple[list, str, list]:
    """Load RAG-based context for conversation."""
    # 1. Get recent messages for immediate context (last 3 exchanges = 6 messages)
    recent_messages = await chat_service.get_conversation_history(
        conversation_id=conversation_id, limit=6
    )

    # 2. Use VectorDB to find semantically relevant messages from current conversation
    relevant_current = await chat_service.get_relevant_context(
        query=message,
        current_conversation_id=conversation_id,
        max_messages=5,  # Top 5 relevant messages from this conversation
    )

    # 3. Use VectorDB to find relevant messages from OTHER conversations
    vector_db_service = chat_service.vector_db
    relevant_other = await vector_db_service.search_chat_history(
        query=message,
        user_id=str(user_id),
        limit=3,  # Top 3 relevant from other conversations
    )
    # Filter out messages from current conversation
    relevant_other = [
        msg for msg in relevant_other if msg.get("conversation_id") != conversation_id
    ]

    return recent_messages, relevant_current, relevant_other


def _prepare_agent_context(
    agent: AIAgentService,
    recent_messages: list,
    relevant_current: str,
    relevant_other: list,
) -> None:
    """Prepare agent with conversation context."""
    # Build agent's conversation history with smart context
    agent.conversation_history = []

    # Add recent messages first (chronological order for immediate context)
    for msg in recent_messages:
        if msg.role == "user":
            agent.conversation_history.append(("User", msg.content))
        elif msg.role == "assistant":
            agent.conversation_history.append(("Assistant", msg.content))

    # Store RAG context separately to be injected into prompt
    agent.rag_context = {
        "current_conversation": relevant_current,
        "related_conversations": relevant_other,
    }


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str | None = None
    context: dict | None = None


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Chat with AI Agent.
    """
    try:
        # Get user's Google Access Token from DB
        if not current_user.google_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google Calendar access not found. Please login with Google again.",
            )

        # Initialize services
        chat_service = ChatHistoryService(db, current_user.id)

        # Get or create conversation
        if request.conversation_id:
            await _verify_conversation_access(db, request.conversation_id, current_user.id)
            conversation_id = request.conversation_id
        else:
            conversation = await chat_service.create_conversation()
            conversation_id = conversation.id

        # Get relevant context from Vector DB
        context = ""
        if request.conversation_id:
            context = await chat_service.get_relevant_context(
                query=request.message, current_conversation_id=conversation_id
            )

        # Get or create agent instance for this user
        user_id = current_user.id
        if user_id not in _agent_instances:
            _agent_instances[user_id] = AIAgentService(user_token=current_user.google_access_token)

        agent = _agent_instances[user_id]

        # RAG-based context retrieval for better token efficiency
        if request.conversation_id:
            recent_messages, relevant_current, relevant_other = await _load_rag_context(
                chat_service, conversation_id, request.message, user_id
            )
            _prepare_agent_context(agent, recent_messages, relevant_current, relevant_other)
        else:
            # New conversation - clear history and RAG context
            agent.conversation_history = []
            agent.rag_context = None

        # Process message with RAG-enhanced context
        response_text = await agent.process_message(request.message)

        # Save messages to DB and Vector DB
        await chat_service.add_message(
            conversation_id=conversation_id, role="user", content=request.message
        )

        await chat_service.add_message(
            conversation_id=conversation_id, role="assistant", content=response_text
        )

        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            context={"relevant_text": context} if context else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/conversations")
async def list_conversations(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent conversations."""
    chat_service = ChatHistoryService(db, current_user.id)
    return await chat_service.get_recent_conversations(limit=limit)


@router.get("/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages for a specific conversation."""
    # Verify conversation belongs to current user
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this conversation",
        )

    chat_service = ChatHistoryService(db, current_user.id)
    return await chat_service.get_conversation_history(conversation_id, limit=limit)


@router.get("/search")
async def search_conversations(
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search conversations using Vector DB (only user's own conversations)."""
    chat_service = ChatHistoryService(db, current_user.id)
    results = await chat_service.search_conversations(query, limit=limit)

    # Verify all results belong to current user (defense in depth)
    for result in results:
        if result.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to conversation",
            )

    return results


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    try:
        # Verify conversation belongs to current user
        await _verify_conversation_access(db, conversation_id, current_user.id)

        # Delete conversation and all messages
        chat_service = ChatHistoryService(db, current_user.id)
        await chat_service.delete_conversation(conversation_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {e!s}",
        ) from e
