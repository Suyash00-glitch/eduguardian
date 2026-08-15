"""
Study Planner Agent Contracts.

Defines the request and response models for generating structured,
actionable study plans rendered directly in the chatbot frontend.
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from chatbot.backend.schemas.student import StudentContext
from chatbot.backend.schemas.insight import StudentInsight


class PriorityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StudyTask(BaseModel):
    """An individual actionable task within a study plan."""
    task_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for frontend tracking/completion",
    )
    title: str = Field(description="Short summary of the task")
    description: str = Field(
        default="",
        description="Detailed instructions on what and how to study",
    )
    subject: str = Field(description="Course or domain the task relates to")
    day: str | None = Field(
        default=None,
        description="Day of week (e.g. 'Monday') or relative period ('Day 1')",
    )
    time_slot: str | None = Field(
        default=None,
        description="Recommended time interval, e.g. '09:00–10:30'",
    )
    duration_minutes: int = Field(
        default=60,
        ge=10,
        le=360,
        description="Estimated duration in minutes",
    )
    priority: PriorityLevel = Field(
        default=PriorityLevel.MEDIUM,
        description="Priority weighting",
    )
    is_completed: bool = Field(
        default=False,
        description="Completion state tracked in frontend",
    )


class PlanMilestone(BaseModel):
    """Key check-in checkpoint or objective within the study timeframe."""
    milestone_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(description="Description of checkpoint achievement")
    target_day: str | None = Field(default=None, description="Target day for milestone")
    is_reached: bool = Field(default=False)


class PlanRequest(BaseModel):
    """Input payload for Study Planner Agent."""
    student_id: str
    student_context: StudentContext
    student_insight: StudentInsight | None = None
    user_goal: str | None = Field(
        default=None,
        description="Specific student goal (e.g., 'prepare for Math quiz on Friday')",
    )
    timeframe_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Plan duration in days",
    )
    existing_plan: StudyPlan | None = Field(
        default=None,
        description="Optional existing plan to revise or adjust",
    )


class StudyPlan(BaseModel):
    """
    Structured Study Plan returned by the Study Planner Agent.
    Directly renderable in the chatbot UI modal/cards.
    """
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(description="Title of the plan (e.g. 'Weekly Focused Revision Plan')")
    goals: list[str] = Field(
        default_factory=list,
        description="Primary academic objectives for this plan",
    )
    priorities: list[str] = Field(
        default_factory=list,
        description="Key subject priorities established for the timeframe",
    )
    week_start: str | None = Field(
        default=None,
        description="ISO date string for start of week (e.g. '2026-08-18')",
    )
    tasks: list[StudyTask] = Field(
        default_factory=list,
        description="List of daily/weekly study tasks",
    )
    milestones: list[PlanMilestone] = Field(
        default_factory=list,
        description="Checkpoints to evaluate progress",
    )
    resources: list[str] = Field(
        default_factory=list,
        description="Curated learning materials, textbook chapters, or LMS links",
    )
    notes: str | None = Field(
        default=None,
        description="Encouraging coach's tip or strategy for sticking to the plan",
    )
    rationale: str | None = Field(
        default=None,
        description="Why this specific schedule was prioritized",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
