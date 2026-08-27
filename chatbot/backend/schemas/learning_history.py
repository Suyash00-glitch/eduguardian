"""
LearningHistory Contract.

Defines the supplemental, interaction-derived learning history for a student
accumulated across EduGuardian chatbot sessions (quiz completions, tutoring interactions,
and explicit user preferences).

IMPORTANT ARCHITECTURAL RULE:
- StudentContext remains the sole authoritative academic profile (name, marks, attendance, etc.).
- LearningHistory NEVER duplicates or replaces StudentContext.
- It is strictly non-judgmental and topic-sensitive (no permanent student-level labels).
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class TopicQuizRecord(BaseModel):
    """Aggregated quiz metrics for a single topic."""
    topic: str
    attempts: int = Field(default=0, ge=0)
    total_score: float = Field(default=0.0, ge=0.0)
    total_possible: int = Field(default=0, ge=0)
    latest_score: float | None = None
    latest_total: int | None = None
    average_accuracy: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average score ratio across attempts (0.0 to 1.0)",
    )


class LearningHistory(BaseModel):
    """
    Lightweight, supplemental learning history derived from EduGuardian interactions.
    Strictly avoids duplicating StudentContext.
    """
    student_id: str = Field(description="Unique student identifier matching StudentContext")

    # Topic-level quiz mastery mapping (e.g., {"Binary Trees": 0.80, "Python": 1.0})
    quiz_mastery: dict[str, float] = Field(
        default_factory=dict,
        description="Topic -> average accuracy ratio (0.0 to 1.0)",
    )

    # Granular per-topic statistics
    topic_records: dict[str, TopicQuizRecord] = Field(
        default_factory=dict,
        description="Detailed quiz attempt records per topic",
    )

    # Topics where student demonstrated high mastery (>= 80% with repeated/solid evidence)
    mastered_topics: list[str] = Field(
        default_factory=list,
        description="Topics where student demonstrated high mastery",
    )

    # Topics where student recently struggled (< 50% with repeated/solid evidence)
    needs_practice_topics: list[str] = Field(
        default_factory=list,
        description="Topics where student recently struggled and benefits from foundational reinforcement",
    )

    # Explicitly stated student preferences (e.g. {'format': 'concise', 'examples': 'code'})
    explicit_preferences: dict[str, str] = Field(
        default_factory=dict,
        description="Explicit user preferences captured from conversation",
    )

    total_quizzes_completed: int = Field(
        default=0,
        ge=0,
        description="Total completed quiz sessions across all topics",
    )
