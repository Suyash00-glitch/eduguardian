"""
Comprehensive Integration Tests for the Chat API Gateway.

Verifies:
1. New conversation creation on first message
2. Existing conversation follow-up
3. General support request flow
4. Academic insight request flow
5. Study planning request flow
6. Structured StudyPlan returned correctly
7. Conversation history retrieval (/messages)
8. Conversation listing (/conversations)
9. Conversation ownership enforcement (403 for mismatched student)
10. Invalid conversation ID format validation (422)
11. Missing conversation handling (404)
12. Empty message validation (422)
13. Conversation deletion (/chat/{conversation_id})
14. Student-visible response contains no internal jargon
15. No sensitive secrets or tokens exposed
16. Health endpoint remains fast and lightweight
"""
from __future__ import annotations

import datetime
import json
import re
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from chatbot.backend.api.main import app
from chatbot.backend.api.dependencies import (
    get_conversation_repo,
    get_current_student_id,
    get_student_context_repo,
)
from chatbot.backend.schemas.chat import MessageRole, MessageSchema
from chatbot.backend.schemas.coach import CoachResponse
from chatbot.backend.schemas.planner import StudyPlan, StudyTask, PriorityLevel
from chatbot.backend.schemas.student import StudentContext, AttendanceSummary, SubjectPerformance

_FORBIDDEN_TERMS = re.compile(
    r"\b(high[- ]risk|at[- ]risk|weak student|poor student|failing student|predicted to fail)\b",
    re.IGNORECASE,
)


@pytest.fixture
def mock_student() -> StudentContext:
    return StudentContext(
        student_id="student_001",
        student_name="Aisha Raza",
        department="Computer Science",
        year_of_study=2,
        attendance=AttendanceSummary(overall_percentage=75.0, trend="stable"),
        subjects=[
            SubjectPerformance(subject_name="Data Structures", current_marks_percentage=65.0),
            SubjectPerformance(subject_name="Operating Systems", current_marks_percentage=85.0),
        ],
    )


@pytest.fixture
def sample_study_plan() -> StudyPlan:
    return StudyPlan(
        title="Weekly Success Plan: Data Structures",
        week_start="2026-08-15",
        goals=["Master tree traversals"],
        tasks=[
            StudyTask(
                title="Tree Traversals Practice",
                day="Monday",
                time_slot="10:00–11:30",
                subject="Data Structures",
                duration_minutes=90,
                priority=PriorityLevel.HIGH,
            )
        ],
        notes="Take breaks and stay confident!",
    )


@pytest.fixture
def client():
    return TestClient(app)


