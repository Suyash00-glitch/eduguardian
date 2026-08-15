"""
Context Selection Layer for EduGuardian AI.

Selects only the minimal, relevant context package required for a specific request.
Prevents academic profile data or irrelevant identity records from leaking into unrelated prompts.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from chatbot.backend.schemas.student import StudentContext
from chatbot.backend.schemas.coach import CoachMessageItem
from chatbot.backend.schemas.routing import ProcessedRequest, RequestIntent, ResponseConstraints
from chatbot.backend.core.memory import UserFacts


class SelectedContext(BaseModel):
    """Minimal context package provided to downstream agents or LLMs."""
    user_identity_context: dict[str, Any] | None = None
    academic_context: StudentContext | None = None
    conversation_memory: list[CoachMessageItem] = Field(default_factory=list)
    request_constraints: ResponseConstraints = Field(default_factory=ResponseConstraints)
    inject_academic_insight: bool = False


def select_relevant_context(
    processed_request: ProcessedRequest,
    user_facts: UserFacts,
    student_context: StudentContext | None,
    conversation_history: list[Any],
) -> SelectedContext:
    """
    Constructs a scoped, minimized context package based on detected intent.
    """
    intent = processed_request.intent
    constraints = processed_request.constraints

    # Adapt history
    adapted_history: list[CoachMessageItem] = []
    for m in conversation_history:
        role = getattr(m, "role", "user")
        content = getattr(m, "content", str(m))
        adapted_history.append(CoachMessageItem(role=str(role), content=content))

    identity_dict: dict[str, Any] = {}
    if user_facts.name:
        identity_dict["name"] = user_facts.name
    if user_facts.hometown:
        identity_dict["hometown"] = user_facts.hometown
    if user_facts.location:
        identity_dict["location"] = user_facts.location

    # 1. Identity & Direct Factual Queries
    if intent in [RequestIntent.IDENTITY, RequestIntent.FACTUAL]:
        return SelectedContext(
            user_identity_context=identity_dict if identity_dict else None,
            academic_context=None,  # Zero academic records
            conversation_memory=adapted_history[-2:],
            request_constraints=constraints,
            inject_academic_insight=False,
        )

    # 2. Educational & Resource Requests
    if intent in [RequestIntent.EDUCATIONAL, RequestIntent.RESOURCE_REQUEST]:
        return SelectedContext(
            user_identity_context=None,
            academic_context=None,  # Zero academic records
            conversation_memory=adapted_history[-2:],
            request_constraints=constraints,
            inject_academic_insight=False,
        )

    # 3. Academic Insight & Study Planning Queries
    if intent in [RequestIntent.ACADEMIC_INSIGHT, RequestIntent.STUDY_PLAN]:
        return SelectedContext(
            user_identity_context=identity_dict if identity_dict else None,
            academic_context=student_context,
            conversation_memory=adapted_history[-6:],
            request_constraints=constraints,
            inject_academic_insight=True,
        )

    # 4. Emotional Support Queries
    if intent == RequestIntent.EMOTIONAL_SUPPORT:
        return SelectedContext(
            user_identity_context=identity_dict if identity_dict else None,
            academic_context=student_context,  # Passed for positive strength reinforcement
            conversation_memory=adapted_history[-4:],
            request_constraints=constraints,
            inject_academic_insight=True,
        )

    # 5. General Conversation / Greeting
    return SelectedContext(
        user_identity_context=identity_dict if identity_dict else None,
        academic_context=None,  # Zero academic records
        conversation_memory=adapted_history[-4:],
        request_constraints=constraints,
        inject_academic_insight=False,
    )
