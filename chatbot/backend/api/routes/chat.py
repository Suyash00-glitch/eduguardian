"""
Chat routes — the core API endpoints for the student chatbot.

Endpoints:
  POST   /chat                              — Send a message, receive a response & optional study plan
  GET    /chat/{conversation_id}/messages   — Retrieve chronological conversation messages
  GET    /chat/{conversation_id}/history    — Backward compatible alias for /messages
  GET    /chat/conversations                — List conversations for the current student
  PATCH  /chat/{conversation_id}/title      — Rename a conversation
  DELETE /chat/{conversation_id}            — Delete a conversation thread
"""
from __future__ import annotations

import logging
import uuid
from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from chatbot.backend.api.dependencies import (
    get_chat_service,
    get_current_student_id,
)
from chatbot.backend.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    MessageRole,
    MessageSchema,
)
from chatbot.backend.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class RenameRequest(BaseModel):
    """Request body for renaming a conversation."""
    title: str = Field(..., min_length=1, max_length=80, description="New conversation title")


def _resolve_student_id(
    jwt_student_id: str | None,
    body_user_id: str | None,
    header_student_id: str | None,
) -> str:
    """Resolves authoritative student identity for the turn."""
    sid = jwt_student_id or header_student_id or body_user_id or ""
    clean = sid.strip()
    if not clean:
        return "student_001"
    return clean


# ── POST /chat ─────────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def send_message(
    request: ChatRequest,
    jwt_student_id: str | None = Depends(get_current_student_id),
    x_student_id: str | None = Header(None, alias="X-Student-ID"),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """
    Main chat turn endpoint.
    """
    effective_student_id = _resolve_student_id(jwt_student_id, request.user_id or request.student_id, x_student_id)
    return await chat_service.send_message(student_id=effective_student_id, request=request)


# ── POST /chat/stream ──────────────────────────────────────────────────────────

@router.post("/stream", status_code=status.HTTP_200_OK)
async def send_message_stream(
    request: ChatRequest,
    jwt_student_id: str | None = Depends(get_current_student_id),
    x_student_id: str | None = Header(None, alias="X-Student-ID"),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Progressive SSE streaming turn endpoint.
    """
    effective_student_id = _resolve_student_id(jwt_student_id, request.user_id or request.student_id, x_student_id)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        chat_service.send_message_stream(student_id=effective_student_id, request=request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── GET /chat/{conversation_id}/messages ───────────────────────────────────────

@router.get(
    "/{conversation_id}/messages",
    response_model=ConversationHistoryResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/{conversation_id}/history",
    response_model=ConversationHistoryResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_messages(
    conversation_id: uuid.UUID,
    jwt_student_id: str | None = Depends(get_current_student_id),
    x_student_id: str | None = Header(None, alias="X-Student-ID"),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationHistoryResponse:
    """
    Retrieves the chronological message history for a specific conversation thread.
    Enforces student-level ownership verification.
    """
    effective_student_id = _resolve_student_id(jwt_student_id, None, x_student_id)
    return await chat_service.get_history(student_id=effective_student_id, conversation_id=conversation_id)


# ── GET /chat/conversations ───────────────────────────────────────────────────

@router.get(
    "/conversations",
    status_code=status.HTTP_200_OK,
)
async def list_conversations(
    jwt_student_id: str | None = Depends(get_current_student_id),
    x_student_id: str | None = Header(None, alias="X-Student-ID"),
    chat_service: ChatService = Depends(get_chat_service),
) -> list[dict[str, Any]]:
    """
    Lists all conversation threads belonging to the authenticated student.
    """
    effective_student_id = _resolve_student_id(jwt_student_id, None, x_student_id)
    return await chat_service.list_conversations(student_id=effective_student_id)


# ── DELETE /chat/{conversation_id} ─────────────────────────────────────────────

@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    jwt_student_id: str | None = Depends(get_current_student_id),
    x_student_id: str | None = Header(None, alias="X-Student-ID"),
    chat_service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    """
    Deletes a conversation thread and its associated message history.
    """
    effective_student_id = _resolve_student_id(jwt_student_id, None, x_student_id)
    return await chat_service.delete_conversation(student_id=effective_student_id, conversation_id=conversation_id)


# ── PATCH /chat/{conversation_id}/title ────────────────────────────────────────

@router.patch(
    "/{conversation_id}/title",
    status_code=status.HTTP_200_OK,
)
async def rename_conversation(
    conversation_id: uuid.UUID,
    body: RenameRequest,
    student_id: str = Depends(get_current_student_id),
    chat_service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    """
    Renames a conversation thread title.
    Enforces student ownership. Title is trimmed and capped at 80 characters.
    """
    return await chat_service.rename_conversation(
        student_id=student_id,
        conversation_id=conversation_id,
        new_title=body.title,
    )
