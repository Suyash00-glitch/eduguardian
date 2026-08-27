"""
Unit tests for the Student Insight Agent.

Tests cover:
1. Strong student performance (all indicators positive)
2. Declining trend detection (attendance & submissions downward)
3. Improving trend detection (positive academic momentum)
4. Mixed performance (strengths in one course, focus needed in another)
5. Missing data handling (gracefully handles partial context without unsupported claims)
6. No historical data (evaluates current snapshot without fabricating historical trends)
7. Multiple contributing factors aggregation
8. Positive factors recognition
9. Strict schema compliance (validates against StudentInsight schema)
10. Safety check (zero judgmental labels like dull, lazy, stupid, bad student, failure)
"""
from __future__ import annotations

import re
import pytest

from chatbot.backend.agents.student_insight.agent import StudentInsightAgent
from chatbot.backend.schemas.student import (
    StudentContext,
    AttendanceSummary,
    SubjectPerformance,
    AssignmentSummary,
    AssessmentSummary,
    EngagementSummary,
    TrendInformation,
)
from chatbot.backend.schemas.insight import InsightRequest, StudentInsight

# Regex for safety verification against judgmental labels
_JUDGMENTAL_LABELS = re.compile(
    r"\b(dull|lazy|stupid|bad student|failure|incapable|hopeless|idiot)\b",
    re.IGNORECASE,
)


