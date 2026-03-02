"""API routes package."""

from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.kubernetes import router as k8s_router
from app.api.analytics import router as analytics_router

router = APIRouter()

router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(k8s_router, prefix="/k8s", tags=["Kubernetes"])
router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
