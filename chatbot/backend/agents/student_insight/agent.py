"""
Student Insight Agent Implementation.

The Student Insight Agent performs internal academic analysis of a student's
performance, attendance, submissions, and trajectories to generate evidence-based
insight.

It does NOT interact directly with students.
Its output is consumed by the Study Planner and Recovery Coach.
"""
from __future__ import annotations

import logging
from typing import Any

from chatbot.backend.agents.student_insight.analyzer import synthesize_academic_insight
from chatbot.backend.agents.student_insight.ml_adapter import (
    BaselineRulePredictor,
    FeatureExtractor,
    MLPredictorInterface,
)
from chatbot.backend.schemas.student import StudentContext
from chatbot.backend.schemas.insight import InsightRequest, StudentInsight

logger = logging.getLogger(__name__)


class StudentInsightAgent:
    """
    Student Insight Agent Service.

    Combines explainable deterministic rule/trend analysis with pluggable
    ML prediction models (LightGBM/XGBoost/SHAP).
    """

    def __init__(self, ml_predictor: MLPredictorInterface | None = None) -> None:
        self._ml_predictor = ml_predictor or BaselineRulePredictor()

    def analyze(self, request: InsightRequest | StudentContext) -> StudentInsight:
        """
        Synchronous analysis method.

        Consumes:
            request: InsightRequest or StudentContext
        Returns:
            StudentInsight: Structured, evidence-based academic insight.
        """
        # Resolve StudentContext and query context
        if isinstance(request, InsightRequest):
            context = request.student_context
            query_context = request.query_context
        else:
            context = request
            query_context = None

        logger.info("StudentInsightAgent: Analyzing records for student_id=%s", context.student_id)

        # 1. Run deterministic rule-based analysis
        insight = synthesize_academic_insight(context, query_context=query_context)

        # 2. Run ML prediction & feature attribution (if available)
        try:
            features = FeatureExtractor.extract_features(context)
            ml_result = self._ml_predictor.predict(features)

            # Enrich insight with ML prediction indicators if intensity elevated
            if ml_result.support_intensity == "intensive":
                insight.support_intensity = "intensive"
                insight.has_concerning_patterns = True
            elif ml_result.support_intensity == "guided" and insight.support_intensity == "standard":
                insight.support_intensity = "guided"

            if ml_result.feature_attributions:
                insight.metadata["ml_feature_attributions"] = ml_result.feature_attributions
        except Exception as exc:
            logger.warning("StudentInsightAgent: ML predictor step skipped (%s)", exc)

        logger.info(
            "StudentInsightAgent: Analysis complete for student_id=%s (intensity=%s, concerning=%s)",
            context.student_id,
            insight.support_intensity,
            insight.has_concerning_patterns,
        )
        return insight

    async def analyze_async(self, request: InsightRequest | StudentContext) -> StudentInsight:
        """Asynchronous wrapper for agent invocation."""
        return self.analyze(request)


# ── LangGraph Node Wrapper (for orchestrator execution) ───────────────────────

async def student_insight_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node execution wrapper for StudentInsightAgent."""
    agent = StudentInsightAgent()

    context = state.get("student_context")
    if not context:
        logger.warning("StudentInsightAgent: No student_context in graph state — returning None")
        return {
            **state,
            "insight_response": None,
            "student_insight": None,
            "agents_used": state.get("agents_used", []) + ["student_insight"],
        }

    request = InsightRequest(
        student_id=state.get("student_id", context.student_id),
        student_context=context,
        query_context=state.get("user_message"),
    )

    try:
        insight = await agent.analyze_async(request)
    except Exception as exc:
        logger.error("StudentInsightAgent: Node execution failed (%s) — continuing gracefully", exc)
        insight = None

    return {
        **state,
        "insight_response": insight,
        "student_insight": insight,
        "agents_used": state.get("agents_used", []) + ["student_insight"],
    }
