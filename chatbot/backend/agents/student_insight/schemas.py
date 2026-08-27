"""
Student Insight Agent — Pydantic schemas for request/response.

InsightRequest:  Input to the agent (what context to analyze).
InsightResponse: Structured internal analysis output.

IMPORTANT: InsightResponse is for internal agent use only.
Its fields (especially risk signals) must NEVER be directly
shown to the student in any UI or message text.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from chatbot.backend.schemas.student import StudentContext


class InsightRequest(BaseModel):
    student_context: StudentContext
    focus_question: str | None = Field(
        default=None,
        description="Optional specific question to focus the insight analysis on.",
    )


class SubjectInsight(BaseModel):
    subject_name: str
    status: str = Field(description="'strength' | 'needs_attention' | 'critical'")
    key_observation: str
    recommended_action: str


class InsightResponse(BaseModel):
    """
    Structured internal analysis of a student's academic situation.

    For agent orchestration ONLY.
    Do NOT serialize and send this to the frontend or student.
    """
    student_id: str
    overall_summary: str = Field(
        description="One-sentence internal summary of academic situation."
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Subjects or skills where the student is performing well.",
    )
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Subjects or areas needing immediate attention.",
    )
    subject_insights: list[SubjectInsight] = Field(default_factory=list)
    contributing_factors: list[str] = Field(
        default_factory=list,
        description="Possible causes (e.g. low attendance in Math correlates with low grade).",
    )
    recommended_areas_of_attention: list[str] = Field(
        default_factory=list,
        description="Prioritized list of interventions for the Recovery Coach.",
    )
    support_intensity: str = Field(
        default="standard",
        description="INTERNAL: 'light' | 'standard' | 'intensive' — drives coach tone.",
    )
    has_concerning_patterns: bool = Field(
        default=False,
        description="INTERNAL flag — if True, coach should be extra supportive.",
    )
