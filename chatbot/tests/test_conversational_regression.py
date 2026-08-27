"""
Conversational Behavior & Directness Regression Test Suite.
Verifies all 10 user requirements for concise direct answers, format overrides,
no psychological projection, and conditional academic personalization.
"""
import pytest
from chatbot.backend.agents.recovery_coach.agent import RecoveryCoachAgent
from chatbot.backend.agents.recovery_coach.prompts import (
    build_recovery_coach_user_prompt,
    _detect_format_modifier,
    _detect_identity_request,
    _detect_math_or_simple_qa,
    _detect_academic_focus_request,
    _detect_progress_request,
    _detect_explicit_data_request,
    _detect_emotional_message,
    _detect_complex_detailed_request,
)
from chatbot.backend.schemas.coach import CoachRequest, CoachMessageItem
from chatbot.backend.schemas.student import (
    StudentContext,
    AttendanceSummary,
    SubjectPerformance,
    AssignmentSummary,
)
from chatbot.backend.schemas.insight import StudentInsight
from chatbot.backend.schemas.planner import StudyPlan, StudyTask, PriorityLevel


class FakeEchoLLM:
    def __init__(self, response_map: dict[str, str] = None):
        self.response_map = response_map or {}
        self.last_system_prompt = ""
        self.last_user_prompt = ""

    async def complete_simple(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        for k, v in self.response_map.items():
            if k in user_prompt:
                return v
        return "Default echo response"


@pytest.fixture
def sample_context():
    return StudentContext(
        student_id="student_001",
        student_name="Ajmal",
        attendance=AttendanceSummary(overall_percentage=67.0, trend="declining"),
        subjects=[
            SubjectPerformance(subject_name="Data Structures", current_marks_percentage=48.0),
            SubjectPerformance(subject_name="DBMS", current_marks_percentage=51.0),
            SubjectPerformance(subject_name="Operating Systems", current_marks_percentage=72.0),
        ],
        assignments=AssignmentSummary(total_assigned=10, total_submitted=6, pending_count=4),
    )


@pytest.fixture
def sample_insight():
    return StudentInsight(
        student_id="student_001",
        overall_summary="Operating Systems is solid; Data Structures and DBMS need focus.",
        strengths=["Operating Systems"],
        focus_areas=["Data Structures", "DBMS"],
        recommended_areas_of_attention=["Trees", "SQL queries"],
        support_intensity="guided",
    )


@pytest.fixture
def sample_plan():
    return StudyPlan(
        title="Data Structures Focus Plan",
        goals=["Master Binary Search Trees", "Improve Attendance"],
        priorities=["Data Structures"],
        tasks=[
            StudyTask(
                title="BST Traversal Practice",
                description="Solve 3 traversal questions",
                subject="Data Structures",
                day="Monday",
                duration_minutes=60,
                priority=PriorityLevel.HIGH,
            )
        ],
        resources=["GeeksforGeeks"],
    )


# ── 10 Regression Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_1_who_am_i_direct_answer(sample_context, sample_insight):
    """Test 1: 'Who am I?' -> Direct name answer, NO existential/counseling essay."""
    fake_llm = FakeEchoLLM(response_map={"Current Message:\n\"Who am I?\"": "Ajmal."})
    agent = RecoveryCoachAgent(llm_client=fake_llm)

    req = CoachRequest(
        student_id="student_001",
        user_message="Who am I?",
        student_context=sample_context,
        student_insight=sample_insight,
    )
    resp = await agent.generate_response(req)

    assert resp.response_text.strip() == "Ajmal."
    assert "DIRECT IDENTITY QUERY" in fake_llm.last_user_prompt
    assert "DO NOT give psychological interpretations" in fake_llm.last_user_prompt


@pytest.mark.asyncio
async def test_2_in_one_word_override(sample_context, sample_insight):
    """Test 2: 'in one word' -> Exactly one word answer."""
    fake_llm = FakeEchoLLM(response_map={"Current Message:\n\"in one word\"": "Ajmal"})
    agent = RecoveryCoachAgent(llm_client=fake_llm)

    history = [
        CoachMessageItem(role="user", content="Who am I?"),
        CoachMessageItem(role="assistant", content="Ajmal."),
    ]
    req = CoachRequest(
        student_id="student_001",
        user_message="in one word",
        student_context=sample_context,
        student_insight=sample_insight,
        conversation_history=history,
    )
    resp = await agent.generate_response(req)

    assert resp.response_text.strip() == "Ajmal"
    assert "CRITICAL OVERRIDE — EXACTLY ONE WORD" in fake_llm.last_user_prompt


@pytest.mark.asyncio
async def test_3_what_is_my_attendance_direct(sample_context, sample_insight):
    """Test 3: 'What is my attendance?' -> Direct numerical attendance answer."""
    fake_llm = FakeEchoLLM(response_map={"attendance": "Your current attendance is 67%."})
    agent = RecoveryCoachAgent(llm_client=fake_llm)

    req = CoachRequest(
        student_id="student_001",
        user_message="What is my attendance?",
        student_context=sample_context,
        student_insight=sample_insight,
    )
    resp = await agent.generate_response(req)

    assert "67%" in resp.response_text
    assert "DIRECT FACTUAL DATA" in fake_llm.last_user_prompt


@pytest.mark.asyncio
async def test_4_which_subject_should_i_focus_on(sample_context, sample_insight):
    """Test 4: 'Which subject should I focus on?' -> Direct personalized subject recommendation."""
    fake_llm = FakeEchoLLM(response_map={"focus": "Data Structures would be the main priority right now."})
    agent = RecoveryCoachAgent(llm_client=fake_llm)

    req = CoachRequest(
        student_id="student_001",
        user_message="Which subject should I focus on?",
        student_context=sample_context,
        student_insight=sample_insight,
    )
    resp = await agent.generate_response(req)

    assert "Data Structures" in resp.response_text
    assert "SUBJECT PRIORITY RECOMMENDATION" in fake_llm.last_user_prompt


@pytest.mark.asyncio
async def test_5_how_can_i_improve_data_structures(sample_context, sample_insight):
    """Test 5: 'How can I improve my Data Structures performance?' -> Concise actionable guidance."""
    canned = "To improve in Data Structures, focus on daily practice with Trees and Linked Lists. Solving 2–3 problems a day will build confidence."
    fake_llm = FakeEchoLLM(response_map={"improve": canned})
    agent = RecoveryCoachAgent(llm_client=fake_llm)

    req = CoachRequest(
        student_id="student_001",
        user_message="How can I improve my Data Structures performance?",
        student_context=sample_context,
        student_insight=sample_insight,
    )
    resp = await agent.generate_response(req)

    word_count = len(resp.response_text.split())
    assert "Data Structures" in resp.response_text
    assert word_count <= 80
    assert "ACADEMIC GUIDANCE" in fake_llm.last_user_prompt


@pytest.mark.asyncio
async def test_6_create_a_study_plan_presents_plan(sample_context, sample_insight, sample_plan):
    """Test 6: 'Create a study plan.' -> Uses plan and introduces it concisely."""
    canned = "I've created your Data Structures Focus Plan. Let's start with Monday's BST traversal practice."
    fake_llm = FakeEchoLLM(response_map={"study_plan": canned})
    agent = RecoveryCoachAgent(llm_client=fake_llm)

    req = CoachRequest(
        student_id="student_001",
        user_message="Create a study plan.",
        student_context=sample_context,
        student_insight=sample_insight,
        study_plan=sample_plan,
    )
    resp = await agent.generate_response(req)

    assert resp.has_study_plan is True
    assert resp.study_plan == sample_plan
    assert "STUDY PLAN PRESENTATION" in fake_llm.last_user_prompt


@pytest.mark.asyncio
async def test_7_emotional_support_short_and_supportive(sample_context, sample_insight):
    """Test 7: 'I feel like I'm not good at studies.' -> Short, supportive, grounded response."""
    canned = "Feeling stuck doesn't mean you can't improve. You have a solid grasp of Operating Systems, so let's take things one step at a time with Data Structures."
    fake_llm = FakeEchoLLM(response_map={"not good at": canned})
    agent = RecoveryCoachAgent(llm_client=fake_llm)

    req = CoachRequest(
        student_id="student_001",
        user_message="I feel like I'm not good at studies.",
        student_context=sample_context,
        student_insight=sample_insight,
    )
    resp = await agent.generate_response(req)

    word_count = len(resp.response_text.split())
    assert word_count <= 80
    assert "EMOTIONAL SUPPORT" in fake_llm.last_user_prompt


@pytest.mark.asyncio
async def test_8_explain_data_structures_in_detail():
    """Test 8: 'Explain Data Structures in detail.' -> Detailed educational explanation."""
    fake_llm = FakeEchoLLM(response_map={"detail": "Data Structures in depth: 1. Arrays, 2. Linked Lists, 3. Trees..."})
    agent = RecoveryCoachAgent(llm_client=fake_llm)

    req = CoachRequest(
        student_id="student_001",
        user_message="Explain Data Structures in detail.",
    )
    await agent.generate_response(req)

    assert "DETAILED REQUEST" in fake_llm.last_user_prompt


@pytest.mark.asyncio
async def test_9_explain_in_one_sentence():
    """Test 9: 'Explain it in one sentence.' -> Exactly one sentence."""
    fake_llm = FakeEchoLLM(response_map={"one sentence": "A data structure is a specialized format for organizing, processing, and storing data."})
    agent = RecoveryCoachAgent(llm_client=fake_llm)

    req = CoachRequest(
        student_id="student_001",
        user_message="Explain it in one sentence.",
    )
    await agent.generate_response(req)

    assert "CRITICAL OVERRIDE — EXACTLY ONE SENTENCE" in fake_llm.last_user_prompt


@pytest.mark.asyncio
async def test_10_give_me_3_ways_to_improve():
    """Test 10: 'Give me 3 ways to improve.' -> Exactly 3 concise points."""
    canned = "• Practice coding problems daily.\n• Attend all lecture sessions.\n• Submit lab assignments on time."
    fake_llm = FakeEchoLLM(response_map={"3 ways": canned})
    agent = RecoveryCoachAgent(llm_client=fake_llm)

    req = CoachRequest(
        student_id="student_001",
        user_message="Give me 3 ways to improve.",
    )
    await agent.generate_response(req)

    assert "CRITICAL OVERRIDE — EXACTLY 3 CONCISE BULLET POINTS" in fake_llm.last_user_prompt
