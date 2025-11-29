from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.ai.agent_service import AIAgentService
from app.services.chat_history import ChatHistoryService

router = APIRouter(prefix="/chat", tags=["Chat"])

# Store agent instances per user to maintain conversation history
_agent_instances: dict[int, AIAgentService] = {}


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
            # Verify conversation exists and belongs to user
            history = await chat_service.get_conversation_history(request.conversation_id, limit=1)
            if not history:
                # If not found, treat as new conversation or raise error?
                # For now, let's create a new one if ID is invalid isn't ideal, but let's assume valid ID
                pass
            conversation_id = request.conversation_id
        else:
            conversation = await chat_service.create_conversation()
            conversation_id = conversation.id

        # Get relevant context from Vector DB
        context = await chat_service.get_relevant_context(
            query=request.message, current_conversation_id=conversation_id
        )

        # Get or create agent instance for this user
        user_id = current_user.id
        if user_id not in _agent_instances:
            _agent_instances[user_id] = AIAgentService(user_token=current_user.google_access_token)

        agent = _agent_instances[user_id]

        # Process message with context
        # Note: We might want to pass context to the agent in the future
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
    chat_service = ChatHistoryService(db, current_user.id)
    return await chat_service.get_conversation_history(conversation_id, limit=limit)


@router.get("/search")
async def search_conversations(
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search conversations using Vector DB."""
    chat_service = ChatHistoryService(db, current_user.id)
    return await chat_service.search_conversations(query, limit=limit)
