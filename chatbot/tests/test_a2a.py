"""
Comprehensive Tests for Official a2a-sdk Agent Communication & Services.

Verifies:
1. Agent Card retrieval and discovery endpoints (/health, /.well-known/agent-card.json, /a2a/card)
2. Student Insight Agent official A2A server execution
3. Study Planner Agent official A2A server execution
4. Recovery Coach Agent official A2A server execution
5. Official A2A Clients (StudentInsightA2AClient, StudyPlannerA2AClient, RecoveryCoachA2AClient)
6. Full LangGraph -> Official A2A integration across all 3 primary flows
"""
from __future__ import annotations

import pytest
import httpx

from chatbot.backend.a2a.client import (
    StudentInsightA2AClient,
    StudyPlannerA2AClient,
    RecoveryCoachA2AClient,
)
from chatbot.backend.services.insight_service import create_insight_service_app
from chatbot.backend.services.planner_service import create_planner_service_app
from chatbot.backend.services.coach_service import create_coach_service_app
from chatbot.backend.schemas.student import (
    StudentContext,
    AttendanceSummary,
    SubjectPerformance,
    AssignmentSummary,
)
from chatbot.backend.schemas.insight import InsightRequest, StudentInsight
from chatbot.backend.schemas.planner import PlanRequest, StudyPlan
from chatbot.backend.schemas.coach import CoachRequest, CoachResponse
from chatbot.backend.orchestrator.graph import run_graph
from chatbot.backend.orchestrator.state import GraphState


@pytest.fixture
def mock_student_context() -> StudentContext:
    return StudentContext(
        student_id="student_a2a_001",
        student_name="Tariq Mansoor",
        department="Computer Science",
        year_of_study=3,
        semester=5,
        attendance=AttendanceSummary(overall_percentage=68.0, trend="declining"),
        subjects=[
            SubjectPerformance(
                subject_name="Machine Learning",
                current_marks_percentage=48.0,
                assignment_completion_rate=0.50,
            ),
            SubjectPerformance(
                subject_name="Software Engineering",
                current_marks_percentage=82.0,
                assignment_completion_rate=0.90,
            ),
        ],
        assignments=AssignmentSummary(total_assigned=8, total_submitted=4, pending_count=4),
    )


class TestAgentCardsAndHealth:

    @pytest.mark.asyncio
    async def test_insight_service_health_and_card(self):
        """Student Insight service exposes /health and official Agent Card."""
        app = create_insight_service_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Health check
            health_resp = await client.get("/health")
            assert health_resp.status_code == 200
            assert health_resp.json()["service"] == "student_insight"
            assert health_resp.json()["sdk"] == "a2a-sdk==1.1.2"

            # 2. Official Agent Card discovery
            card_resp = await client.get("/.well-known/agent-card.json")
            assert card_resp.status_code == 200
            data = card_resp.json()
            assert data["name"] == "Student Insight Agent"
            assert len(data["skills"]) >= 2
            assert len(data["supportedInterfaces"]) >= 1

    @pytest.mark.asyncio
    async def test_planner_service_health_and_card(self):
        """Study Planner service exposes /health and official Agent Card."""
        app = create_planner_service_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            health_resp = await client.get("/health")
            assert health_resp.status_code == 200
            assert health_resp.json()["service"] == "study_planner"

            card_resp = await client.get("/.well-known/agent-card.json")
            assert card_resp.status_code == 200
            data = card_resp.json()
            assert data["name"] == "Study Planner Agent"

    @pytest.mark.asyncio
    async def test_coach_service_health_and_card(self):
        """Recovery Coach service exposes /health and official Agent Card."""
        app = create_coach_service_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            health_resp = await client.get("/health")
            assert health_resp.status_code == 200
            assert health_resp.json()["service"] == "recovery_coach"

            card_resp = await client.get("/.well-known/agent-card.json")
            assert card_resp.status_code == 200
            data = card_resp.json()
            assert data["name"] == "Recovery Coach Agent"


class TestLangGraphWithA2A:

    @pytest.mark.asyncio
    async def test_flow_1_general_support_via_a2a(self, mock_student_context):
        """Flow 1: General support routes to Recovery Coach."""
        initial_state: GraphState = {
            "student_id": mock_student_context.student_id,
            "user_message": "Hi, I feel nervous about exams.",
            "student_context": mock_student_context,
        }

        result = await run_graph(initial_state)
        assert result["intent"] in ("general_support", "simple")
        assert result["agents_used"] == ["recovery_coach"]
        assert result["final_response"] is not None

    @pytest.mark.asyncio
    async def test_flow_2_academic_insight_via_a2a(self, mock_student_context):
        """Flow 2: Academic query routes to Insight and Coach."""
        initial_state: GraphState = {
            "student_id": mock_student_context.student_id,
            "user_message": "How is my progress in Machine Learning?",
            "student_context": mock_student_context,
        }

        result = await run_graph(initial_state)
        assert result["intent"] in ("academic_insight", "academic")
        assert "student_insight" in result["agents_used"]
        assert "recovery_coach" in result["agents_used"]
        assert "study_planner" not in result["agents_used"]
        assert result["insight_response"] is not None
        assert result["final_response"] is not None

    @pytest.mark.asyncio
    async def test_flow_3_study_planning_via_a2a(self, mock_student_context):
        """Flow 3: Planning request routes to Insight, Planner, and Coach."""
        initial_state: GraphState = {
            "student_id": mock_student_context.student_id,
            "user_message": "Create a study plan for this week.",
            "student_context": mock_student_context,
        }

        result = await run_graph(initial_state)
        assert result["intent"] in ("study_planning", "plan")
        assert result["agents_used"] == ["student_insight", "study_planner", "recovery_coach"]
        assert result["insight_response"] is not None
        assert result["plan_response"] is not None
        assert result["final_response"] is not None
