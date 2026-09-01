"""
Test fixtures: Pre-configured StudentContext objects for automated tests.

This file lives exclusively in tests/ and is never imported or used by production runtime.
"""
from __future__ import annotations

from chatbot.backend.schemas.student import (
    AttendanceSummary,
    AssessmentSummary,
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

STUDENT_A_HIGH_ACHIEVER = StudentContext(
    student_id="student_A_high_achiever",
    student_name="Aarav Sharma",
    department="Information Science",
    year_of_study=3,
    assessments=AssessmentSummary(gpa=8.8),
    historical_academic_performance={"cgpa": 8.8, "latest_sgpa": 8.9},
    attendance=AttendanceSummary(overall_percentage=92.0, trend="stable"),
    subjects=[
        SubjectPerformance(subject_name="Data Structures & Algorithms", current_marks_percentage=94.0, grade="S"),
        SubjectPerformance(subject_name="Operating Systems", current_marks_percentage=89.0, grade="A"),
        SubjectPerformance(subject_name="Machine Learning Foundations", current_marks_percentage=91.0, grade="S"),
        SubjectPerformance(subject_name="Database Management Systems", current_marks_percentage=62.0, grade="D"),
    ],
    risk_level=RiskLevel.LOW,
)

STUDENT_B_STRUGGLING = StudentContext(
    student_id="student_B_struggling",
    student_name="Bhavna Patel",
    department="Information Science",
    year_of_study=3,
    assessments=AssessmentSummary(gpa=6.2),
    historical_academic_performance={"cgpa": 6.2, "latest_sgpa": 6.0},
    attendance=AttendanceSummary(overall_percentage=68.0, trend="declining", subjects_below_threshold=["Operating Systems", "Computer Networks"]),
    subjects=[
        SubjectPerformance(subject_name="Data Structures & Algorithms", current_marks_percentage=71.0, grade="B"),
        SubjectPerformance(subject_name="Operating Systems", current_marks_percentage=54.0, grade="E"),
        SubjectPerformance(subject_name="Database Management Systems", current_marks_percentage=78.0, grade="B"),
        SubjectPerformance(subject_name="Computer Networks", current_marks_percentage=58.0, grade="D"),
    ],
    risk_level=RiskLevel.HIGH,
)

_TEST_STUDENTS = {
    "student_001": STUDENT_001,
    "student_002": STUDENT_002,
    "student_A_high_achiever": STUDENT_A_HIGH_ACHIEVER,
    "student_B_struggling": STUDENT_B_STRUGGLING,
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
