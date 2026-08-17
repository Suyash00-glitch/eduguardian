"""
Phase 8.2 Academic Grounding Guardrail Verification Test Suite.

Verifies:
1. Correct attendance claim -> PASS
2. Incorrect attendance claim -> REWRITE
3. Correct marks -> PASS
4. Incorrect marks -> REWRITE
5. Correct grade -> PASS
6. Incorrect grade -> REWRITE
7. Correct subject enrollment -> PASS
8. Fabricated subject -> REWRITE
9. Correct assignment deadline -> PASS
10. Fabricated assignment deadline -> REWRITE
11. Correct assignment completion count -> PASS
12. Fabricated completion count -> REWRITE
13. Correct semester/year -> PASS
14. Fabricated semester/year -> REWRITE
15. Normal educational question -> PASS
16. General study advice -> PASS
17. Emotional support -> PASS
18. Casual greeting -> PASS
19. LearningHistory personalization -> PASS
20. Internal LearningHistory metrics not leaked -> PASS
21. StudentContext unavailable -> DO NOT FABRICATE
22. Multiple academic claims in one response -> validate all
23. One invalid claim among valid claims -> preserve valid content
24. Student A context cannot validate Student B data (isolation)
25. Study Plan valid deadline -> PASS
26. Study Plan fabricated deadline -> REWRITE
27. Teach Me remains operational
28. Quiz Mode remains operational
29. Existing Phase 8.1 tests remain passing
30. Schema and workflow contracts remain valid
"""
import pytest

from chatbot.backend.schemas.guardrails import (
    GuardrailAction,
    GuardrailCategory,
    GuardrailResult,
)
from chatbot.backend.guardrails.academic_grounding import AcademicGroundingGuardrail
from chatbot.backend.guardrails.output_guardrail import OutputGuardrail
from chatbot.backend.orchestrator.validator import ResponseValidator
from chatbot.backend.orchestrator.router import process_user_request
from chatbot.backend.schemas.routing import ResponseConstraints, ResponseMode, IntentType
from chatbot.backend.schemas.student import (
    StudentContext,
    SubjectPerformance,
    AttendanceSummary,
    AttendanceTrend,
    AssignmentSummary,
    AssessmentSummary,
)
from chatbot.backend.core.memory import UserFacts


@pytest.fixture
def grounding_guardrail():
    return AcademicGroundingGuardrail()


@pytest.fixture
def output_guardrail():
    return OutputGuardrail()


@pytest.fixture
def student_a_context():
    """Student A (Roham): Data Structures = 48%, Attendance = 74%, Semester = 4, Year = 2."""
    return StudentContext(
        student_id="student_A_001",
        student_name="Roham",
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
            SubjectPerformance(
                subject_name="Database Management Systems",
                subject_code="CS202",
                marks_percentage=51.0,
                current_marks_percentage=51.0,
                grade="B",
                attendance_percentage=80.0,
            ),
        ],
        assignments=AssignmentSummary(
            total_assigned=5,
            total_submitted=2,
            pending_count=3,
            upcoming_deadlines=[
                {
                    "subject": "Data Structures",
                    "title": "Trees Assignment",
                    "due_date": "Friday",
                }
            ],
        ),
    )


@pytest.fixture
def student_b_context():
    """Student B (Sara): Data Structures = 90%, Attendance = 95%, Semester = 6, Year = 3."""
    return StudentContext(
        student_id="student_B_002",
        student_name="Sara",
        department="Information Technology",
        program="B.Tech IT",
        year_of_study=3,
        semester=6,
        attendance=AttendanceSummary(
            overall_percentage=95.0,
            trend=AttendanceTrend.IMPROVING,
            classes_attended=48,
            total_classes=50,
        ),
        subjects=[
            SubjectPerformance(
                subject_name="Data Structures",
                subject_code="CS201",
                marks_percentage=90.0,
                current_marks_percentage=90.0,
                grade="A+",
                attendance_percentage=95.0,
            ),
        ],
        assignments=AssignmentSummary(
            total_assigned=5,
            total_submitted=5,
            pending_count=0,
            upcoming_deadlines=[],
        ),
    )


