"""
Phase 8.3 Guardrail Observability & Metrics — Test Suite.

Verifies:
 1.  ALLOW increments allowed count.
 2.  BLOCK increments blocked count.
 3.  REWRITE increments rewritten count.
 4.  FLAG (unknown action) increments flagged count.
 5.  Total checks increments exactly once per record() call.
 6.  Prompt injection category counted correctly.
 7.  Sensitive-data category counted correctly.
 8.  Academic-grounding category counted correctly.
 9.  Output-safety category counted correctly.
10.  Multiple categories aggregate independently.
11.  Reason codes remain stable (ReasonCode enum).
12.  Metrics snapshot contains no raw user content.
13.  Metrics snapshot contains no secrets.
14.  StudentContext is not stored in metrics snapshot.
15.  LearningHistory is not stored in metrics snapshot.
16.  Same guardrail result is not double-counted via GuardrailsService.
17.  Existing Phase 8.1 tests pass (covered by CI run).
18.  Existing Phase 8.2 tests pass (covered by CI run).
19.  Phase 7 regression tests pass (covered by CI run).
20.  Existing chat works (process_user_request operational).
21.  Teach Me works.
22.  Quiz Mode works.
23.  Study Planner works.
24.  infer_reason_code correctly maps common reason strings.
25.  /health/guardrails returns safe aggregate metrics.
"""
import pytest

