from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.ai.agent_service import AIAgentService

router = APIRouter(prefix="/chat", tags=["Chat"])

# Store agent instances per user to maintain conversation history
_agent_instances: dict[int, AIAgentService] = {}


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


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
        # Note: In a real app, you should handle token refresh if it's expired
        if not current_user.google_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google Calendar access not found. Please login with Google again.",
            )

        # Get or create agent instance for this user
        user_id = current_user.id
        if user_id not in _agent_instances:
            _agent_instances[user_id] = AIAgentService(user_token=current_user.google_access_token)

        agent = _agent_instances[user_id]
        response = await agent.process_message(request.message)

        return ChatResponse(response=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
