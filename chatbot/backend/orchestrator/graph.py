"""
LangGraph Orchestrator — Workflow State Management, Fast-Path Routing & Response Validation.

Pipeline:
  START
    │
    ▼
  [prepare_context]
    │
    ▼
  [request_processor] (Intent Detection, Constraint Parsing, Fact Resolution)
    │
    ├─── (Deterministic Fast-Path) ──────────────────────────────► [response_validator]
    │                                                                     ▲
    ├─── "general_support" ──────────────────────► [recovery_coach] ──────┤
    │                                                     ▲               │
    ├─── "academic_insight" ────► [student_insight] ──────┤               │
    │                                     │               │               │
    └─── "study_planning" ──────► [student_insight]       │               │
                                          │               │               │
                                          ▼               │               │
                                   [study_planner] ───────┘               │
                                                                          ▼
                                                                         END
"""
from __future__ import annotations

import logging
import time
from typing import Any, cast

from langgraph.graph import END, START, StateGraph


from chatbot.backend.a2a.client import (
    StudentInsightA2AClient,
    StudyPlannerA2AClient,
    RecoveryCoachA2AClient,
)
from chatbot.backend.config import get_settings
from chatbot.backend.orchestrator.router import (
    process_user_request,
    route_after_insight,
    route_after_intent,
    classify_intent_detailed,
    classify_intent,
)
from chatbot.backend.core.memory import resolve_user_facts, UserFacts
from chatbot.backend.orchestrator.validator import ResponseValidator
from chatbot.backend.orchestrator.state import GraphState
from chatbot.backend.schemas.insight import InsightRequest, StudentInsight
from chatbot.backend.schemas.planner import PlanRequest, StudyPlan
from chatbot.backend.schemas.coach import CoachRequest, CoachResponse, CoachMessageItem
from chatbot.backend.schemas.routing import ResponseConstraints, ProcessedRequest, RequestIntent

logger = logging.getLogger(__name__)


# ── Graph Nodes ───────────────────────────────────────────────────────────────

async def prepare_context_node(state: GraphState) -> dict[str, Any]:
    """Initial node: prepares context, initializes tracing metadata, and sets start time."""
    logger.info(
        "Orchestrator: Starting workflow for student_id=%s (conv_id=%s)",
        state.get("student_id"),
        state.get("conversation_id"),
    )
    metadata = dict(state.get("metadata") or {})
    metadata["start_time"] = time.time()

    return {
        **state,
        "agents_used": list(state.get("agents_used") or []),
        "metadata": metadata,
    }


async def request_processor_node(state: GraphState) -> dict[str, Any]:
    """
    Request Processor Node:
    1. Extracts and resolves user facts from history & current message.
    2. Parses explicit format constraints (one_word, one_sentence, exact_items, etc.).
    3. Checks for deterministic fast-paths (identity lookup, arithmetic, simple QA).
    4. Categorizes semantic request intent and response mode.
    """
    msg = state.get("user_message", "") or ""
    ctx = state.get("student_context")
    existing_name = (ctx.student_name or ctx.full_name or "").strip() if ctx else ""
    history = state.get("conversation_history") or []

    # 1. Resolve user facts
    user_facts = resolve_user_facts(history, msg, known_name=existing_name)
    conversational_name = user_facts.name

    # 2. Process request & constraints
    processed = process_user_request(msg, user_facts, ctx)

    logger.info(
        "RequestProcessor: Intent='%s' Mode='%s' Deterministic=%s for message: %r",
        processed.intent.value,
        processed.response_mode.value,
        processed.is_deterministic,
        msg[:80],
    )

    updates: dict[str, Any] = {
        "intent": processed.workflow_intent.value,
        "response_mode": processed.response_mode.value,
        "conversational_name": conversational_name,
        "user_facts": user_facts.model_dump(),
        "constraints": processed.constraints.model_dump(),
        "processed_request": processed.model_dump(),
    }

    # If deterministic fast-path applies, pre-populate final_response
    if processed.is_deterministic and processed.deterministic_answer is not None:
        updates["final_response"] = CoachResponse(
            response_text=processed.deterministic_answer,
            has_study_plan=False,
            study_plan=None,
            suggested_followups=[],
            resources=[],
            metadata={"fast_path": True, "intent": processed.intent.value},
        )

    return {
        **state,
        **updates,
    }


