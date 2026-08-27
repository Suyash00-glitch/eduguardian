"""
Study Planner Agent — Pydantic schemas.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from chatbot.backend.schemas.student import StudentContext
from chatbot.backend.agents.student_insight.schemas import InsightResponse


class PlanRequest(BaseModel):
    student_context: StudentContext
    insight: InsightResponse | None = None
    user_request: str = Field(
        description="The student's original message requesting a plan."
    )
    week_start_date: str | None = Field(
        default=None,
        description="ISO date string. Defaults to current week if not provided.",
    )


class PlanTask(BaseModel):
    day: str
    time_slot: str
    subject: str
    activity: str
    duration_minutes: int
    priority: str = Field(description="high | medium | low")


class PlanResponse(BaseModel):
    """
    Structured weekly study plan produced by the Study Planner Agent.
    This is converted to StudyPlanSchema before being sent to the frontend.
    """
    title: str
    week_start: str
    goals: list[str]
    tasks: list[PlanTask]
    resources: list[str] = Field(default_factory=list)
    notes: str = ""
    rationale: str = Field(
        description="Internal explanation of why this plan was structured this way.",
    )
