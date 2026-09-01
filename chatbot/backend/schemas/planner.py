"""
Study Planner Agent Contracts.

Defines the request and response models for generating structured,
actionable study plans rendered directly in the chatbot frontend.
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator

from chatbot.backend.schemas.student import StudentContext
from chatbot.backend.schemas.insight import StudentInsight


# ── Study Plan Intake State ───────────────────────────────────────────────────

class StudyPlanIntakeStep(str, Enum):
    """Steps in the guided study plan preference collection flow."""
    DAILY_TIME        = "daily_time"         # Q1: How much time per day?
    DAYS_AND_TIME     = "days_and_time"      # Q2: Which days + what time of day?
    SESSION_STYLE     = "session_style"      # Q3: Session structure preference
    GOAL              = "goal"               # Q4: Main study goal
    DEADLINES         = "deadlines"          # Q5: Upcoming exams / deadlines
    PRIORITY_SUBJECTS = "priority_subjects"  # Q6: Subject prioritization
    COMPLETE          = "complete"           # All answered — ready for LLM plan gen


class StudyPlanIntakeState(BaseModel):
    """
    Multi-turn study plan intake session state.

    Persisted in Message.structured_data["intake_state"] across conversation turns,
    following the same pattern as TeachingState and QuizState.
    """
    active: bool = True
    step: StudyPlanIntakeStep = StudyPlanIntakeStep.DAILY_TIME

    # Collected preferences (None = not yet answered by the student)
    daily_minutes: int | None = None
    study_days: list[str] | None = None       # e.g. ["Monday", "Tuesday", ...]
    preferred_time: str | None = None          # "morning" | "afternoon" | "evening" | "night"
    session_style: str | None = None           # "pomodoro" | "continuous" | "45min" | "flexible"
    main_goal: str | None = None               # "weak_subjects" | "exam_prep" | "improve_cgpa" | ...
    exam_deadlines: list[dict[str, Any]] = Field(default_factory=list)  # [{"subject": ..., "date": ...}]
    priority_subjects: list[str] = Field(default_factory=list)  # student-specified subject priorities

    # Raw student text for each answered step (passed verbatim to LLM prompt for nuance)
    raw_answers: dict[str, str] = Field(default_factory=dict)

    # How many times the current question has been re-asked (unrecognized answer)
    retry_count: int = 0


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
    subject: str = Field(
        default="General Study",
        description="Course or domain the task relates to (never None or empty)",
    )
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

    @field_validator("subject", mode="before")
    @classmethod
    def validate_subject(cls, v: Any) -> str:
        if v is None:
            return "General Study"
        s = str(v).strip()
        if not s or s.lower() in ("none", "null", "n/a", "undefined", "unknown"):
            return "General Study"
        return s

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: Any) -> str:
        if v is None:
            return "Focused Study Session"
        s = str(v).strip()
        if not s or s.lower() in ("none", "null", "n/a"):
            return "Focused Study Session"
        return s

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Any) -> PriorityLevel:
        if isinstance(v, PriorityLevel):
            return v
        if isinstance(v, str):
            clean = v.strip().lower()
            if clean in ("high", "urgent", "critical"):
                return PriorityLevel.HIGH
            elif clean in ("low", "optional"):
                return PriorityLevel.LOW
            return PriorityLevel.MEDIUM
        return PriorityLevel.MEDIUM

    @field_validator("duration_minutes", mode="before")
    @classmethod
    def validate_duration(cls, v: Any) -> int:
        try:
            val = int(v)
            return max(10, min(360, val))
        except (ValueError, TypeError):
            return 60


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
    learning_history: dict[str, Any] | None = Field(
        default=None,
        description="Supplemental interaction-derived learning history (topic records, preferences)",
    )
    student_preferences: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Parsed student study preferences extracted from conversation. "
            "Keys: daily_minutes (int), preferred_time (str: morning/afternoon/evening/night), "
            "schedule_mode (str: everyday/weekdays/weekends), excluded_days (list[str]), "
            "exam_timeframe (str|None), has_explicit_time (bool)."
        ),
    )


class StudyPlan(BaseModel):
    """
    Structured Study Plan returned by the Study Planner Agent.
    Directly renderable in the chatbot UI modal/cards.
    """
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(
        default="Personalized Study Plan",
        description="Title of the plan (e.g. 'Weekly Focused Revision Plan')",
    )
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

    @field_validator("week_start", mode="before")
    @classmethod
    def validate_week_start(cls, v: Any) -> str:
        from datetime import date
        if not v or not isinstance(v, str) or str(v).strip().lower() in ("none", "null", ""):
            return date.today().isoformat()
        return str(v).strip()

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: Any) -> str:
        if not v or not isinstance(v, str) or str(v).strip().lower() in ("none", "null", ""):
            return "Personalized Study Schedule"
        return str(v).strip()