# Backwards compatibility alias for classify_intent_node
classify_intent_node = request_processor_node




async def student_insight_node(state: GraphState) -> dict[str, Any]:
    """Orchestrator node invoking Student Insight Agent via A2A client."""
    context = state.get("student_context")
    if not context:
        logger.warning("StudentInsightNode: No student_context in state — returning None")
        return {
            **state,
            "insight_response": None,
            "agents_used": state.get("agents_used", []) + ["student_insight"],
        }

    request = InsightRequest(
        student_id=state.get("student_id", context.student_id),
        student_context=context,
        query_context=state.get("user_message"),
    )

    settings = get_settings()
    insight: StudentInsight | None = None

    try:
        if settings.a2a_use_remote_services:
            logger.info("StudentInsightNode: Dispatching InsightRequest to Student Insight Agent over official A2A SDK (:8001)")
            client = StudentInsightA2AClient()
            insight = await client.analyze(request)
        else:
            from chatbot.backend.agents.student_insight.agent import StudentInsightAgent
            insight = await StudentInsightAgent().analyze_async(request)
    except Exception as exc:
        logger.error("StudentInsightNode: Execution failed (%s) — continuing gracefully", exc)
        insight = None

    return {
        **state,
        "insight_response": insight,
        "agents_used": state.get("agents_used", []) + ["student_insight"],
    }


async def study_planner_node(state: GraphState) -> dict[str, Any]:
    """Orchestrator node invoking Study Planner Agent via A2A client."""
    context = state.get("student_context")
    if not context:
        logger.warning("StudyPlannerNode: No student_context in state — cannot generate plan")
        return {
            **state,
            "plan_response": None,
            "agents_used": state.get("agents_used", []) + ["study_planner"],
        }

    request = PlanRequest(
        student_id=state.get("student_id", context.student_id),
        student_context=context,
        student_insight=state.get("insight_response"),
        existing_plan=state.get("plan_response"),
        user_goal=state.get("user_message", "Create a study plan for me"),
    )

    settings = get_settings()
    plan: StudyPlan | None = None

    try:
        if settings.a2a_use_remote_services:
            logger.info("StudyPlannerNode: Dispatching PlanRequest to Study Planner Agent over official A2A SDK (:8002)")
            client = StudyPlannerA2AClient()
            plan = await client.create_plan(request)
        else:
            from chatbot.backend.agents.study_planner.agent import StudyPlannerAgent
            plan = await StudyPlannerAgent().create_plan_async(request)
    except Exception as exc:
        logger.error("StudyPlannerNode: Execution failed (%s) — continuing gracefully", exc)
        plan = None

    return {
        **state,
        "plan_response": plan,
        "agents_used": state.get("agents_used", []) + ["study_planner"],
    }


async def recovery_coach_node(state: GraphState) -> dict[str, Any]:
    """Orchestrator node invoking Recovery Coach Agent via A2A client."""
    history = state.get("conversation_history", [])
    adapted_history = []
    for m in history:
        if isinstance(m, dict):
            role = str(m.get("role", "user"))
            content = str(m.get("content", "") or "")
        else:
            role = str(getattr(m, "role", "user"))
            content = str(getattr(m, "content", "") or "")
        adapted_history.append(CoachMessageItem(role=role, content=content))


    request = CoachRequest(
        student_id=state.get("student_id", "unknown"),
        user_message=state.get("user_message", ""),
        student_context=state.get("student_context"),
        conversation_history=adapted_history,
        student_insight=state.get("insight_response"),
        study_plan=state.get("plan_response"),
        response_mode=state.get("response_mode"),
        conversational_name=state.get("conversational_name"),
        user_facts=state.get("user_facts"),
        constraints=state.get("constraints"),
    )

    settings = get_settings()
    response: CoachResponse | None = None

    if settings.a2a_use_remote_services:
        logger.info("RecoveryCoachNode: Dispatching CoachRequest to Recovery Coach Agent over official A2A SDK (:8003)")
        client = RecoveryCoachA2AClient()
        response = await client.generate_response(request)
    else:
        from chatbot.backend.agents.recovery_coach.agent import RecoveryCoachAgent
        response = await RecoveryCoachAgent().generate_response(request)

    return {
        **state,
        "final_response": response,
        "agents_used": state.get("agents_used", []) + ["recovery_coach"],
    }


