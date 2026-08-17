"""
Teaching & Tutoring Mode Contracts for EduGuardian AI.

Defines the minimal typed state model used for the interactive 'Teach Me'
tutoring loop (concept -> example -> question -> answer -> evaluate -> adapt).
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class TeachingDifficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TeachingEvaluation(str, Enum):
    CORRECT = "correct"
    PARTIALLY_CORRECT = "partially_correct"
    INCORRECT = "incorrect"
    UNCLEAR = "unclear"


class TeachingStep(str, Enum):
    AWAITING_TOPIC = "awaiting_topic"       # User said "teach me something", waiting for topic
    TEACHING = "teaching"                   # Actively explaining / questioning
    AWAITING_ANSWER = "awaiting_answer"     # Question asked, waiting for student response
    COMPLETED = "completed"                 # Session completed or stopped


class TeachingState(BaseModel):
    """
    Minimal state representing an active or completed tutoring session.
    Serialized and preserved in Message.structured_data across turns.
    """
    active: bool = True
    topic: str
    difficulty: TeachingDifficulty = TeachingDifficulty.BEGINNER
    current_concept: str | None = None
    current_question: str | None = None
    last_student_answer: str | None = None
    last_evaluation: TeachingEvaluation | None = None
    step: TeachingStep = TeachingStep.TEACHING
    support_level: int = Field(default=0, ge=0, le=4, description="Adaptive teaching support level: 0=normal, 1=simpler+example, 2=analogy, 3=step-by-step, 4=interactive")
    confusion_count: int = Field(default=0, ge=0, description="Consecutive confusion signals on current topic")
    support_strategy: str = Field(default="normal", description="Current teaching strategy name")
    metadata: dict[str, Any] = Field(default_factory=dict)