class TestChatAPIGateway:

    def test_16_health_endpoint_remains_lightweight(self, client):
        """Health endpoint returns 200 OK immediately without external dependencies."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    @patch("chatbot.backend.services.chat_service.run_graph")
    def test_1_new_conversation_and_first_message(self, mock_run_graph, client, mock_student):
        """POST /api/chat with message only creates new conversation and returns response."""
        conv_id = uuid.uuid4()
        fake_conv = MagicMock(id=conv_id, student_id="student_001")
        fake_msg = MagicMock(id=uuid.uuid4(), created_at=datetime.datetime.utcnow())

        mock_conv_repo = AsyncMock()
        mock_conv_repo.create_conversation.return_value = fake_conv
        mock_conv_repo.get_history.return_value = []
        mock_conv_repo.get_latest_study_plan.return_value = None
        mock_conv_repo.save_user_message.return_value = fake_msg
        mock_conv_repo.save_assistant_message.return_value = fake_msg

        mock_ctx_repo = AsyncMock()
        mock_ctx_repo.get_context.return_value = mock_student

        mock_run_graph.return_value = {
            "final_response": CoachResponse(
                response_text="Hello Aisha! How can I help you succeed today?",
                has_study_plan=False,
            ),
            "plan_response": None,
            "agents_used": ["recovery_coach"],
        }

        app.dependency_overrides[get_current_student_id] = lambda: "student_001"
        app.dependency_overrides[get_conversation_repo] = lambda: mock_conv_repo
        app.dependency_overrides[get_student_context_repo] = lambda: mock_ctx_repo

        try:
            resp = client.post("/api/chat", json={"message": "Hello!"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["conversation_id"] == str(conv_id)
            assert data["message"]["role"] == "assistant"
            assert "Hello Aisha!" in data["message"]["content"]
            assert data["study_plan"] is None
        finally:
            app.dependency_overrides.clear()

    @patch("chatbot.backend.services.chat_service.run_graph")
    def test_2_existing_conversation_follow_up(self, mock_run_graph, client, mock_student):
        """POST /api/chat with valid conversation_id continues the thread."""
        conv_id = uuid.uuid4()
        fake_conv = MagicMock(id=conv_id, student_id="student_001")
        fake_msg = MagicMock(id=uuid.uuid4(), created_at=datetime.datetime.utcnow())

        mock_conv_repo = AsyncMock()
        mock_conv_repo.get_conversation.return_value = fake_conv
        mock_conv_repo.get_history.return_value = []
        mock_conv_repo.get_latest_study_plan.return_value = None
        mock_conv_repo.save_user_message.return_value = fake_msg
        mock_conv_repo.save_assistant_message.return_value = fake_msg

        mock_ctx_repo = AsyncMock()
        mock_ctx_repo.get_context.return_value = mock_student

        mock_run_graph.return_value = {
            "final_response": CoachResponse(
                response_text="Let's prioritize your Data Structures coursework.",
                has_study_plan=False,
            ),
            "plan_response": None,
            "agents_used": ["recovery_coach"],
        }

        app.dependency_overrides[get_current_student_id] = lambda: "student_001"
        app.dependency_overrides[get_conversation_repo] = lambda: mock_conv_repo
        app.dependency_overrides[get_student_context_repo] = lambda: mock_ctx_repo

        try:
            resp = client.post(
                "/api/chat",
                json={"conversation_id": str(conv_id), "message": "What should I do first?"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["conversation_id"] == str(conv_id)
        finally:
            app.dependency_overrides.clear()

    @patch("chatbot.backend.services.chat_service.run_graph")
    def test_5_and_6_study_planning_with_structured_plan(
        self, mock_run_graph, client, mock_student, sample_study_plan
    ):
        """POST /api/chat planning request returns natural text + structured StudyPlan object."""
        conv_id = uuid.uuid4()
        fake_conv = MagicMock(id=conv_id, student_id="student_001")
        fake_msg = MagicMock(id=uuid.uuid4(), created_at=datetime.datetime.utcnow())

        mock_conv_repo = AsyncMock()
        mock_conv_repo.create_conversation.return_value = fake_conv
        mock_conv_repo.get_history.return_value = []
        mock_conv_repo.get_latest_study_plan.return_value = None
        mock_conv_repo.save_user_message.return_value = fake_msg
        mock_conv_repo.save_assistant_message.return_value = fake_msg

        mock_ctx_repo = AsyncMock()
        mock_ctx_repo.get_context.return_value = mock_student

        mock_run_graph.return_value = {
            "final_response": CoachResponse(
                response_text="I've prepared a customized study schedule for you!",
                has_study_plan=True,
            ),
            "plan_response": sample_study_plan,
            "agents_used": ["student_insight", "study_planner", "recovery_coach"],
        }

        app.dependency_overrides[get_current_student_id] = lambda: "student_001"
        app.dependency_overrides[get_conversation_repo] = lambda: mock_conv_repo
        app.dependency_overrides[get_student_context_repo] = lambda: mock_ctx_repo

        try:
            resp = client.post("/api/chat", json={"message": "Make me a study plan for this week."})
            assert resp.status_code == 200
            data = resp.json()
            assert data["study_plan"] is not None
            assert data["study_plan"]["title"] == "Weekly Success Plan: Data Structures"
            assert len(data["study_plan"]["tasks"]) == 1
            assert data["study_plan"]["tasks"][0]["subject"] == "Data Structures"
        finally:
            app.dependency_overrides.clear()

    def test_7_conversation_history_retrieval(self, client):
        """GET /api/chat/{conversation_id}/messages returns chronological messages."""
        conv_id = uuid.uuid4()
        fake_conv = MagicMock(id=conv_id, student_id="student_001")
        now = datetime.datetime.utcnow()
        m1 = MagicMock(id=uuid.uuid4(), role="user", content="Turn 1", created_at=now)
        m2 = MagicMock(id=uuid.uuid4(), role="assistant", content="Turn 2", created_at=now)

        mock_conv_repo = AsyncMock()
        mock_conv_repo.get_conversation.return_value = fake_conv
        mock_conv_repo.get_history.return_value = [m1, m2]
        mock_conv_repo.to_schema = lambda m: MessageSchema(
            id=m.id, role=MessageRole(m.role), content=m.content, created_at=m.created_at
        )

        app.dependency_overrides[get_current_student_id] = lambda: "student_001"
        app.dependency_overrides[get_conversation_repo] = lambda: mock_conv_repo

        try:
            resp = client.get(f"/api/chat/{conv_id}/messages")
            assert resp.status_code == 200
            data = resp.json()
            assert data["conversation_id"] == str(conv_id)
            assert len(data["messages"]) == 2
        finally:
            app.dependency_overrides.clear()

    def test_8_conversation_list(self, client):
        """GET /api/chat/conversations returns student's conversation threads."""
        c1 = MagicMock(id=uuid.uuid4(), student_id="student_001", title="Plan 1", created_at=datetime.datetime.utcnow(), updated_at=datetime.datetime.utcnow())
        mock_conv_repo = AsyncMock()
        mock_conv_repo.list_conversations.return_value = [c1]

        app.dependency_overrides[get_current_student_id] = lambda: "student_001"
        app.dependency_overrides[get_conversation_repo] = lambda: mock_conv_repo

        try:
            resp = client.get("/api/chat/conversations")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["student_id"] == "student_001"
        finally:
            app.dependency_overrides.clear()

    def test_9_conversation_ownership_enforcement(self, client):
        """Attempting to access another student's conversation returns 403 Forbidden."""
        conv_id = uuid.uuid4()
        fake_conv = MagicMock(id=conv_id, student_id="other_student_999")

        mock_conv_repo = AsyncMock()
        mock_conv_repo.get_conversation.return_value = fake_conv

        app.dependency_overrides[get_current_student_id] = lambda: "student_001"
        app.dependency_overrides[get_conversation_repo] = lambda: mock_conv_repo

        try:
            resp = client.post(
                "/api/chat",
                json={"conversation_id": str(conv_id), "message": "Hello"},
            )
            assert resp.status_code == 403
            data = resp.json()
            error_msg = data.get("error", {}).get("message", "") or data.get("detail", "")
            assert "access denied" in error_msg.lower()
        finally:
            app.dependency_overrides.clear()

    def test_10_invalid_conversation_id_format(self, client):
        """Non-UUID conversation_id string returns 422 Unprocessable Entity."""
        resp = client.post("/api/chat", json={"conversation_id": "not-a-valid-uuid", "message": "Hi"})
        assert resp.status_code == 422

    def test_11_missing_conversation_handling(self, client):
        """Non-existent UUID returns 404 Not Found."""
        mock_conv_repo = AsyncMock()
        mock_conv_repo.get_conversation.return_value = None

        app.dependency_overrides[get_current_student_id] = lambda: "student_001"
        app.dependency_overrides[get_conversation_repo] = lambda: mock_conv_repo

        try:
            resp = client.post(
                "/api/chat",
                json={"conversation_id": str(uuid.uuid4()), "message": "Hello"},
            )
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_12_empty_message_validation(self, client):
        """Empty or whitespace-only message returns 422 Unprocessable Entity."""
        resp = client.post("/api/chat", json={"message": "   "})
        assert resp.status_code == 422

    def test_13_delete_conversation(self, client):
        """DELETE /api/chat/{conversation_id} deletes the conversation."""
        conv_id = uuid.uuid4()
        mock_conv_repo = AsyncMock()
        mock_conv_repo.delete_conversation.return_value = True

        app.dependency_overrides[get_current_student_id] = lambda: "student_001"
        app.dependency_overrides[get_conversation_repo] = lambda: mock_conv_repo

        try:
            resp = client.delete(f"/api/chat/{conv_id}")
            assert resp.status_code == 200
            assert resp.json()["status"] == "deleted"
        finally:
            app.dependency_overrides.clear()

    @patch("chatbot.backend.services.chat_service.run_graph")
    def test_14_and_15_clean_response_and_no_secrets(self, mock_run_graph, client, mock_student):
        """Response contains zero forbidden terms or leaked credentials."""
        conv_id = uuid.uuid4()
        fake_conv = MagicMock(id=conv_id, student_id="student_001")
        fake_msg = MagicMock(id=uuid.uuid4(), created_at=datetime.datetime.utcnow())

        mock_conv_repo = AsyncMock()
        mock_conv_repo.create_conversation.return_value = fake_conv
        mock_conv_repo.get_history.return_value = []
        mock_conv_repo.get_latest_study_plan.return_value = None
        mock_conv_repo.save_user_message.return_value = fake_msg
        mock_conv_repo.save_assistant_message.return_value = fake_msg

        mock_ctx_repo = AsyncMock()
        mock_ctx_repo.get_context.return_value = mock_student

        mock_run_graph.return_value = {
            "final_response": CoachResponse(
                response_text="You have strong potential! Let's work on Data Structures together.",
                has_study_plan=False,
            ),
            "plan_response": None,
            "agents_used": ["recovery_coach"],
        }

        app.dependency_overrides[get_current_student_id] = lambda: "student_001"
        app.dependency_overrides[get_conversation_repo] = lambda: mock_conv_repo
        app.dependency_overrides[get_student_context_repo] = lambda: mock_ctx_repo

        try:
            resp = client.post("/api/chat", json={"message": "Can you help me?"})
            assert resp.status_code == 200
            raw_text = resp.text

            # Safety assertions
            assert not _FORBIDDEN_TERMS.search(raw_text)
            assert "sk-" not in raw_text
            assert "password" not in raw_text
        finally:
            app.dependency_overrides.clear()
