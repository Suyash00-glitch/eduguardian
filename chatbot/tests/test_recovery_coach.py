"""
Unit tests for the Recovery Coach Agent.

Tests cover:
1. Simple conversational messages (stress, motivation, greetings)
2. Personalized responses using StudentContext
3. Internal guidance application using StudentInsight
4. Natural presentation of structured StudyPlan
5. Missing context handling (graceful transparency, no hallucinations)
6. Conversation history awareness
7. Safety and product behavior (no forbidden risk terms)
8. Fallback handling on LLM failures
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from chatbot.backend.agents.recovery_coach.agent import RecoveryCoachAgent, _FORBIDDEN_TERMS_PATTERN
from chatbot.backend.schemas.coach import CoachRequest, CoachResponse, CoachMessageItem
from chatbot.backend.schemas.student import (
    AttendanceSummary,
    StudentContext,
    SubjectPerformance,
    AssignmentSummary,
)
from chatbot.backend.schemas.insight import StudentInsight, SubjectInsight
from chatbot.backend.schemas.planner import StudyPlan, StudyTask, PriorityLevel


# ── Fixtures & Mock LLMs ──────────────────────────────────────────────────────

class FakeEchoLLM:
    """Mock LLM that returns customizable response or canned supportive replies."""
    def __init__(self, canned_response: str | None = None) -> None:
        self.canned_response = canned_response
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None

    async def complete_simple(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        if self.canned_response:
            return self.canned_response
        return (
            "Hey! I hear you, and it's completely normal to feel this way. "
            "Let's break things down together into small, achievable steps. "
            "What's one thing we can tackle first today?"
        )


class FailingLLM:
    """Mock LLM that raises an error to test fallback behavior."""
    async def complete_simple(self, *args, **kwargs) -> str:
        raise ConnectionError("Simulated LLM Gateway Timeout")


# ── Test Suite ────────────────────────────────────────────────────────────────

class TestRecoveryCoachAgent:

    @pytest.mark.asyncio
    async def test_1_simple_conversation_stressed(self):
        """Simple conversation message returns a warm, supportive response with no risk labels."""
        fake_llm = FakeEchoLLM()
        agent = RecoveryCoachAgent(llm_client=fake_llm)

        req = CoachRequest(
            student_id="student_001",
            user_message="I'm feeling stressed about my upcoming classes.",
        )

        response = await agent.recover(req)

        assert isinstance(response, CoachResponse)
        assert len(response.response_text) > 0
        assert response.has_study_plan is False
        assert response.study_plan is None
        # Safety check: no forbidden terms in output
        assert not _FORBIDDEN_TERMS_PATTERN.search(response.response_text)

    @pytest.mark.asyncio
    async def test_2_personalized_response_with_student_context(self):
        """Agent builds prompt embedding academic context and addresses student by name."""
        fake_llm = FakeEchoLLM(
            canned_response=(
                "Hi Aisha! Great to talk with you. I see you're doing well in Operating Systems! "
                "Let's put a little extra focus into Data Structures this week."
            )
        )
        agent = RecoveryCoachAgent(llm_client=fake_llm)

        ctx = StudentContext(
            student_id="student_001",
            student_name="Aisha Patel",
            attendance=AttendanceSummary(overall_percentage=75.0, trend="declining"),
            subjects=[
                SubjectPerformance(subject_name="Data Structures", current_marks_percentage=55.0),
                SubjectPerformance(subject_name="Operating Systems", current_marks_percentage=85.0),
            ],
            assignments=AssignmentSummary(total_assigned=8, total_submitted=5, pending_count=3),
        )

        req = CoachRequest(
            student_id="student_001",
            user_message="How can I improve my studies?",
            student_context=ctx,
        )

        response = await agent.recover(req)

        # Verify context was formatted into the prompt
        assert "Aisha" in fake_llm.last_user_prompt
        assert "Data Structures" in fake_llm.last_user_prompt
        assert "Operating Systems" in fake_llm.last_user_prompt
        assert "75.0%" in fake_llm.last_user_prompt

        # Verify response
        assert "Aisha" in response.response_text
        assert not _FORBIDDEN_TERMS_PATTERN.search(response.response_text)

    @pytest.mark.asyncio
    async def test_3_student_insight_usage(self):
        """StudentInsight provides internal guidance without exposing internal jargon."""
        fake_llm = FakeEchoLLM(
            canned_response=(
                "You have a great foundation in OS! Let's schedule two focused practice blocks "
                "on Tree Traversals this week to build your confidence in Data Structures."
            )
        )
        agent = RecoveryCoachAgent(llm_client=fake_llm)

        insight = StudentInsight(
            student_id="student_001",
            overall_summary="Solid OS performance; tree algorithms require practice in DS.",
            strengths=["Operating Systems"],
            focus_areas=["Data Structures"],
            subject_insights=[
                SubjectInsight(
                    subject_name="Data Structures",
                    status="needs_focus",
                    key_observation="Lab submission rate is 65%",
                    recommended_action="Two 60-min practice blocks on Trees",
                )
            ],
            recommended_areas_of_attention=["Tree algorithms", "Graph traversals"],
            support_intensity="intensive",
            has_concerning_patterns=True,
        )

        req = CoachRequest(
            student_id="student_001",
            user_message="What should I work on today?",
            student_insight=insight,
        )

        response = await agent.recover(req)

        # Verify prompt received insight guidance (injected because 'what should I work on today?' is academic)
        assert "Operating Systems" in fake_llm.last_user_prompt
        assert "Data Structures" in fake_llm.last_user_prompt
        # Intensive mode system prompt selected
        assert "ADDITIONAL GUIDANCE" in fake_llm.last_system_prompt

        # Verify response text is clean and supportive
        assert not _FORBIDDEN_TERMS_PATTERN.search(response.response_text)

    @pytest.mark.asyncio
    async def test_4_study_plan_presentation(self):
        """When a StudyPlan is attached, the response attaches it and prompts its review."""
        fake_llm = FakeEchoLLM(
            canned_response=(
                "I've put together a personalized study plan for you this week! "
                "We'll start with Data Structures on Monday and keep our daily blocks manageable."
            )
        )
        agent = RecoveryCoachAgent(llm_client=fake_llm)

        plan = StudyPlan(
            title="Weekly Recovery Schedule",
            goals=["Complete Tree Practice", "Review OS Paging"],
            priorities=["Data Structures"],
            tasks=[
                StudyTask(
                    title="Tree Traversal Practice",
                    description="Implement traversals",
                    subject="Data Structures",
                    day="Monday",
                    duration_minutes=90,
                    priority=PriorityLevel.HIGH,
                )
            ],
            resources=["Visualgo.net"],
        )

        req = CoachRequest(
            student_id="student_001",
            user_message="Can you give me a schedule for this week?",
            study_plan=plan,
        )

        response = await agent.recover(req)

        assert response.has_study_plan is True
        assert response.study_plan == plan
        assert "Weekly Recovery Schedule" in fake_llm.last_user_prompt
        assert len(response.resources) == 1

    @pytest.mark.asyncio
    async def test_5_missing_context_handling(self):
        """Minimal request without context generates graceful prompt without hallucinating."""
        fake_llm = FakeEchoLLM(
            canned_response="Hello! I'm here to help you with your studies. What would you like to work on?"
        )
        agent = RecoveryCoachAgent(llm_client=fake_llm)

        req = CoachRequest(
            student_id="student_001",
            user_message="Hello",
            student_context=None,
            student_insight=None,
            study_plan=None,
        )

        response = await agent.recover(req)

        assert "Not injected for this request type" in fake_llm.last_user_prompt
        assert response.response_text is not None
        assert response.has_study_plan is False

    @pytest.mark.asyncio
    async def test_6_conversation_history_awareness(self):
        """Recent conversation history turns are passed into the prompt context."""
        fake_llm = FakeEchoLLM()
        agent = RecoveryCoachAgent(llm_client=fake_llm)

        history = [
            CoachMessageItem(role="user", content="I struggled with my math quiz yesterday."),
            CoachMessageItem(role="assistant", content="That's okay, quizzes are learning checkpoints."),
        ]

        req = CoachRequest(
            student_id="student_001",
            user_message="Can we practice calculus formulas today?",
            conversation_history=history,
        )

        await agent.recover(req)

        assert "Student: I struggled with my math quiz yesterday." in fake_llm.last_user_prompt
        assert "EduGuardian: That's okay" in fake_llm.last_user_prompt

    @pytest.mark.asyncio
    async def test_7_forbidden_terms_sanitizer(self):
        """Safety post-processor intercepts and scrubs forbidden labels if produced by model."""
        # Simulated rogue LLM output containing forbidden label
        rogue_llm = FakeEchoLLM(
            canned_response="As an at-risk student, you should study hard because you are a weak student."
        )
        agent = RecoveryCoachAgent(llm_client=rogue_llm)

        req = CoachRequest(
            student_id="student_001",
            user_message="How am I doing?",
        )

        response = await agent.recover(req)

        # Verify forbidden terms were sanitized
        assert "at-risk" not in response.response_text
        assert "weak student" not in response.response_text
        assert not _FORBIDDEN_TERMS_PATTERN.search(response.response_text)

    @pytest.mark.asyncio
    async def test_8_llm_failure_fallback(self):
        """When LLM raises an error, agent returns a friendly, reassuring fallback response."""
        failing_llm = FailingLLM()
        agent = RecoveryCoachAgent(llm_client=failing_llm)

        req = CoachRequest(
            student_id="student_001",
            user_message="Hello!",
        )

        response = await agent.recover(req)

        assert isinstance(response, CoachResponse)
        assert len(response.response_text) > 0
        assert "help you" in response.response_text or "support" in response.response_text
        assert response.metadata.get("is_fallback") is True
