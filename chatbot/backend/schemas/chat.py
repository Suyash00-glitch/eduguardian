"""
Chat Message & Conversation Contracts.

Defines the shared models for messages, conversation threads,
and API chat request/response schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from chatbot.backend.schemas.planner import StudyPlan, StudyTask

# Aliases for backwards compatibility with earlier endpoint prototypes
StudyPlanSchema = StudyPlan
StudyTaskSchema = StudyTask


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"  # internal only, never exposed to frontend


class ChatMessage(BaseModel):
    """An individual message turn within a conversation."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    role: MessageRole
    content: str = Field(description="Textual content of the message")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    structured_data: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured payloads attached to this message (e.g. StudyPlan)",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationHistory(BaseModel):
    """Full thread of messages in a chat session."""
    conversation_id: uuid.UUID
    student_id: str
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Payload sent by the student/frontend to POST /chat."""
    message: str = Field(min_length=1, max_length=4000, description="User's input text")
    conversation_id: uuid.UUID | None = Field(
        default=None,
        description="Optional UUID of ongoing conversation. If omitted, a new conversation is started.",
    )
    user_id: str | None = Field(
        default=None,
        description="Optional explicit student identity override for testing/multi-tenant scenarios.",
    )
    student_id: str | None = Field(
        default=None,
        description="Optional alias for user_id.",
    )


class MessageSchema(BaseModel):
    """Student-facing message schema in API responses."""
    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    """Complete API response returned to the frontend."""
    conversation_id: uuid.UUID
    message: MessageSchema
    study_plan: StudyPlan | None = None
    teaching_state: dict[str, Any] | None = None
    quiz_state: dict[str, Any] | None = None
    agents_used: list[str] = Field(default_factory=list)


class ConversationHistoryResponse(BaseModel):
    """Response returned by GET /chat/{id}/history."""
    conversation_id: uuid.UUID
    messages: list[MessageSchema]
    created_at: datetime
