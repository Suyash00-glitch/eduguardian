"""
Agent-to-Agent (A2A) Contract Models.

Defines the application-level payload models used when serializing tasks
and responses between autonomous agents.

Separates our application contracts from the low-level A2A transport protocol.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from chatbot.backend.schemas.student import StudentContext
from chatbot.backend.schemas.insight import StudentInsight
from chatbot.backend.schemas.planner import StudyPlan
from chatbot.backend.schemas.coach import CoachResponse


class A2AAgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    STUDENT_INSIGHT = "student_insight"
    STUDY_PLANNER = "study_planner"
    RECOVERY_COACH = "recovery_coach"


class A2ATaskType(str, Enum):
    GENERATE_INSIGHT = "generate_insight"
    GENERATE_PLAN = "generate_plan"
    GENERATE_COACHING = "generate_coaching"


class InsightTaskPayload(BaseModel):
    """Payload for Student Insight Agent task."""
    student_id: str
    student_context: StudentContext
    query_context: str | None = None


class PlannerTaskPayload(BaseModel):
    """Payload for Study Planner Agent task."""
    student_id: str
    student_context: StudentContext
    student_insight: StudentInsight | None = None
    user_goal: str | None = None
    timeframe_days: int = 7
    learning_history: dict[str, Any] | None = None


class CoachTaskPayload(BaseModel):
    """Payload for Recovery Coach Agent task."""
    student_id: str
    user_message: str
    student_context: StudentContext | None = None
    student_insight: StudentInsight | None = None
    study_plan: StudyPlan | None = None
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    learning_history: dict[str, Any] | None = None


class A2ATaskEnvelope(BaseModel):
    """Structured envelope wrapping an inter-agent task request."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: A2ATaskType
    sender: A2AAgentRole
    recipient: A2AAgentRole
    created_at: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any]


class A2AResultEnvelope(BaseModel):
    """Structured envelope wrapping an inter-agent task result."""
    task_id: str
    sender: A2AAgentRole
    recipient: A2AAgentRole
    status: str = "completed"  # 'completed' | 'failed'
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    result_data: dict[str, Any] | None = None
    error_message: str | None = None
