"""
Student Insight Agent Contracts.

Defines the input request and output structured insight models for the
Student Insight Agent.

PRODUCT PHILOSOPHY & SAFETY RULE:
- Internal analytical fields (`support_intensity`, `has_concerning_patterns`) are
  strictly for agent-to-agent decision context.
- They are NEVER to be rendered directly to the student or phrased judgmentally.
- The model surfaces evidence (strengths, focus areas, observations) enabling the
  Recovery Coach to respond constructively and supportively.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from chatbot.backend.schemas.student import StudentContext


class SubjectInsight(BaseModel):
    """Granular observation and recommendation for an individual subject."""
    subject_name: str = Field(description="Name of the course/subject")
    status: str = Field(
        description="'strong' | 'steady' | 'needs_focus' | 'needs_practice'",
    )
    key_observation: str = Field(
        description="Factual, neutral observation about progress or attendance",
    )
    recommended_action: str = Field(
        description="Actionable, positive suggestion for the student",
    )


class InsightRequest(BaseModel):
    """Input payload for Student Insight Agent."""
    student_id: str
    student_context: StudentContext
    query_context: str | None = Field(
        default=None,
        description="Optional current student question or topic of interest",
    )


class StudentInsight(BaseModel):
    """
    Structured analytical output produced by Student Insight Agent.
    Transferred to Study Planner Agent and Recovery Coach Agent.
    """
    student_id: str
    overall_summary: str = Field(
        description="Holistic summary of academic standing and progress",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Subjects or areas where the student is excelling",
    )
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Topics/courses that will benefit most from targeted study time",
    )
    subject_insights: list[SubjectInsight] = Field(
        default_factory=list,
        description="Detailed insights per course",
    )
    contributing_factors: list[str] = Field(
        default_factory=list,
        description="Root factors (e.g. attendance gaps, pending lab assignments)",
    )
    recommended_areas_of_attention: list[str] = Field(
        default_factory=list,
        description="Prioritized list of subjects/skills to focus on next",
    )
    explanation: str = Field(
        default="",
        description="Evidence-based reasoning behind the focus recommendations",
    )

    # ── Internal Agent-to-Agent Coordination (NOT exposed to student) ────────
    support_intensity: str = Field(
        default="standard",
        description="INTERNAL ONLY: 'standard' | 'guided' | 'intensive'",
    )
    has_concerning_patterns: bool = Field(
        default=False,
        description="INTERNAL ONLY: Flag indicating rapid decline requiring proactive planning",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
