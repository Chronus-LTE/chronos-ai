from fastapi import APIRouter

from app.api.v1.alerts import router as alerts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.chat import router as chat_router
from app.api.v1.gmail import router as gmail_router
from app.api.v1.knowledge import router as knowledge_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(calendar_router)
api_router.include_router(chat_router)
api_router.include_router(gmail_router)
api_router.include_router(alerts_router)
api_router.include_router(knowledge_router)
