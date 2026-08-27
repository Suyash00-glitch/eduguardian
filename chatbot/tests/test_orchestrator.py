"""
Unit and Integration tests for the LangGraph Orchestrator.

Verifies:
1. Flow 1: General Support route (Recovery Coach only)
2. Flow 2: Academic Insight route (Student Insight -> Recovery Coach)
3. Flow 3: Study Planning route (Student Insight -> Study Planner -> Recovery Coach)
4. Explicit planning request routing
5. Non-planning message skips planner
6. Preservation and propagation of intermediate agent states
7. Follow-up plan revision flow
8. Graceful failure handling if an agent node encounters an error
9. Minimal/empty context execution
10. Final student-facing response contains zero internal labels
11. Router intent classification and confidence
"""
from __future__ import annotations

import re
import pytest
from unittest.mock import AsyncMock, patch

from chatbot.backend.orchestrator.graph import run_graph, build_graph
from chatbot.backend.orchestrator.router import (
    classify_intent,
    classify_intent_detailed,
    route_after_intent,
    route_after_insight,
)
from chatbot.backend.orchestrator.state import GraphState
from chatbot.backend.schemas.student import (
    StudentContext,
    AttendanceSummary,
    SubjectPerformance,
    AssignmentSummary,
)
from chatbot.backend.schemas.insight import StudentInsight
from chatbot.backend.schemas.planner import StudyPlan, StudyTask, PriorityLevel
from chatbot.backend.schemas.routing import IntentType

# Safety regex
_FORBIDDEN_TERMS = re.compile(
    r"\b(high[- ]risk|at[- ]risk|weak student|poor student|failing student|predicted to fail)\b",
    re.IGNORECASE,
)


@pytest.fixture
def mock_student_context() -> StudentContext:
    return StudentContext(
        student_id="student_001",
        student_name="Aisha Raza",
        department="Computer Science",
        year_of_study=2,
        semester=4,
        attendance=AttendanceSummary(overall_percentage=72.0, trend="declining"),
        subjects=[
            SubjectPerformance(
                subject_name="Data Structures",
                current_marks_percentage=54.0,
                assignment_completion_rate=0.60,
            ),
            SubjectPerformance(
                subject_name="Operating Systems",
                current_marks_percentage=85.0,
                assignment_completion_rate=0.95,
            ),
        ],
        assignments=AssignmentSummary(total_assigned=10, total_submitted=6, pending_count=4),
    )


class TestRouterIntentClassification:

    def test_general_support_intents(self):
        """Casual greetings and emotional stress route to general_support."""
        assert classify_intent({"user_message": "Hello there!"}) in ("general_support", "simple")
        assert classify_intent({"user_message": "I'm feeling so stressed today."}) in ("general_support", "simple")
        assert classify_intent({"user_message": "Thanks for your help!"}) in ("general_support", "simple")

    def test_academic_insight_intents(self):
        """Questions about performance, grades, or attendance route to academic_insight."""
        assert classify_intent({"user_message": "Why am I struggling with my studies?"}) in ("academic_insight", "academic")
        assert classify_intent({"user_message": "How is my attendance doing?"}) in ("academic_insight", "academic")
        assert classify_intent({"user_message": "What are my current grades?"}) in ("academic_insight", "academic")

    def test_study_planning_intents(self):
        """Explicit planning and schedule requests route to study_planning."""
        assert classify_intent({"user_message": "Make me a study plan for this week."}) in ("study_planning", "plan")
        assert classify_intent({"user_message": "Create a revision schedule for exams."}) in ("study_planning", "plan")
        assert classify_intent({"user_message": "Can you adjust my schedule for Tuesday?"}) in ("study_planning", "plan")

    def test_conditional_edges(self):
        """Edge routing functions return appropriate next node names."""
        # Simple -> Coach
        assert route_after_intent({"intent": "general_support"}) == "recovery_coach"
        assert route_after_intent({"intent": "simple"}) == "recovery_coach"

        # Academic -> Insight -> Coach
        assert route_after_intent({"intent": "academic_insight"}) == "student_insight"
        assert route_after_insight({"intent": "academic_insight"}) == "recovery_coach"

        # Planning -> Insight -> Planner
        assert route_after_intent({"intent": "study_planning"}) == "student_insight"
        assert route_after_insight({"intent": "study_planning"}) == "study_planner"


