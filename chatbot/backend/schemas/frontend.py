"""
Frontend Client Contracts.

Defines the clean, friendly response models delivered to the chatbot UI.

The frontend receives ONLY student-supportive content:
- Message content
- Renderable Study Plan cards/tasks/milestones
- Suggested quick prompt chips
- Actionable study resources

NO internal model scores, risk tiers, or orchestration details are exposed here.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from chatbot.backend.schemas.planner import StudyPlan, PriorityLevel


class FrontendMessage(BaseModel):
    """User or Assistant message displayed in the UI."""
    id: uuid.UUID
    role: str = Field(description="'user' | 'assistant'")
    content: str
    created_at: datetime


class FrontendChatResponse(BaseModel):
    """Primary payload consumed by the React/Vite frontend hook."""
    conversation_id: uuid.UUID
    message: FrontendMessage
    study_plan: StudyPlan | None = None
    suggested_prompts: list[str] = Field(
        default_factory=list,
        description="Chips displayed above input bar (e.g. '📋 Make me a study plan')",
    )