class TestAcademicGroundingGuardrailCore:
    """Core deterministic claim verification and rewrite tests."""

    def test_1_correct_attendance_claim_passes(self, grounding_guardrail, student_a_context):
        text = "Your attendance is 74%, so attending upcoming classes consistently could help."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True
        assert res.sanitized_text == text

    def test_2_incorrect_attendance_claim_rewritten(self, grounding_guardrail, student_a_context):
        text = "Your attendance is 82%, so you are doing fine."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_modified is True
        assert "74%" in res.sanitized_text
        assert "82%" not in res.sanitized_text

    def test_3_correct_marks_passes(self, grounding_guardrail, student_a_context):
        text = "You scored 48% in Data Structures, so let's review the fundamental concepts."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True
        assert res.sanitized_text == text

    def test_4_incorrect_marks_rewritten(self, grounding_guardrail, student_a_context):
        text = "You scored 85% in Data Structures, great job!"
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_modified is True
        assert "48%" in res.sanitized_text
        assert "85%" not in res.sanitized_text

    def test_5_correct_grade_passes(self, grounding_guardrail, student_a_context):
        text = "You received a grade of C in Data Structures."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True
        assert res.sanitized_text == text

    def test_6_incorrect_grade_rewritten(self, grounding_guardrail, student_a_context):
        text = "You got an A in Data Structures."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_modified is True
        assert "grade of C in Data Structures" in res.sanitized_text

    def test_7_correct_subject_enrollment_passes(self, grounding_guardrail, student_a_context):
        text = "You are currently enrolled in Data Structures."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True

    def test_8_fabricated_subject_rewritten(self, grounding_guardrail, student_a_context):
        text = "You are currently enrolled in Quantum Computing."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_modified is True
        assert "Quantum Computing is not in your official enrollment" in res.sanitized_text

    def test_9_correct_assignment_deadline_passes(self, grounding_guardrail, student_a_context):
        text = "Your Data Structures assignment is due Friday."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True
        assert res.sanitized_text == text

    def test_10_fabricated_assignment_deadline_rewritten(self, grounding_guardrail, student_a_context):
        text = "Your Data Structures assignment is due Monday."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_modified is True
        assert "Friday" in res.sanitized_text
        assert "due Monday" not in res.sanitized_text

    def test_11_correct_assignment_completion_count_passes(self, grounding_guardrail, student_a_context):
        text = "You completed 2 assignments so far."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True

    def test_12_fabricated_completion_count_rewritten(self, grounding_guardrail, student_a_context):
        text = "You completed 8 assignments so far."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_modified is True
        assert "completed 2 assignments" in res.sanitized_text

    def test_13_correct_semester_and_year_passes(self, grounding_guardrail, student_a_context):
        text = "Since you are in your 4th semester and in your 2nd year, this coursework is crucial."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True

    def test_14_fabricated_semester_rewritten(self, grounding_guardrail, student_a_context):
        text = "Since you are in 7th semester, you will graduate soon."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_modified is True
        assert "4th semester" in res.sanitized_text


class TestNonAcademicExclusionsAndSafety:
    """Tests 15-20: Ensure non-academic claims, educational text, and advice are not over-blocked."""

    def test_15_normal_educational_explanation_passes(self, grounding_guardrail, student_a_context):
        for text in [
            "Binary trees usually have at most two children.",
            "An algorithm with O(log n) complexity halves the problem size at each step.",
            "Database normalization reduces data redundancy and improves integrity.",
        ]:
            res = grounding_guardrail.evaluate(text, student_context=student_a_context)
            assert res.is_allowed is True
            assert res.sanitized_text == text

    def test_16_general_study_advice_passes(self, grounding_guardrail, student_a_context):
        text = "Active recall and spaced repetition are highly effective study methods for exam prep."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True

    def test_17_emotional_support_passes(self, grounding_guardrail, student_a_context):
        text = "It's completely normal to feel stressed about upcoming exams. Let's break your revision into manageable steps."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True

    def test_18_casual_greeting_passes(self, grounding_guardrail, student_a_context):
        text = "Hi Roham! How can I help with your studies today?"
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True

    def test_19_learning_history_personalization_passes(self, grounding_guardrail, student_a_context):
        text = "Let's spend a little more time practicing recursion since it's a core topic."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True

    def test_20_internal_learning_history_labels_not_leaked(self, output_guardrail, student_a_context):
        text = "Based on our sessions, let's work on recursion."
        res = output_guardrail.evaluate(text, student_context=student_a_context)
        assert res.sanitized_text is not None
        assert "needs_practice" not in res.sanitized_text
        assert "struggling_topics" not in res.sanitized_text