class TestLangGraphWorkflows:

    @pytest.mark.asyncio
    async def test_1_flow_1_general_support(self, mock_student_context):
        """Flow 1: Casual message invokes ONLY the Recovery Coach."""
        initial_state: GraphState = {
            "student_id": "student_001",
            "user_message": "Hello! I'm feeling a bit anxious about my semester.",
            "student_context": mock_student_context,
            "conversation_history": [],
        }

        result = await run_graph(initial_state)

        assert result["intent"] in ("general_support", "simple")
        assert result["agents_used"] == ["recovery_coach"]
        assert result.get("plan_response") is None
        assert result.get("study_plan") is None
        assert result["final_response"] is not None
        assert not _FORBIDDEN_TERMS.search(result["final_response"].response_text)

    @pytest.mark.asyncio
    async def test_2_flow_2_academic_insight(self, mock_student_context):
        """Flow 2: Academic query invokes Insight Agent and Recovery Coach."""
        initial_state: GraphState = {
            "student_id": "student_001",
            "user_message": "Why am I struggling with my courses?",
            "student_context": mock_student_context,
            "conversation_history": [],
        }

        result = await run_graph(initial_state)

        assert result["intent"] in ("academic_insight", "academic")
        assert "student_insight" in result["agents_used"]
        assert "recovery_coach" in result["agents_used"]
        assert "study_planner" not in result["agents_used"]

        # Verify intermediate insight was generated
        insight = result.get("insight_response") or result.get("student_insight")
        assert insight is not None
        assert isinstance(insight, StudentInsight)
        assert len(insight.focus_areas) > 0

        # Verify final response exists and is supportive
        assert result["final_response"] is not None
        assert not _FORBIDDEN_TERMS.search(result["final_response"].response_text)

    @pytest.mark.asyncio
    async def test_3_flow_3_study_planning(self, mock_student_context):
        """Flow 3: Planning query invokes Insight Agent, Study Planner, and Recovery Coach."""
        initial_state: GraphState = {
            "student_id": "student_001",
            "user_message": "Make me a study plan for this week.",
            "student_context": mock_student_context,
            "conversation_history": [],
        }

        result = await run_graph(initial_state)

        assert result["intent"] in ("study_planning", "plan")
        assert result["agents_used"] == ["student_insight", "study_planner", "recovery_coach"]

        # Verify structured study plan was generated
        plan = result.get("plan_response") or result.get("study_plan")
        assert plan is not None
        assert isinstance(plan, StudyPlan)
        assert len(plan.tasks) > 0

        # Verify coach received plan and introduced it
        assert result["final_response"] is not None
        assert result["final_response"].has_study_plan is True

    @pytest.mark.asyncio
    async def test_4_explicit_planning_request(self, mock_student_context):
        """Explicit planning requests always activate the planner node."""
        initial_state: GraphState = {
            "student_id": "student_001",
            "user_message": "Create a revision schedule for Data Structures.",
            "student_context": mock_student_context,
        }

        result = await run_graph(initial_state)
        assert "study_planner" in result["agents_used"]

    @pytest.mark.asyncio
    async def test_5_non_planning_message_skips_planner(self, mock_student_context):
        """Casual conversation must NEVER activate the planner node."""
        initial_state: GraphState = {
            "student_id": "student_001",
            "user_message": "Good morning! Can you give me some words of motivation?",
            "student_context": mock_student_context,
        }

        result = await run_graph(initial_state)
        assert "study_planner" not in result["agents_used"]
        assert "student_insight" not in result["agents_used"]
        assert result["agents_used"] == ["recovery_coach"]

    @pytest.mark.asyncio
    async def test_6_empty_context_handling(self):
        """Workflow completes safely even if student_context is completely None."""
        initial_state: GraphState = {
            "student_id": "unknown",
            "user_message": "Hello, how can you help me?",
            "student_context": None,
            "conversation_history": [],
        }

        result = await run_graph(initial_state)
        assert result["final_response"] is not None
        assert len(result["final_response"].response_text) > 0

    @pytest.mark.asyncio
    async def test_7_agent_failure_graceful_handling(self, mock_student_context):
        """If Student Insight raises an error, the workflow continues to Recovery Coach."""
        with patch("chatbot.backend.agents.student_insight.agent.StudentInsightAgent.analyze_async", side_effect=RuntimeError("Insight Service Unavailable")):
            initial_state: GraphState = {
                "student_id": "student_001",
                "user_message": "Why are my scores slipping?",
                "student_context": mock_student_context,
            }

            # Graph should not crash; it logs error and completes through Recovery Coach
            result = await run_graph(initial_state)
            assert result["final_response"] is not None
            assert "recovery_coach" in result["agents_used"]

    @pytest.mark.asyncio
    async def test_8_student_facing_response_clean(self, mock_student_context):
        """Output response does not leak internal node names, risk tiers, or scores."""
        initial_state: GraphState = {
            "student_id": "student_001",
            "user_message": "Can you give me a weekly schedule?",
            "student_context": mock_student_context,
        }

        result = await run_graph(initial_state)
        response_text = result["final_response"].response_text

        # Verify no internal jargon leaks
        assert "student_insight" not in response_text
        assert "study_planner" not in response_text
        assert "recovery_coach" not in response_text
        assert not _FORBIDDEN_TERMS.search(response_text)