class TestStudentInsightAgent:

    def test_1_strong_student_performance(self):
        """Strong attendance, marks, and submissions yield strengths and standard intensity."""
        agent = StudentInsightAgent()
        ctx = StudentContext(
            student_id="student_001",
            student_name="Rahul Menon",
            attendance=AttendanceSummary(overall_percentage=94.0, trend="improving"),
            subjects=[
                SubjectPerformance(subject_name="Operating Systems", current_marks_percentage=90.0, grade="A"),
                SubjectPerformance(subject_name="Machine Learning", current_marks_percentage=88.0, grade="A"),
            ],
            assignments=AssignmentSummary(total_assigned=10, total_submitted=10, pending_count=0),
            assessments=AssessmentSummary(gpa=9.1, average_quiz_score=92.0),
        )

        insight = agent.analyze(ctx)

        assert isinstance(insight, StudentInsight)
        assert len(insight.strengths) > 0
        assert "Operating Systems" in insight.strengths
        assert "Machine Learning" in insight.strengths
        assert insight.support_intensity == "standard"
        assert insight.has_concerning_patterns is False
        assert not _JUDGMENTAL_LABELS.search(insight.overall_summary)

    def test_2_declining_trend_detection(self):
        """Declining attendance and pending assignments trigger focus areas and intensive intensity."""
        agent = StudentInsightAgent()
        ctx = StudentContext(
            student_id="student_002",
            student_name="Aisha Raza",
            attendance=AttendanceSummary(
                overall_percentage=64.0,
                trend="declining",
                subjects_below_threshold=["Data Structures"],
            ),
            subjects=[
                SubjectPerformance(
                    subject_name="Data Structures",
                    current_marks_percentage=48.0,
                    assignment_completion_rate=0.50,
                ),
            ],
            assignments=AssignmentSummary(total_assigned=10, total_submitted=5, pending_count=5),
            trends=TrendInformation(grade_trajectory="downward"),
        )

        insight = agent.analyze(ctx)

        assert "Attendance consistency" in insight.focus_areas or "Attendance momentum" in insight.focus_areas
        assert "Data Structures" in insight.focus_areas
        assert len(insight.contributing_factors) >= 2
        assert insight.support_intensity == "intensive"
        assert insight.has_concerning_patterns is True
        assert not _JUDGMENTAL_LABELS.search(insight.explanation)

    def test_3_improving_trend_recognition(self):
        """Improving quiz and momentum trends are recognized positively."""
        agent = StudentInsightAgent()
        ctx = StudentContext(
            student_id="student_003",
            student_name="Samir Khan",
            attendance=AttendanceSummary(overall_percentage=82.0, trend="improving"),
            trends=TrendInformation(grade_trajectory="improving"),
            assessments=AssessmentSummary(gpa=7.5, average_quiz_score=84.0),
        )

        insight = agent.analyze(ctx)

        assert any("momentum" in s.lower() or "improving" in s.lower() for s in insight.strengths)
        assert insight.has_concerning_patterns is False

    def test_4_mixed_performance(self):
        """Mixed standing identifies both specific strengths and targeted focus areas."""
        agent = StudentInsightAgent()
        ctx = StudentContext(
            student_id="student_004",
            student_name="Priya Sharma",
            attendance=AttendanceSummary(overall_percentage=88.0, trend="stable"),
            subjects=[
                SubjectPerformance(subject_name="Operating Systems", current_marks_percentage=85.0, grade="A"),
                SubjectPerformance(subject_name="Discrete Math", current_marks_percentage=54.0, grade="D"),
            ],
        )

        insight = agent.analyze(ctx)

        assert "Operating Systems" in insight.strengths
        assert "Discrete Math" in insight.focus_areas
        assert len(insight.subject_insights) == 2
        # Check that individual subject insights are granular
        os_insight = next(s for s in insight.subject_insights if s.subject_name == "Operating Systems")
        assert os_insight.status == "strong"
        dm_insight = next(s for s in insight.subject_insights if s.subject_name == "Discrete Math")
        assert dm_insight.status == "needs_focus"

    def test_5_missing_data_graceful_handling(self):
        """When only attendance is provided, no unsupported claims are made about missing dimensions."""
        agent = StudentInsightAgent()
        ctx = StudentContext(
            student_id="student_005",
            student_name="Test Student",
            attendance=AttendanceSummary(overall_percentage=80.0),
            subjects=[],
            assignments=None,
            assessments=None,
            engagement=None,
        )

        insight = agent.analyze(ctx)

        assert isinstance(insight, StudentInsight)
        assert insight.metadata.get("has_assignments_data") is False
        assert insight.metadata.get("has_subjects_data") is False
        # Verify no fabricated claims
        assert len(insight.subject_insights) == 0

    def test_6_no_historical_data_snapshot_only(self):
        """When trends are absent, current metrics are analyzed without claiming a trajectory."""
        agent = StudentInsightAgent()
        ctx = StudentContext(
            student_id="student_006",
            student_name="Elena Vance",
            attendance=AttendanceSummary(overall_percentage=85.0, trend=None),
            trends=None,
        )

        insight = agent.analyze(ctx)

        assert insight.student_id == "student_006"
        # No downward trajectory claimed
        assert not any("downward" in f.lower() for f in insight.focus_areas)

    def test_7_multiple_contributing_factors_aggregation(self):
        """Contributing factors aggregate attendance gaps, low scores, and pending submissions."""
        agent = StudentInsightAgent()
        ctx = StudentContext(
            student_id="student_007",
            student_name="Devin Ross",
            attendance=AttendanceSummary(
                overall_percentage=68.0,
                subjects_below_threshold=["Algorithms"],
            ),
            subjects=[
                SubjectPerformance(subject_name="Algorithms", current_marks_percentage=52.0),
            ],
            assignments=AssignmentSummary(total_assigned=8, total_submitted=4, pending_count=4),
        )

        insight = agent.analyze(ctx)

        factors = " ".join(insight.contributing_factors).lower()
        assert "algorithms" in factors
        assert "attendance" in factors
        assert "pending" in factors or "assignment" in factors

    def test_8_positive_factors_recognition(self):
        """High LMS activity and timely submissions are recognized as positive strengths."""
        agent = StudentInsightAgent()
        ctx = StudentContext(
            student_id="student_008",
            student_name="Kiran Roy",
            attendance=AttendanceSummary(overall_percentage=92.0),
            assignments=AssignmentSummary(total_assigned=12, total_submitted=12),
            engagement=EngagementSummary(lms_logins_last_30_days=25),
        )

        insight = agent.analyze(ctx)

        strengths_str = " ".join(insight.strengths).lower()
        assert "attendance" in strengths_str
        assert "assignment" in strengths_str
        assert "lms" in strengths_str or "portal" in strengths_str

    def test_9_output_conforms_to_schema_roundtrip(self):
        """Insight parses into JSON and restores cleanly matching StudentInsight contract."""
        agent = StudentInsightAgent()
        ctx = StudentContext(
            student_id="student_009",
            student_name="Maya Lin",
            attendance=AttendanceSummary(overall_percentage=78.0),
        )

        req = InsightRequest(student_id="student_009", student_context=ctx)
        insight = agent.analyze(req)

        json_data = insight.model_dump_json()
        restored = StudentInsight.model_validate_json(json_data)
        assert restored.student_id == "student_009"
        assert restored.support_intensity in ("standard", "guided", "intensive")

    def test_10_zero_judgmental_labels(self):
        """All generated texts (summary, explanation, observations) contain no negative labels."""
        agent = StudentInsightAgent()
        # Challenged student profile
        ctx = StudentContext(
            student_id="student_010",
            student_name="Jordan Bell",
            attendance=AttendanceSummary(overall_percentage=55.0, trend="declining"),
            subjects=[
                SubjectPerformance(subject_name="Physics", current_marks_percentage=42.0),
            ],
            assignments=AssignmentSummary(total_assigned=10, total_submitted=3, pending_count=7),
            trends=TrendInformation(grade_trajectory="downward"),
        )

        insight = agent.analyze(ctx)

        full_text = f"{insight.overall_summary} {insight.explanation} {' '.join(insight.contributing_factors)}"
        for s in insight.subject_insights:
            full_text += f" {s.key_observation} {s.recommended_action}"

        assert not _JUDGMENTAL_LABELS.search(full_text)