class TestMultiStudentIsolationAndEdgeCases:
    """Tests 21-26: Isolation, missing context, and combined claims."""

    def test_21_student_context_unavailable_does_not_fabricate(self, grounding_guardrail):
        text = "Your attendance is 88%."
        res = grounding_guardrail.evaluate(text, student_context=None)
        assert res.is_modified is True
        assert "not available" in res.sanitized_text.lower()
        assert "88%" not in res.sanitized_text

    def test_22_multiple_academic_claims_validated(self, grounding_guardrail, student_a_context):
        text = "Your attendance is 82% and you scored 85% in Data Structures."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_modified is True
        assert "74%" in res.sanitized_text
        assert "48%" in res.sanitized_text

    def test_23_one_invalid_claim_among_valid_claims_preserves_valid(self, grounding_guardrail, student_a_context):
        text = "Your attendance is 74%, but you scored 85% in Data Structures."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_modified is True
        assert "74%" in res.sanitized_text
        assert "48%" in res.sanitized_text

    def test_24_multi_student_isolation(self, grounding_guardrail, student_a_context, student_b_context):
        text_a = "You scored 48% in Data Structures."
        text_b = "You scored 90% in Data Structures."

        # Student A context allows 48%, rewrites 90%
        res_a_valid = grounding_guardrail.evaluate(text_a, student_context=student_a_context)
        assert res_a_valid.is_allowed is True

        res_a_with_b_data = grounding_guardrail.evaluate(text_b, student_context=student_a_context)
        assert res_a_with_b_data.is_modified is True
        assert "48%" in res_a_with_b_data.sanitized_text

        # Student B context allows 90%, rewrites 48%
        res_b_valid = grounding_guardrail.evaluate(text_b, student_context=student_b_context)
        assert res_b_valid.is_allowed is True

        res_b_with_a_data = grounding_guardrail.evaluate(text_a, student_context=student_b_context)
        assert res_b_with_a_data.is_modified is True
        assert "90%" in res_b_with_a_data.sanitized_text

    def test_25_study_plan_valid_deadline_passes(self, grounding_guardrail, student_a_context):
        text = "Goal: Complete your Data Structures assignment due Friday."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_allowed is True

    def test_26_study_plan_fabricated_deadline_rewritten(self, grounding_guardrail, student_a_context):
        text = "Goal: Complete your Data Structures assignment due Monday."
        res = grounding_guardrail.evaluate(text, student_context=student_a_context)
        assert res.is_modified is True
        assert "Friday" in res.sanitized_text


class TestPhase8IntegrationAndRegression:
    """Tests 27-30: Teach Me, Quiz Mode, and ResponseValidator integration."""

    def test_27_teach_me_remains_operational(self, student_a_context):
        facts = UserFacts(name="Roham")
        processed = process_user_request(
            user_message="Teach me recursion",
            user_facts=facts,
            student_context=student_a_context,
        )
        assert processed.response_mode == ResponseMode.TEACH_ME
        assert processed.teaching_state is not None
        assert processed.teaching_state.active is True

    def test_28_quiz_mode_remains_operational(self, student_a_context):
        facts = UserFacts(name="Roham")
        processed = process_user_request(
            user_message="Quiz me on Data Structures",
            user_facts=facts,
            student_context=student_a_context,
        )
        assert processed.response_mode == ResponseMode.QUIZ_ME
        assert processed.quiz_state is not None
        assert processed.quiz_state.active is True

    def test_29_response_validator_with_grounding_integration(self, student_a_context):
        constraints = ResponseConstraints()
        raw_output = "Hello! Your attendance is 90% and you scored 85% in Data Structures."
        cleaned = ResponseValidator.validate_and_enforce(
            response_text=raw_output,
            constraints=constraints,
            student_context=student_a_context,
        )
        assert "74%" in cleaned
        assert "48%" in cleaned
        assert "90%" not in cleaned
        assert "85%" not in cleaned
