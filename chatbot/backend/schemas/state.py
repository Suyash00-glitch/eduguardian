"""
Chat State Contract.

Defines the state structure used by the LangGraph orchestrator to coordinate
information across execution turns and agent nodes.
"""
from __future__ import annotations

from typing import Any, TypedDict
from pydantic import BaseModel, Field

from chatbot.backend.schemas.student import StudentContext
from chatbot.backend.schemas.insight import StudentInsight
from chatbot.backend.schemas.planner import StudyPlan
from chatbot.backend.schemas.coach import CoachResponse
from chatbot.backend.schemas.chat import MessageSchema
from chatbot.backend.schemas.routing import IntentType


class ChatState(TypedDict):
    """
    LangGraph Workflow State TypedDict.
    Maintains execution context across graph nodes.
    """
    student_id: str
    user_message: str
    conversation_id: str | None
    student_context: StudentContext | None
    conversation_history: list[MessageSchema]
    intent: IntentType | str
    student_insight: StudentInsight | None
    study_plan: StudyPlan | None
    final_response: CoachResponse | None
    agents_used: list[str]
    metadata: dict[str, Any]


class ChatStateModel(BaseModel):
    """Pydantic representation of ChatState for serialization and validation."""
    student_id: str
    user_message: str
    conversation_id: str | None = None
    student_context: StudentContext | None = None
    conversation_history: list[MessageSchema] = Field(default_factory=list)
    intent: IntentType = IntentType.GENERAL_SUPPORT
    student_insight: StudentInsight | None = None
    study_plan: StudyPlan | None = None
    final_response: CoachResponse | None = None
    agents_used: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