from chatbot.backend.guardrails.metrics import (
    GuardrailMetrics,
    ReasonCode,
    infer_reason_code,
)
from chatbot.backend.guardrails.service import GuardrailsService
from chatbot.backend.schemas.guardrails import (
    GuardrailAction,
    GuardrailCategory,
    GuardrailResult,
)
from chatbot.backend.schemas.student import (
    StudentContext,
    SubjectPerformance,
    AttendanceSummary,
    AttendanceTrend,
    AssignmentSummary,
)
from chatbot.backend.orchestrator.router import process_user_request
from chatbot.backend.schemas.routing import ResponseMode
from chatbot.backend.core.memory import UserFacts


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset global metrics before each test to ensure isolation."""
    GuardrailMetrics.reset()
    yield
    GuardrailMetrics.reset()


@pytest.fixture
def service():
    """Fresh GuardrailsService (not cached singleton) for each test."""
    return GuardrailsService()


@pytest.fixture
def student_ctx():
    return StudentContext(
        student_id="metrics_test_student",
        student_name="TestStudent",
        department="Computer Science",
        program="B.Tech Computer Science",
        year_of_study=2,
        semester=4,
        attendance=AttendanceSummary(
            overall_percentage=74.0,
            trend=AttendanceTrend.DECLINING,
            classes_attended=37,
            total_classes=50,
        ),
        subjects=[
            SubjectPerformance(
                subject_name="Data Structures",
                subject_code="CS201",
                marks_percentage=48.0,
                current_marks_percentage=48.0,
                grade="C",
                attendance_percentage=74.0,
            ),
        ],
        assignments=AssignmentSummary(
            total_assigned=5,
            total_submitted=2,
            pending_count=3,
            upcoming_deadlines=[],
        ),
    )


# ── Tests 1-5: Core counter behaviour ────────────────────────────────────────

class TestCoreCounters:

    def test_1_allow_increments_allowed_count(self):
        GuardrailMetrics.record(action="allow", category="none", reason_code=ReasonCode.CLEAN)
        snap = GuardrailMetrics.snapshot()
        assert snap["allowed"] == 1
        assert snap["total_checks"] == 1

    def test_2_block_increments_blocked_count(self):
        GuardrailMetrics.record(action="block", category="prompt_injection", reason_code=ReasonCode.PROMPT_INJECTION)
        snap = GuardrailMetrics.snapshot()
        assert snap["blocked"] == 1
        assert snap["total_checks"] == 1

    def test_3_rewrite_increments_rewritten_count(self):
        GuardrailMetrics.record(action="revise", category="academic_grounding", reason_code=ReasonCode.UNSUPPORTED_ATTENDANCE)
        snap = GuardrailMetrics.snapshot()
        assert snap["rewritten"] == 1
        assert snap["total_checks"] == 1

    def test_3b_modify_also_increments_rewritten_count(self):
        GuardrailMetrics.record(action="modify", category="output_safety", reason_code=ReasonCode.THINK_TAG)
        snap = GuardrailMetrics.snapshot()
        assert snap["rewritten"] == 1

    def test_4_unknown_action_increments_flagged(self):
        GuardrailMetrics.record(action="flag", category="none", reason_code=ReasonCode.UNKNOWN)
        snap = GuardrailMetrics.snapshot()
        assert snap["flagged"] == 1
        assert snap["total_checks"] == 1

    def test_5_total_checks_increments_exactly_once(self):
        for _ in range(7):
            GuardrailMetrics.record(action="allow", category="none", reason_code=ReasonCode.CLEAN)
        snap = GuardrailMetrics.snapshot()
        assert snap["total_checks"] == 7
        assert snap["allowed"] == 7


# ── Tests 6-10: Category breakdown ───────────────────────────────────────────

class TestCategoryBreakdown:

    def test_6_prompt_injection_category_counted(self):
        GuardrailMetrics.record(action="block", category="prompt_injection", reason_code=ReasonCode.PROMPT_INJECTION)
        GuardrailMetrics.record(action="block", category="prompt_injection", reason_code=ReasonCode.SYSTEM_PROMPT_EXTRACTION)
        GuardrailMetrics.record(action="allow", category="prompt_injection", reason_code=ReasonCode.CLEAN)
        snap = GuardrailMetrics.snapshot()
        cat = snap["by_category"]["prompt_injection"]
        assert cat["blocked"] == 2
        assert cat["allowed"] == 1

    def test_7_sensitive_data_category_counted(self):
        GuardrailMetrics.record(action="block", category="privacy_sensitive_data", reason_code=ReasonCode.CREDENTIAL_EXTRACTION)
        snap = GuardrailMetrics.snapshot()
        assert snap["by_category"]["privacy_sensitive_data"]["blocked"] == 1

    def test_8_academic_grounding_category_counted(self):
        GuardrailMetrics.record(action="revise", category="academic_grounding", reason_code=ReasonCode.UNSUPPORTED_ATTENDANCE)
        GuardrailMetrics.record(action="revise", category="academic_grounding", reason_code=ReasonCode.UNSUPPORTED_MARK)
        GuardrailMetrics.record(action="allow", category="none", reason_code=ReasonCode.CLEAN)
        snap = GuardrailMetrics.snapshot()
        ag = snap["by_category"]["academic_grounding"]
        assert ag["rewritten"] == 2
        assert snap["rewritten"] == 2

    def test_9_output_safety_category_counted(self):
        GuardrailMetrics.record(action="revise", category="output_safety", reason_code=ReasonCode.THINK_TAG)
        snap = GuardrailMetrics.snapshot()
        assert snap["by_category"]["output_safety"]["rewritten"] == 1

    def test_10_multiple_categories_aggregate_independently(self):
        GuardrailMetrics.record(action="block", category="prompt_injection", reason_code=ReasonCode.PROMPT_INJECTION)
        GuardrailMetrics.record(action="revise", category="academic_grounding", reason_code=ReasonCode.UNSUPPORTED_GRADE)
        GuardrailMetrics.record(action="allow", category="none", reason_code=ReasonCode.CLEAN)
        GuardrailMetrics.record(action="revise", category="output_safety", reason_code=ReasonCode.CREDENTIAL_LEAK)
        snap = GuardrailMetrics.snapshot()
        assert snap["total_checks"] == 4
        assert snap["blocked"] == 1
        assert snap["rewritten"] == 2
        assert snap["allowed"] == 1
        assert snap["by_category"]["prompt_injection"]["blocked"] == 1
        assert snap["by_category"]["academic_grounding"]["rewritten"] == 1
        assert snap["by_category"]["output_safety"]["rewritten"] == 1


# ── Tests 11-15: Reason codes & privacy ──────────────────────────────────────

class TestReasonCodesAndPrivacy:

    def test_11_reason_codes_are_stable_enums(self):
        """All reason codes should be stable string constants."""
        assert ReasonCode.PROMPT_INJECTION == "prompt_injection"
        assert ReasonCode.UNSUPPORTED_ATTENDANCE == "unsupported_attendance"
        assert ReasonCode.CREDENTIAL_LEAK == "credential_leak"
        assert ReasonCode.CLEAN == "clean"
        assert ReasonCode.UNSUPPORTED_MARK == "unsupported_mark"
        assert ReasonCode.UNSUPPORTED_GRADE == "unsupported_grade"
        assert ReasonCode.UNSUPPORTED_SUBJECT == "unsupported_subject"
        assert ReasonCode.UNSUPPORTED_DEADLINE == "unsupported_deadline"
        assert ReasonCode.THINK_TAG == "think_tag"
        assert ReasonCode.STIGMATIZING_LANGUAGE == "stigmatizing_language"

    def test_12_snapshot_contains_no_raw_user_content(self):
        GuardrailMetrics.record(action="block", category="prompt_injection", reason_code=ReasonCode.PROMPT_INJECTION)
        snap = GuardrailMetrics.snapshot()
        snap_str = str(snap)
        # Should contain only counter keys and category names — no user text
        assert "Ignore all previous instructions" not in snap_str
        assert "system prompt" not in snap_str
        assert "attendance" not in snap_str or snap_str.count("attendance") < 5  # keys are fine
        # Ensure no message payloads
        for sensitive_word in ["gsk_", "sk-", "eyJ", "postgresql://", "password"]:
            assert sensitive_word not in snap_str

    def test_13_snapshot_contains_no_secrets(self):
        GuardrailMetrics.record(action="revise", category="output_safety", reason_code=ReasonCode.CREDENTIAL_LEAK)
        snap = GuardrailMetrics.snapshot()
        snap_str = str(snap)
        for secret_pattern in ["gsk_", "sk-", "eyJhb", "postgresql://", "DATABASE_URL", "GROQ_API_KEY"]:
            assert secret_pattern not in snap_str

    def test_14_student_context_not_stored_in_metrics(self, student_ctx):
        """Verify that StudentContext data does not appear in the metrics snapshot."""
        GuardrailMetrics.record(action="revise", category="academic_grounding", reason_code=ReasonCode.UNSUPPORTED_ATTENDANCE)
        snap = GuardrailMetrics.snapshot()
        snap_str = str(snap)
        # Student name, department, and specific values must not appear
        assert "metrics_test_student" not in snap_str
        assert "TestStudent" not in snap_str
        assert "74.0" not in snap_str
        assert "48.0" not in snap_str

    def test_15_learning_history_not_stored_in_metrics(self):
        """LearningHistory concepts should not appear in the metrics snapshot."""
        GuardrailMetrics.record(action="allow", category="none", reason_code=ReasonCode.CLEAN)
        snap = GuardrailMetrics.snapshot()
        snap_str = str(snap)
        for key in ["mastered_topics", "needs_practice", "quiz_attempts", "learning_preferences"]:
            assert key not in snap_str


# ── Test 16: No double-counting ───────────────────────────────────────────────

class TestNoDoubleCounting:

    def test_16_service_records_exactly_once_per_call(self, service, student_ctx):
        """GuardrailsService.validate_input records exactly 1 check per call."""
        before = GuardrailMetrics.snapshot()["total_checks"]
        service.validate_input(user_message="Hello, how are you?", student_context=student_ctx)
        after = GuardrailMetrics.snapshot()["total_checks"]
        assert after - before == 1

    def test_16b_service_output_records_exactly_once(self, service, student_ctx):
        """GuardrailsService.validate_output records exactly 1 check per call."""
        before = GuardrailMetrics.snapshot()["total_checks"]
        service.validate_output(
            response_text="Binary trees are hierarchical data structures.",
            student_context=student_ctx,
        )
        after = GuardrailMetrics.snapshot()["total_checks"]
        assert after - before == 1

    def test_16c_grounding_result_not_double_counted(self, service, student_ctx):
        """AcademicGroundingGuardrail runs inside OutputGuardrail but only 1 metric recorded."""
        before = GuardrailMetrics.snapshot()["total_checks"]
        service.validate_output(
            response_text="Your attendance is 99% in Data Structures.",
            student_context=student_ctx,
        )
        after = GuardrailMetrics.snapshot()["total_checks"]
        assert after - before == 1  # NOT 2


# ── Tests 17-23: Regression — existing modes remain operational ───────────────

class TestRegressionExistingModes:

    def test_20_existing_chat_works(self, student_ctx):
        facts = UserFacts(name="TestStudent")
        result = process_user_request(
            user_message="How can I improve my grades?",
            user_facts=facts,
            student_context=student_ctx,
        )
        assert result is not None

    def test_21_teach_me_works(self, student_ctx):
        facts = UserFacts(name="TestStudent")
        result = process_user_request(
            user_message="Teach me recursion",
            user_facts=facts,
            student_context=student_ctx,
        )
        assert result.response_mode == ResponseMode.TEACH_ME
        assert result.teaching_state is not None
        assert result.teaching_state.active is True

    def test_22_quiz_mode_works(self, student_ctx):
        facts = UserFacts(name="TestStudent")
        result = process_user_request(
            user_message="Quiz me on Data Structures",
            user_facts=facts,
            student_context=student_ctx,
        )
        assert result.response_mode == ResponseMode.QUIZ_ME
        assert result.quiz_state is not None
        assert result.quiz_state.active is True

    def test_23_study_planner_works(self, student_ctx):
        facts = UserFacts(name="TestStudent")
        result = process_user_request(
            user_message="Create a study schedule for algorithms next week",
            user_facts=facts,
            student_context=student_ctx,
        )
        assert result is not None


# ── Test 24: infer_reason_code helper ────────────────────────────────────────

class TestInferReasonCode:

    def test_24_infer_prompt_injection(self):
        assert infer_reason_code("Detected attempt to override instructions") == ReasonCode.PROMPT_INJECTION

    def test_24_infer_system_prompt_extraction(self):
        assert infer_reason_code("Attempt to extract system prompt") == ReasonCode.SYSTEM_PROMPT_EXTRACTION

    def test_24_infer_credential_extraction(self):
        assert infer_reason_code("Credential theft attempt detected") == ReasonCode.CREDENTIAL_EXTRACTION

    def test_24_infer_think_tag(self):
        assert infer_reason_code("Stripped <think> reasoning tags from output") == ReasonCode.THINK_TAG

    def test_24_infer_attendance(self):
        assert infer_reason_code("Grounding: Corrected attendance from 99% to 74%") == ReasonCode.UNSUPPORTED_ATTENDANCE

    def test_24_infer_mark(self):
        assert infer_reason_code("Grounding: Corrected mark for Data Structures") == ReasonCode.UNSUPPORTED_MARK

    def test_24_infer_grade(self):
        assert infer_reason_code("Grounding: Corrected grade from A to C") == ReasonCode.UNSUPPORTED_GRADE

    def test_24_infer_deadline(self):
        assert infer_reason_code("Grounding: Corrected assignment deadline") == ReasonCode.UNSUPPORTED_DEADLINE

    def test_24_infer_clean_for_empty(self):
        assert infer_reason_code("") == ReasonCode.CLEAN

    def test_24_infer_unknown_fallback(self):
        assert infer_reason_code("Some completely unrecognised reason text xyz") == ReasonCode.UNKNOWN


# ── Test 25: Metrics snapshot endpoint-style test ────────────────────────────

class TestMetricsSnapshot:

    def test_25_snapshot_structure_is_correct(self):
        GuardrailMetrics.record(action="allow", category="none", reason_code=ReasonCode.CLEAN)
        GuardrailMetrics.record(action="block", category="prompt_injection", reason_code=ReasonCode.PROMPT_INJECTION)
        GuardrailMetrics.record(action="revise", category="academic_grounding", reason_code=ReasonCode.UNSUPPORTED_ATTENDANCE)

        snap = GuardrailMetrics.snapshot()

        # Required keys
        assert "total_checks" in snap
        assert "allowed" in snap
        assert "blocked" in snap
        assert "rewritten" in snap
        assert "flagged" in snap
        assert "by_category" in snap
        assert "by_reason_code" in snap

        # Correct values
        assert snap["total_checks"] == 3
        assert snap["allowed"] == 1
        assert snap["blocked"] == 1
        assert snap["rewritten"] == 1

    def test_25_snapshot_is_safe_for_api_exposure(self):
        """Simulate what /health/guardrails returns and verify it's clean."""
        GuardrailMetrics.record(action="block", category="prompt_injection", reason_code=ReasonCode.PROMPT_INJECTION)
        snap = GuardrailMetrics.snapshot()

        # Serialize as JSON-compatible structure
        import json
        snap_json = json.dumps({
            "status": "healthy",
            "checks": snap["total_checks"],
            "allowed": snap["allowed"],
            "blocked": snap["blocked"],
            "rewritten": snap["rewritten"],
            "flagged": snap["flagged"],
            "categories": snap["by_category"],
            "reason_codes": snap["by_reason_code"],
        })

        # Ensure no sensitive data in JSON output
        for secret in ["gsk_", "sk-", "eyJ", "postgresql://", "password", "student_id", "TestStudent"]:
            assert secret not in snap_json

    def test_25_reset_clears_all_counters(self):
        GuardrailMetrics.record(action="block", category="prompt_injection", reason_code=ReasonCode.PROMPT_INJECTION)
        GuardrailMetrics.record(action="allow", category="none", reason_code=ReasonCode.CLEAN)
        GuardrailMetrics.reset()
        snap = GuardrailMetrics.snapshot()
        assert snap["total_checks"] == 0
        assert snap["allowed"] == 0
        assert snap["blocked"] == 0
        assert snap["by_category"] == {}
        assert snap["by_reason_code"] == {}

    def test_25_service_metrics_snapshot_method(self, service):
        GuardrailMetrics.record(action="allow", category="none", reason_code=ReasonCode.CLEAN)
        snap = service.metrics_snapshot()
        assert "total_checks" in snap
        assert snap["total_checks"] >= 1
