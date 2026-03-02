"""Chat API endpoints for interacting with the AI bot."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, Conversation
from app.services.ai_service import AIService
from app.services.k8s_service import K8sService

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    """Chat response model."""

    session_id: str
    message: str
    actions_taken: List[dict] = []
    suggestions: List[str] = []


class ConversationHistory(BaseModel):
    """Conversation history model."""

    session_id: str
    messages: List[ChatMessage]


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message to the AI bot and get a response."""
    session_id = request.session_id or str(uuid.uuid4())

    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(Conversation.created_at)
    )
    history = result.scalars().all()

    messages = [{"role": msg.role, "content": msg.content} for msg in history]

    user_msg = Conversation(
        session_id=session_id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)

    ai_service = AIService()
    k8s_service = K8sService()

    response = await ai_service.process_message(
        message=request.message,
        history=messages,
        k8s_service=k8s_service,
    )

    assistant_msg = Conversation(
        session_id=session_id,
        role="assistant",
        content=response["message"],
    )
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(
        session_id=session_id,
        message=response["message"],
        actions_taken=response.get("actions_taken", []),
        suggestions=response.get("suggestions", []),
    )


@router.get("/history/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get conversation history for a session."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(Conversation.created_at)
    )
    messages = result.scalars().all()

    if not messages:
        raise HTTPException(status_code=404, detail="Session not found")

    return ConversationHistory(
        session_id=session_id,
        messages=[
            ChatMessage(role=msg.role, content=msg.content) for msg in messages
        ],
    )


@router.delete("/history/{session_id}")
async def clear_conversation_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Clear conversation history for a session."""
    result = await db.execute(
        select(Conversation).where(Conversation.session_id == session_id)
    )
    messages = result.scalars().all()

    for msg in messages:
        await db.delete(msg)

    await db.commit()

    return {"status": "success", "message": "Conversation history cleared"}


@router.post("/new-session")
async def create_new_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}
