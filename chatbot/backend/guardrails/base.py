"""
Base Guardrail Interfaces for EduGuardian AI.

Defines abstract base classes for Input and Output guardrails.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from chatbot.backend.schemas.guardrails import GuardrailResult
from chatbot.backend.schemas.student import StudentContext


class BaseInputGuardrail(ABC):
    """Abstract interface for all input guardrail evaluators."""

    @abstractmethod
    def evaluate(
        self,
        user_message: str,
        student_context: StudentContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GuardrailResult:
        """
        Evaluates incoming user message against safety, privacy, and scope policies.

        Args:
            user_message: Raw user input text.
            student_context: Authenticated student academic context (if available).
            metadata: Optional additional execution parameters.

        Returns:
            GuardrailResult with action, category, and safe response if blocked.
        """
        pass


class BaseOutputGuardrail(ABC):
    """Abstract interface for all output guardrail evaluators."""

    @abstractmethod
    def evaluate(
        self,
        response_text: str,
        student_context: StudentContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GuardrailResult:
        """
        Evaluates outgoing assistant response against secret leaks, reasoning tags, and safety policies.

        Args:
            response_text: Candidate assistant response text.
            student_context: Authenticated student academic context (if available).
            metadata: Optional additional execution parameters.

        Returns:
            GuardrailResult with action, category, and sanitized/revised response.
        """
        pass
