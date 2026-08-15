"""
Study Planner Agent Implementation.

The Study Planner Agent converts student context, academic insight, and user goals
into an actionable, structured, and manageable StudyPlan.

It is a specialist planning agent invoked conditionally when study scheduling is needed.
"""
from __future__ import annotations

import logging
from typing import Any

from chatbot.backend.agents.study_planner.builder import (
    build_default_plan,
    parse_llm_plan_json,
)
from chatbot.backend.agents.study_planner.prompts import (
    STUDY_PLANNER_SYSTEM_PROMPT,
    build_study_planner_user_prompt,
)
from chatbot.backend.schemas.planner import PlanRequest, StudyPlan
from chatbot.backend.llm.base import BaseLLMClient
from chatbot.backend.llm.omniroute import create_llm_client

logger = logging.getLogger(__name__)


class StudyPlannerAgent:
    """
    Study Planner Agent Service.

    Generates structured study plans using LLM prompt reasoning with
    deterministic fallback and deadline prioritization.
    """

    def __init__(self, llm_client: BaseLLMClient | None = None) -> None:
        self._llm_client = llm_client or create_llm_client()

    async def create_plan_async(self, request: PlanRequest) -> StudyPlan:
        """
        Asynchronously generates a structured StudyPlan.

        Consumes:
            request: PlanRequest (student context, insight, user goal, timeframe)
        Returns:
            StudyPlan: Typed machine-readable study plan
        """
        student_id = request.student_id
        logger.info("StudyPlannerAgent: Generating plan for student_id=%s", student_id)

        user_prompt = build_study_planner_user_prompt(request)

        try:
            raw_text = await self._llm_client.complete_simple(
                system_prompt=STUDY_PLANNER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=2048,
            )
            plan = parse_llm_plan_json(raw_text, request)
            logger.info("StudyPlannerAgent: Plan generated with %d tasks", len(plan.tasks))
            return plan

        except Exception as exc:
            logger.error("StudyPlannerAgent: LLM completion failed (%s) — returning structured baseline plan", exc)
            return build_default_plan(request)

    def create_plan(self, request: PlanRequest) -> StudyPlan:
        """Synchronous wrapper for deterministic plan creation."""
        return build_default_plan(request)


# ── LangGraph Node Wrapper (for orchestrator execution) ───────────────────────

async def study_planner_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node execution wrapper for StudyPlannerAgent."""
    agent = StudyPlannerAgent()

    context = state.get("student_context")
    if not context:
        logger.warning("StudyPlannerAgent: No student_context in state — cannot generate plan")
        return {
            **state,
            "plan_response": None,
            "study_plan": None,
            "agents_used": state.get("agents_used", []) + ["study_planner"],
        }

    request = PlanRequest(
        student_id=state.get("student_id", context.student_id),
        student_context=context,
        student_insight=state.get("insight_response") or state.get("student_insight"),
        user_goal=state.get("user_message", "Create a study plan for me"),
    )

    try:
        plan = await agent.create_plan_async(request)
    except Exception as exc:
        logger.error("StudyPlannerAgent: Node execution failed (%s) — continuing gracefully", exc)
        plan = None

    return {
        **state,
        "plan_response": plan,
        "study_plan": plan,
        "agents_used": state.get("agents_used", []) + ["study_planner"],
    }