async def response_validator_node(state: GraphState) -> dict[str, Any]:

    """
    Response Validation Node:
    Validates, sanitizes, and enforces response constraints before student-facing delivery.
    """
    final_resp: CoachResponse | None = state.get("final_response")
    if not final_resp or not final_resp.response_text:
        return state

    constraints_dict = state.get("constraints") or {}
    constraints = ResponseConstraints(**constraints_dict)

    user_facts_dict = state.get("user_facts") or {}
    user_facts = UserFacts(**user_facts_dict)

    proc_dict = state.get("processed_request") or {}
    req_intent_str = proc_dict.get("intent", "general_conversation")
    try:
        req_intent = RequestIntent(req_intent_str)
    except Exception:
        req_intent = RequestIntent.GENERAL_CONVERSATION

    # Enforce constraints and safety
    validated_text = ResponseValidator.validate_and_enforce(
        response_text=final_resp.response_text,
        constraints=constraints,
        user_facts=user_facts,
        intent=req_intent,
    )

    final_resp.response_text = validated_text
    logger.info("ResponseValidator: Validated response (%d chars)", len(validated_text))

    return {
        **state,
        "final_response": final_resp,
    }


# ── Graph Construction ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Constructs the LangGraph StateGraph with fast-paths and response validation."""
    graph = StateGraph(GraphState)

    # ── Register Nodes ────────────────────────────────────────────────────────
    graph.add_node("prepare_context", prepare_context_node)
    graph.add_node("request_processor", request_processor_node)
    graph.add_node("student_insight", student_insight_node)
    graph.add_node("study_planner", study_planner_node)
    graph.add_node("recovery_coach", recovery_coach_node)
    graph.add_node("response_validator", response_validator_node)

    # ── Entry Point ───────────────────────────────────────────────────────────
    graph.add_edge(START, "prepare_context")
    graph.add_edge("prepare_context", "request_processor")

    # ── Conditional Routing after Request Processor ───────────────────────────
    graph.add_conditional_edges(
        "request_processor",
        route_after_intent,
        {
            "response_validator": "response_validator",
            "student_insight": "student_insight",
            "recovery_coach": "recovery_coach",
        },
    )

    # ── Conditional Routing after Student Insight ─────────────────────────────
    graph.add_conditional_edges(
        "student_insight",
        route_after_insight,
        {
            "study_planner": "study_planner",
            "recovery_coach": "recovery_coach",
        },
    )

    # ── Study Planner always transitions to Recovery Coach ────────────────────
    graph.add_edge("study_planner", "recovery_coach")

    # ── Recovery Coach transitions to Response Validator ──────────────────────
    graph.add_edge("recovery_coach", "response_validator")

    # ── Response Validator is always the terminal output node ─────────────────
    graph.add_edge("response_validator", END)

    return graph


# Compile once at startup
_compiled_graph = build_graph().compile()


async def run_graph(initial_state: GraphState) -> GraphState:
    """Executes the compiled LangGraph workflow with the provided state."""
    logger.info("Executing LangGraph workflow for student_id=%s", initial_state.get("student_id"))
    final_state = await _compiled_graph.ainvoke(initial_state)
    return cast(GraphState, final_state)

