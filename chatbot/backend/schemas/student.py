"""
StudentContext Contract.

Defines the structured academic record and contextual information needed by
the AI chatbot system.

CORE ARCHITECTURAL RULE:
This contract completely decouples the AI chatbot from teammate implementations
(portal scraping, authentication mechanisms, database models). Teammates map their
data into this contract; the AI chatbot consumes only this model.

NO passwords, session cookies, or credentials are ever present in this model.
All academic sub-structures support optional fields gracefully.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Union
from pydantic import BaseModel, Field


class AttendanceTrend(str, Enum):
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"


class RiskLevel(str, Enum):
    """
    Internal agent-to-agent coordination only.
    NEVER exposed to students.
    """
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class AttendanceSummary(BaseModel):
    """Attendance metrics across subjects and recent trends."""
    overall_percentage: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Overall attendance percentage (0-100)",
    )
    trend: AttendanceTrend | str | None = Field(
        default=None,
        description="Recent trajectory of attendance: 'improving' | 'declining' | 'stable'",
    )
    recent_trend: str | None = Field(
        default=None,
        description="Alias for trend",
    )
    classes_attended: int | None = Field(default=None, ge=0)
    total_classes: int | None = Field(default=None, ge=0)
    subjects_below_threshold: list[str] = Field(
        default_factory=list,
        description="Subjects where attendance is below college policy threshold",
    )


class SubjectPerformance(BaseModel):
    """Academic progress and metrics in a single subject/course."""
    subject_code: str | None = Field(default=None, description="Course/subject identifier code")
    subject_name: str = Field(description="Name of the subject")
    faculty_name: str | None = Field(default=None, description="Course instructor name")
    current_marks_percentage: float | None = Field(default=None, ge=0.0, le=100.0)
    marks_percentage: float | None = Field(default=None, ge=0.0, le=100.0)
    grade: str | None = Field(default=None, description="Letter grade if assigned")
    attendance_percentage: float | None = Field(default=None, ge=0.0, le=100.0)
    assignment_completion_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Ratio of assignments submitted (0.0 to 1.0)",
    )
    quiz_average: float | None = Field(default=None, ge=0.0, le=100.0)


class AssignmentSummary(BaseModel):
    """Summary of coursework and assignment submissions."""
    total_assigned: int = Field(default=0, ge=0)
    total_submitted: int = Field(default=0, ge=0)
    pending_count: int = Field(default=0, ge=0)
    average_score: float | None = Field(default=None, ge=0.0, le=100.0)
    upcoming_deadlines: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of upcoming assignments with due dates",
    )


class AssessmentSummary(BaseModel):
    """Summary of mid-terms, quizzes, and internal exam scores."""
    gpa: float | None = Field(default=None, ge=0.0, le=10.0, description="Current semester GPA/CGPA")
    quizzes_completed: int = Field(default=0, ge=0)
    average_quiz_score: float | None = Field(default=None, ge=0.0, le=100.0)
    recent_exam_scores: list[dict[str, Any]] = Field(default_factory=list)


class EngagementSummary(BaseModel):
    """LMS activity and portal interaction metrics (if tracked)."""
    lms_logins_last_30_days: int | None = Field(default=None, ge=0)
    study_materials_accessed: int | None = Field(default=None, ge=0)
    resources_accessed: int | None = Field(default=None, ge=0)
    discussion_forum_posts: int | None = Field(default=None, ge=0)
    forum_posts: int | None = Field(default=None, ge=0)
    last_active_at: datetime | None = None


# Alias for backwards compatibility
EngagementMetrics = EngagementSummary


class TrendInformation(BaseModel):
    """Historical academic trajectory and momentum indicators."""
    grade_trajectory: str | None = Field(
        default=None,
        description="Direction of overall marks: 'upward', 'downward', 'consistent'",
    )
    consistency_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Measure of submission/attendance consistency",
    )
    notable_changes: list[str] = Field(default_factory=list)


class InterventionHistory(BaseModel):
    """Record of prior academic coaching, study plans, or support provided."""
    intervention_id: str
    date_provided: datetime = Field(default_factory=datetime.utcnow)
    intervention_type: str = Field(description="'study_plan', 'mentor_session', 'resource_referral'")
    focus_subject: str | None = None
    outcome_notes: str | None = None


class StudentContext(BaseModel):
    """
    Complete Student Context model.
    Passed to the AI system to provide holistic, evidence-based academic context.
    """
    student_id: str = Field(description="Unique student identifier")
    student_name: str | None = Field(default=None, description="Student's display name")
    full_name: str | None = Field(default=None, description="Alias for student_name")
    department: str | None = Field(default=None, description="Academic department or major")
    program: str | None = Field(default=None, description="Academic degree program")
    year_of_study: int | None = Field(default=None, ge=1, le=6)
    semester: Union[int, str, None] = Field(default=None)

    # Modular academic structures
    attendance: AttendanceSummary | None = None
    subjects: list[SubjectPerformance] = Field(default_factory=list)
    assignments: AssignmentSummary | None = None
    assessments: AssessmentSummary | None = None
    engagement: EngagementSummary | None = None
    trends: TrendInformation | None = None
    interventions: list[Union[InterventionHistory, str]] = Field(default_factory=list)

    # Internal support context (never shown to student directly)
    risk_level: RiskLevel | str | None = Field(
        default=None,
        description="INTERNAL ONLY: Agent coordination support routing.",
    )
    previous_interventions: list[str] = Field(
        default_factory=list,
        description="Internal history of support actions.",
    )

    # Extensible metadata
    metadata: dict[str, Any] = Field(default_factory=dict)
