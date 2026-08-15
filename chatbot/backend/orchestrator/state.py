"""
GraphState Contract for LangGraph Orchestration.

Maintains workflow state as execution flows across orchestrator nodes.
Aligns with shared domain contracts (StudentContext, StudentInsight, StudyPlan, CoachResponse).
"""
from __future__ import annotations

from typing import Any, TypedDict, Union
from chatbot.backend.schemas.student import StudentContext
from chatbot.backend.schemas.insight import StudentInsight
from chatbot.backend.schemas.planner import StudyPlan
from chatbot.backend.schemas.coach import CoachResponse
from chatbot.backend.schemas.routing import IntentType


class GraphState(TypedDict, total=False):
    """
    TypedDict representing the complete state for LangGraph workflow execution.
    Note: State key names are kept distinct from node names per LangGraph requirements.
    """
    # ── Input Fields ──────────────────────────────────────────────────────────
    student_id: str
    user_message: str
    conversation_id: str | None

    # Student context fetched from repository or passed in request
    student_context: StudentContext | None

    # Conversation history (last N messages) loaded from DB
    conversation_history: list[Any]

    # ── Intent Routing ────────────────────────────────────────────────────────
    # 'general_support' | 'academic_insight' | 'study_planning'
    intent: Union[IntentType, str]

    # Fine-grained response mode for the Recovery Coach
    # One of: direct_factual, identity, format_constrained, educational,
    #         task_request, resource_request, academic_insight, study_plan,
    #         emotional_support, conversational
    response_mode: str | None

    # Name resolved from conversation history (e.g. user said "my name is Ajmal")
    # Used when StudentContext.student_name is empty
    conversational_name: str | None

    # Structured user facts (name, hometown, location, interests)
    user_facts: dict[str, Any] | None

    # Full processed request metadata and format constraints
    processed_request: dict[str, Any] | None
    constraints: dict[str, Any] | None




    # ── Intermediate Outputs (Agent Results) ──────────────────────────────────
    insight_response: StudentInsight | None   # written by student_insight node
    plan_response: StudyPlan | None           # written by study_planner node

    # ── Final Student-Facing Output ───────────────────────────────────────────
    final_response: CoachResponse | None      # written by recovery_coach node

    # ── Observability & Tracking ──────────────────────────────────────────────
    agents_used: list[str]
    metadata: dict[str, Any]
