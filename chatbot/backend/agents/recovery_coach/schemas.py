"""
Recovery Coach Agent — Pydantic schemas.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from chatbot.backend.agents.student_insight.schemas import InsightResponse
from chatbot.backend.agents.study_planner.schemas import PlanResponse
from chatbot.backend.schemas.chat import MessageSchema


class CoachRequest(BaseModel):
    student_name: str
    user_message: str
    conversation_history: list[MessageSchema] = Field(default_factory=list)
    insight: InsightResponse | None = None
    plan: PlanResponse | None = None


class CoachResponse(BaseModel):
    """
    The final student-facing response from the Recovery Coach Agent.
    """
    response_text: str = Field(
        description="Warm, encouraging, student-facing natural language response."
    )
    has_study_plan: bool = False
    study_plan_title: str | None = None
