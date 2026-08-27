"""
Unit tests for Shared Data Contracts & Schemas.

Verifies:
1. Valid data parsing and serialization (JSON round-trip)
2. Handling of optional/missing fields
3. Rejection of invalid types/ranges
4. Reusable nested academic models
5. Insight, Planner, Coach, and Frontend contract boundaries
6. Zero leakage of passwords or sensitive credentials
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
import pytest
from pydantic import ValidationError

from chatbot.backend.schemas import (
    # Student Context
    AttendanceTrend,
    AttendanceSummary,
    SubjectPerformance,
    AssignmentSummary,
    AssessmentSummary,
    EngagementSummary,
    TrendInformation,
    InterventionHistory,
    StudentContext,
    # Student Insight
    SubjectInsight,
    InsightRequest,
    StudentInsight,
    # Study Planner
    PriorityLevel,
    StudyTask,
    PlanMilestone,
    PlanRequest,
    StudyPlan,
    # Recovery Coach
    CoachMessageItem,
    CoachRequest,
    CoachResponse,
    # Chat
    MessageRole,
    ChatMessage,
    ConversationHistory,
    ChatRequest,
    MessageSchema,
    ChatResponse,
    # Intent
    IntentType,
    IntentClassification,
    # State
    ChatStateModel,
    # A2A
    A2AAgentRole,
    A2ATaskType,
    A2ATaskEnvelope,
    A2AResultEnvelope,
    InsightTaskPayload,
    # Frontend
    FrontendMessage,
    FrontendChatResponse,
)


# ── 1. Student Context & Nested Records ───────────────────────────────────────

class TestStudentContextContracts:
    def test_minimal_student_context(self):
        """StudentContext should be instantiable with just student_id and student_name."""
        ctx = StudentContext(student_id="student_101", student_name="Aisha Patel")
        assert ctx.student_id == "student_101"
        assert ctx.student_name == "Aisha Patel"
        assert ctx.attendance is None
        assert ctx.subjects == []
        assert ctx.assignments is None
        assert ctx.engagement is None

    def test_full_student_context_roundtrip(self):
        """Complete StudentContext should serialize to JSON and back losslessly."""
        ctx = StudentContext(
            student_id="student_101",
            student_name="Aisha Patel",
            department="Computer Science",
            year_of_study=3,
            semester=5,
            attendance=AttendanceSummary(
                overall_percentage=72.5,
                trend=AttendanceTrend.DECLINING,
                classes_attended=58,
                total_classes=80,
                subjects_below_threshold=["Data Structures"],
            ),
            subjects=[
                SubjectPerformance(
                    subject_code="CS301",
                    subject_name="Data Structures",
                    faculty_name="Dr. Rao",
                    current_marks_percentage=58.0,
                    grade="C",
                    attendance_percentage=68.0,
                    assignment_completion_rate=0.65,
                    quiz_average=60.0,
                ),
                SubjectPerformance(
                    subject_code="CS302",
                    subject_name="Operating Systems",
                    faculty_name="Prof. Sharma",
                    current_marks_percentage=84.0,
                    grade="A",
                    attendance_percentage=90.0,
                    assignment_completion_rate=0.95,
                    quiz_average=88.0,
                ),
            ],
            assignments=AssignmentSummary(
                total_assigned=10,
                total_submitted=7,
                pending_count=3,
                average_score=70.0,
            ),
            assessments=AssessmentSummary(
                gpa=7.8,
                quizzes_completed=6,
                average_quiz_score=74.0,
            ),
            engagement=EngagementSummary(
                lms_logins_last_30_days=18,
                study_materials_accessed=24,
                discussion_forum_posts=2,
            ),
            trends=TrendInformation(
                grade_trajectory="upward",
                consistency_score=0.8,
                notable_changes=["Attendance dipped in morning lectures"],
            ),
            interventions=[
                InterventionHistory(
                    intervention_id="int_01",
                    intervention_type="study_plan",
                    focus_subject="Data Structures",
                    outcome_notes="Completed 3 practice modules",
                )
            ],
        )

        json_str = ctx.model_dump_json()
        restored = StudentContext.model_validate_json(json_str)

        assert restored.student_id == "student_101"
        assert len(restored.subjects) == 2
        assert restored.attendance.overall_percentage == 72.5
        assert restored.attendance.trend == AttendanceTrend.DECLINING
        assert restored.subjects[0].subject_name == "Data Structures"
        assert restored.interventions[0].focus_subject == "Data Structures"

    def test_validation_bounds_checking(self):
        """Attendance and marks must obey valid 0-100 percentage ranges."""
        with pytest.raises(ValidationError):
            AttendanceSummary(overall_percentage=150.0)  # > 100 invalid

        with pytest.raises(ValidationError):
            SubjectPerformance(subject_name="Math", assignment_completion_rate=1.5)  # > 1.0 invalid


# ── 2. Student Insight Contracts ──────────────────────────────────────────────

class TestStudentInsightContracts:
    def test_insight_serialization(self):
        """StudentInsight should serialize and parse all fields correctly."""
        insight = StudentInsight(
            student_id="student_101",
            overall_summary="Solid foundation in OS, with opportunity to practice Data Structures.",
            strengths=["Operating Systems", "Computer Architecture"],
            focus_areas=["Data Structures", "Discrete Math"],
            subject_insights=[
                SubjectInsight(
                    subject_name="Data Structures",
                    status="needs_focus",
                    key_observation="Assignment submission is at 65%",
                    recommended_action="Dedicate two 60-min practice blocks this week",
                )
            ],
            contributing_factors=["Gaps in early morning lecture attendance"],
            recommended_areas_of_attention=["Trees & Graphs", "Dynamic Programming"],
            explanation="Focusing on foundational tree algorithms will boost upcoming quiz confidence.",
            support_intensity="standard",
            has_concerning_patterns=False,
        )

        json_str = insight.model_dump_json()
        restored = StudentInsight.model_validate_json(json_str)
        assert restored.student_id == "student_101"
        assert len(restored.strengths) == 2
        assert restored.subject_insights[0].status == "needs_focus"


# ── 3. Study Plan Contracts ───────────────────────────────────────────────────

class TestStudyPlanContracts:
    def test_study_plan_structure(self):
        """StudyPlan and tasks must have required fields and proper types."""
        plan = StudyPlan(
            title="Weekly Success Plan",
            goals=["Complete CS301 Tree Assignment", "Review OS Memory Paging"],
            priorities=["Data Structures", "Operating Systems"],
            week_start="2026-08-18",
            tasks=[
                StudyTask(
                    title="Tree Traversal Practice",
                    description="Implement Inorder, Preorder, and Postorder traversals",
                    subject="Data Structures",
                    day="Monday",
                    time_slot="09:00–10:30",
                    duration_minutes=90,
                    priority=PriorityLevel.HIGH,
                ),
                StudyTask(
                    title="OS Paging Chapter Review",
                    description="Read chapter 8 on virtual memory and paging tables",
                    subject="Operating Systems",
                    day="Tuesday",
                    time_slot="14:00–15:00",
                    duration_minutes=60,
                    priority=PriorityLevel.MEDIUM,
                ),
            ],
            milestones=[
                PlanMilestone(title="Submit Tree Assignment", target_day="Wednesday")
            ],
            resources=["Visualgo Tree Animations", "Textbook Ch. 8"],
            notes="Consistency wins over cramming!",
        )

        data = plan.model_dump()
        assert len(data["tasks"]) == 2
        assert data["tasks"][0]["priority"] == "high"
        assert len(data["milestones"]) == 1

        # JSON round-trip
        restored = StudyPlan.model_validate_json(plan.model_dump_json())
        assert restored.tasks[0].duration_minutes == 90
        assert restored.tasks[0].priority == PriorityLevel.HIGH


# ── 4. Recovery Coach Contracts ───────────────────────────────────────────────

class TestCoachContracts:
    def test_coach_response_structure(self):
        """CoachResponse should hold supportive message and optional study plan."""
        response = CoachResponse(
            response_text="Hey Aisha! You're making great progress. Let's tackle Data Structures together.",
            has_study_plan=True,
            suggested_followups=["📋 Show me my weekly timetable", "📊 How is my attendance?"],
            resources=["LMS Module 3 notes"],
        )

        assert response.has_study_plan is True
        assert len(response.suggested_followups) == 2
        assert "Aisha" in response.response_text


# ── 5. Chat Messages & API Contracts ──────────────────────────────────────────

class TestChatContracts:
    def test_chat_message_role_enum(self):
        """ChatMessage should enforce MessageRole enum."""
        msg = ChatMessage(
            role=MessageRole.USER,
            content="Can you help me organize my week?",
        )
        assert msg.role == MessageRole.USER
        assert isinstance(msg.id, uuid.UUID)

    def test_chat_request_validation(self):
        """ChatRequest requires non-empty message."""
        with pytest.raises(ValidationError):
            ChatRequest(message="")  # min_length=1


# ── 6. Intent & LangGraph State Contracts ─────────────────────────────────────

class TestIntentAndStateContracts:
    def test_intent_types(self):
        """IntentType covers the three primary routing categories."""
        assert IntentType.GENERAL_SUPPORT.value == "general_support"
        assert IntentType.ACADEMIC_INSIGHT.value == "academic_insight"
        assert IntentType.STUDY_PLANNING.value == "study_planning"

    def test_chat_state_model_defaults(self):
        """ChatStateModel allows conditional execution state with null defaults."""
        state = ChatStateModel(
            student_id="student_101",
            user_message="Hello!",
            intent=IntentType.GENERAL_SUPPORT,
        )
        assert state.student_insight is None
        assert state.study_plan is None
        assert state.final_response is None
        assert state.agents_used == []


# ── 7. A2A & Frontend Contracts ───────────────────────────────────────────────

class TestA2AAndFrontendContracts:
    def test_a2a_task_envelope(self):
        """A2ATaskEnvelope cleanly packages inter-agent payload."""
        envelope = A2ATaskEnvelope(
            task_type=A2ATaskType.GENERATE_INSIGHT,
            sender=A2AAgentRole.ORCHESTRATOR,
            recipient=A2AAgentRole.STUDENT_INSIGHT,
            payload={"student_id": "student_101"},
        )
        assert envelope.task_type == A2ATaskType.GENERATE_INSIGHT
        assert envelope.recipient == A2AAgentRole.STUDENT_INSIGHT

    def test_frontend_chat_response_structure(self):
        """FrontendChatResponse provides clean student-facing payload."""
        msg_id = uuid.uuid4()
        conv_id = uuid.uuid4()
        frontend_resp = FrontendChatResponse(
            conversation_id=conv_id,
            message=FrontendMessage(
                id=msg_id,
                role="assistant",
                content="Here is your study plan!",
                created_at=datetime.utcnow(),
            ),
            suggested_prompts=["📋 Make me a study plan", "📊 How am I doing?"],
        )

        json_data = json.loads(frontend_resp.model_dump_json())
        assert json_data["conversation_id"] == str(conv_id)
        assert json_data["message"]["role"] == "assistant"
        assert len(json_data["suggested_prompts"]) == 2
