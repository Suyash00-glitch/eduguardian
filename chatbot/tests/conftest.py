"""
pytest configuration and shared fixtures for all chatbot tests.

Provides:
  - mock_llm_client: always returns a predictable response
  - mock_student_context: returns mock student data
  - test_client: FastAPI TestClient with mocked dependencies
  - test_db: in-memory async session (when needed)
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from chatbot.backend.llm.base import BaseLLMClient, LLMMessage, LLMResponse
from chatbot.backend.schemas.student import (
    AttendanceSummary,
    EngagementMetrics,
    RiskLevel,
    StudentContext,
    SubjectPerformance,
)
from chatbot.tests.fixtures.student_fixtures import get_mock_student_context


# ── Mock LLM Client ────────────────────────────────────────────────────────────

class FakeLLMClient(BaseLLMClient):
    """Always returns a fixed response — no network calls."""

    def __init__(self, response_text: str = "This is a test response from EduGuardian.") -> None:
        self._response = response_text

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        return LLMResponse(
            content=self._response,
            model="fake-llm",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    return FakeLLMClient()


@pytest.fixture
def fake_llm_json() -> FakeLLMClient:
    """Returns a valid InsightResponse JSON — for testing the insight agent."""
    json_response = """{
      "student_id": "student_001",
      "overall_summary": "Student shows mixed performance with notable strengths in OS.",
      "strengths": ["Operating Systems"],
      "focus_areas": ["Data Structures", "Mathematics III"],
      "subject_insights": [
        {
          "subject_name": "Data Structures",
          "status": "needs_attention",
          "key_observation": "Marks at 58%, assignment completion 65%",
          "recommended_action": "Increase weekly practice sessions"
        }
      ],
      "contributing_factors": ["Attendance declining in key subjects"],
      "recommended_areas_of_attention": ["Data Structures", "Mathematics III"],
      "support_intensity": "standard",
      "has_concerning_patterns": false
    }"""
    return FakeLLMClient(response_text=json_response)


@pytest.fixture
def fake_plan_json() -> FakeLLMClient:
    """Returns a valid PlanResponse JSON — for testing the study planner agent."""
    json_response = """{
      "title": "Your Personalised Study Plan",
      "week_start": "2024-11-11",
      "goals": ["Strengthen Data Structures", "Catch up on Mathematics III"],
      "tasks": [
        {
          "day": "Monday",
          "time_slot": "09:00-11:00",
          "subject": "Data Structures",
          "activity": "Review linked lists and trees",
          "duration_minutes": 120,
          "priority": "high"
        }
      ],
      "resources": ["CLRS textbook chapter 10"],
      "notes": "You got this! Small steps add up.",
      "rationale": "Prioritised weakest subjects first."
    }"""
    return FakeLLMClient(response_text=json_response)


# ── Mock student context ────────────────────────────────────────────────────────

@pytest.fixture
def mock_student() -> StudentContext:
    return get_mock_student_context("student_001")


@pytest.fixture
def mock_graph_state(mock_student):
    """A minimal GraphState for testing agents in isolation."""
    return {
        "student_id": "student_001",
        "user_message": "How can I improve my grades?",
        "conversation_id": None,
        "student_context": mock_student,
        "conversation_history": [],
        "insight_response": None,
        "plan_response": None,
        "final_response": None,
        "agents_used": [],
        "intent": "academic",
    }
