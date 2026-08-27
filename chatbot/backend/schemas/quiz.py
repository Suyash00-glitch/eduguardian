"""
Quiz Mode Contracts for EduGuardian AI.

Defines the typed models used for interactive Quizzes:
- Step progression (Awaiting Topic -> In Progress -> Completed)
- Single question tracking (MCQ and Short Answer)
- Backend mathematical scoring (1.0 = Correct, 0.5 = Partial, 0.0 = Incorrect)
- Answer history and final summary metrics
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class QuizDifficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuizQuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"


class QuizEvaluation(str, Enum):
    CORRECT = "correct"
    PARTIALLY_CORRECT = "partially_correct"
    INCORRECT = "incorrect"
    UNCLEAR = "unclear"


class QuizStep(str, Enum):
    AWAITING_TOPIC = "awaiting_topic"       # User asked "Quiz me", awaiting topic selection
    IN_PROGRESS = "in_progress"             # Active question presented, awaiting student answer
    COMPLETED = "completed"                 # Final question evaluated, final score and summary delivered


class QuizAnswerRecord(BaseModel):
    """Historical record of an individual answered quiz question."""
    question_number: int
    question_text: str
    question_type: QuizQuestionType = QuizQuestionType.MULTIPLE_CHOICE
    student_answer: str
    correct_answer: str | None = None
    is_correct: bool
    score_awarded: float = 0.0              # 1.0, 0.5, or 0.0
    explanation: str = ""


class QuizState(BaseModel):
    """
    Complete state representing an ongoing or completed Quiz session.
    Preserved in Message.structured_data across conversational turns.
    """
    active: bool = True
    topic: str
    difficulty: QuizDifficulty = QuizDifficulty.BEGINNER
    step: QuizStep = QuizStep.IN_PROGRESS
    current_question_number: int = 1
    total_questions: int = 5                # Default 5 (bounded between 1 and 15)
    current_question_type: QuizQuestionType = QuizQuestionType.MULTIPLE_CHOICE
    current_question_text: str | None = None
    current_options: list[str] | None = None # e.g. ["A. 1", "B. 2", "C. 3", "D. Unlimited"]
    current_correct_answer: str | None = None # Never exposed to frontend
    last_student_answer: str | None = None
    last_evaluation: QuizEvaluation | None = None
    score: float = 0.0
    history: list[QuizAnswerRecord] = Field(default_factory=list)
    difficulty_history: list[str] = Field(default_factory=list)
    recent_evaluations: list[bool] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        """
        Returns a sanitized dictionary representation safe for frontend consumption.
        Strictly strips current_correct_answer so students cannot cheat via devtools/network inspecting.
        """
        data = self.model_dump(mode="json")
        data.pop("current_correct_answer", None)
        return data
