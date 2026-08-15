"""
Test fixtures: Pre-configured StudentContext objects for automated tests.

This file lives exclusively in tests/ and is never imported or used by production runtime.
"""
from __future__ import annotations

from chatbot.backend.schemas.student import (
    AttendanceSummary,
    EngagementMetrics,
    RiskLevel,
    StudentContext,
    SubjectPerformance,
)

STUDENT_001 = StudentContext(
    student_id="student_001",
    student_name="Test Student 1",
    department="Computer Science",
    year_of_study=2,
    attendance=AttendanceSummary(overall_percentage=75.0, trend="stable"),
    subjects=[
        SubjectPerformance(
            subject_name="Data Structures",
            current_marks_percentage=65.0,
            target_marks_percentage=75.0,
            assignment_completion_rate=0.8,
            quiz_average=62.0,
        ),
        SubjectPerformance(
            subject_name="Operating Systems",
            current_marks_percentage=85.0,
            target_marks_percentage=80.0,
            assignment_completion_rate=0.95,
            quiz_average=88.0,
        ),
        SubjectPerformance(
            subject_name="Discrete Mathematics",
            current_marks_percentage=70.0,
            target_marks_percentage=75.0,
            assignment_completion_rate=0.75,
            quiz_average=68.0,
        ),
    ],
    engagement=EngagementMetrics(
        lms_logins_last_30_days=18,
        resources_accessed=42,
        forum_posts=8,
    ),
    risk_level=RiskLevel.MODERATE,
    previous_interventions=["Peer tutoring in Data Structures (Semester 1)"],
)

STUDENT_002 = StudentContext(
    student_id="student_002",
    student_name="Test Student 2",
    department="Information Technology",
    year_of_study=3,
    attendance=AttendanceSummary(overall_percentage=58.0, trend="declining"),
    subjects=[
        SubjectPerformance(
            subject_name="Database Systems",
            current_marks_percentage=52.0,
            target_marks_percentage=70.0,
            assignment_completion_rate=0.6,
            quiz_average=50.0,
        ),
        SubjectPerformance(
            subject_name="Web Technologies",
            current_marks_percentage=48.0,
            target_marks_percentage=65.0,
            assignment_completion_rate=0.55,
            quiz_average=45.0,
        ),
        SubjectPerformance(
            subject_name="Computer Networks",
            current_marks_percentage=60.0,
            target_marks_percentage=65.0,
            assignment_completion_rate=0.7,
            quiz_average=58.0,
        ),
    ],
    engagement=EngagementMetrics(
        lms_logins_last_30_days=8,
        resources_accessed=19,
        forum_posts=2,
    ),
    risk_level=RiskLevel.HIGH,
    previous_interventions=[],
)

_TEST_STUDENTS = {
    "student_001": STUDENT_001,
    "student_002": STUDENT_002,
}

def get_mock_student_context(student_id: str) -> StudentContext:
    """Helper for unit test fixtures."""
    return _TEST_STUDENTS.get(
        student_id,
        StudentContext(
            student_id=student_id,
            student_name="Test Student",
            department="General Engineering",
            year_of_study=1,
            attendance=AttendanceSummary(overall_percentage=80.0, trend="stable"),
            subjects=[
                SubjectPerformance(
                    subject_name="Introduction to Computing",
                    current_marks_percentage=75.0,
                )
            ],
            engagement=EngagementMetrics(
                lms_logins_last_30_days=20,
                resources_accessed=35,
                forum_posts=5,
            ),
        ),
    )
