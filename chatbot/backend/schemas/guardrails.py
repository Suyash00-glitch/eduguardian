"""
Guardrails Data Contracts & Schemas for EduGuardian AI.

Defines the core data contracts for input and output guardrails:
- GuardrailAction: Resulting action (ALLOW, BLOCK, MODIFY, REVISE)
- GuardrailCategory: Classification category for policy violations and scope
- GuardrailResult: Detailed evaluation payload containing decisions, reasons, and sanitized content
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class GuardrailAction(str, Enum):
    """Action to take based on guardrail evaluation."""
    ALLOW = "allow"
    BLOCK = "block"
    MODIFY = "modify"
    REVISE = "revise"


class GuardrailCategory(str, Enum):
    """Primary categorization of guardrail triggers and safety checks."""
    PROMPT_INJECTION = "prompt_injection"
    PRIVACY_SENSITIVE_DATA = "privacy_sensitive_data"
    ACADEMIC_GROUNDING = "academic_grounding"
    OUTPUT_SAFETY = "output_safety"
    EMOTIONAL_SUPPORT = "emotional_support"
    SCOPE_RELEVANCE = "scope_relevance"
    NONE = "none"


class GuardrailResult(BaseModel):
    """
    Standardized result payload returned by input and output guardrails.
    """
    action: GuardrailAction = GuardrailAction.ALLOW
    category: GuardrailCategory = GuardrailCategory.NONE
    reason: str = ""
    sanitized_text: str | None = None
    blocked_response: str | None = Field(
        default=None,
        description="Safe, natural student-facing message returned when action is BLOCK.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_blocked(self) -> bool:
        """Returns True if the request or response is blocked."""
        return self.action == GuardrailAction.BLOCK

    @property
    def is_allowed(self) -> bool:
        """Returns True if the request or response is permitted without modification."""
        return self.action == GuardrailAction.ALLOW

    @property
    def is_modified(self) -> bool:
        """Returns True if the text was modified or revised by guardrails."""
        return self.action in (GuardrailAction.MODIFY, GuardrailAction.REVISE)
