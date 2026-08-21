"""
Deterministic Academic Analysis Engine.

Performs rule-based, explainable analysis of student records across:
- Attendance rates and trajectory
- Subject performance (marks, grades, assignment submission rates, quizzes)
- Assignment and submission health
- Assessment trends and GPA
- LMS engagement and activity
- Historical momentum

This module is 100% deterministic, explainable, and does not require external LLM calls.
"""
from __future__ import annotations

import logging
from typing import Any

from chatbot.backend.schemas.student import (
    StudentContext,
    AttendanceSummary,
    SubjectPerformance,
    AssignmentSummary,
    AssessmentSummary,
    EngagementSummary,
    TrendInformation,
)
from chatbot.backend.schemas.insight import (
    StudentInsight,
    SubjectInsight,
)

logger = logging.getLogger(__name__)


def analyze_attendance(attendance: AttendanceSummary | None) -> dict[str, Any]:
    """Analyzes attendance records, trajectory, and course thresholds."""
    if not attendance or attendance.overall_percentage is None:
        return {"has_data": False}

    pct = attendance.overall_percentage
    trend = str(attendance.trend or attendance.recent_trend or "stable").lower()
    below_thresh = attendance.subjects_below_threshold or []

    is_strong = pct >= 85.0
    is_moderate = 75.0 <= pct < 85.0
    needs_attention = pct < 75.0 or len(below_thresh) > 0 or trend == "declining"

    strengths = []
    focus_areas = []
    contributing_factors = []

    if is_strong and trend != "declining":
        strengths.append(f"Strong attendance consistency ({pct:.1f}%)")
    elif is_moderate and trend != "declining":
        strengths.append(f"Steady attendance ({pct:.1f}%)")

    if needs_attention:
        if pct < 75.0:
            focus_areas.append("Attendance consistency")
            contributing_factors.append(f"Overall attendance is at {pct:.1f}% (below 75% target)")
        if trend == "declining":
            focus_areas.append("Attendance momentum")
            contributing_factors.append("Attendance has shown a declining trend recently")
        if below_thresh:
            for s in below_thresh:
                contributing_factors.append(f"Attendance below threshold in {s}")

    return {
        "has_data": True,
        "percentage": pct,
        "trend": trend,
        "is_strong": is_strong,
        "needs_attention": needs_attention,
        "strengths": strengths,
        "focus_areas": focus_areas,
        "contributing_factors": contributing_factors,
    }


def analyze_subjects(subjects: list[SubjectPerformance]) -> dict[str, Any]:
    """Analyzes individual subject marks, assignment completion rates, and quizzes."""
    if not subjects:
        return {"has_data": False, "subject_insights": [], "strengths": [], "focus_areas": []}

    subject_insights: list[SubjectInsight] = []
    strengths: list[str] = []
    focus_areas: list[str] = []
    contributing_factors: list[str] = []
    recommended_topics: list[str] = []

    for s in subjects:
        marks = s.current_marks_percentage if s.current_marks_percentage is not None else s.marks_percentage
        assign_rate = s.assignment_completion_rate
        quiz_avg = s.quiz_average
        att_rate = s.attendance_percentage

        # Evaluate subject standing
        is_high_performing = (marks is not None and marks >= 75.0) or (s.grade in ("A", "A+", "B+"))
        has_academic_drag = (marks is not None and marks < 60.0) or (assign_rate is not None and assign_rate < 0.70)

        if is_high_performing:
            status = "strong"
            strengths.append(s.subject_name)
            key_obs = f"Solid mastery in {s.subject_name}"
            if marks is not None:
                key_obs += f" ({marks:.0f}% marks)"
            rec_action = f"Maintain current review rhythm and explore advanced topics in {s.subject_name}."
        elif has_academic_drag:
            status = "needs_focus"
            focus_areas.append(s.subject_name)
            recommended_topics.append(f"{s.subject_name} core revision")

            observations = []
            if marks is not None and marks < 60.0:
                observations.append(f"current score is {marks:.0f}%")
                contributing_factors.append(f"Lower score in {s.subject_name} ({marks:.0f}%)")
            if assign_rate is not None and assign_rate < 0.70:
                observations.append(f"assignment completion is at {assign_rate*100:.0f}%")
                contributing_factors.append(f"Pending assignments in {s.subject_name}")

            key_obs = f"{s.subject_name} has opportunity for growth: {', '.join(observations)}." if observations else f"{s.subject_name} needs additional focus."
            rec_action = f"Dedicate structured 60-90 min practice blocks to {s.subject_name} foundational topics."
        else:
            status = "steady"
            key_obs = f"Progressing steadily in {s.subject_name}."
            rec_action = f"Continue consistent weekly assignments and review key notes in {s.subject_name}."

        subject_insights.append(
            SubjectInsight(
                subject_name=s.subject_name,
                status=status,
                key_observation=key_obs,
                recommended_action=rec_action,
            )
        )

    return {
        "has_data": True,
        "subject_insights": subject_insights,
        "strengths": strengths,
        "focus_areas": focus_areas,
        "contributing_factors": contributing_factors,
        "recommended_topics": recommended_topics,
    }


def analyze_assignments(assignments: AssignmentSummary | None) -> dict[str, Any]:
    """Analyzes overall assignment completion and submission health."""
    if not assignments or assignments.total_assigned == 0:
        return {"has_data": False}

    submitted = assignments.total_submitted
    total = assignments.total_assigned
    pending = assignments.pending_count or (total - submitted)
    rate = submitted / total if total > 0 else 1.0

    strengths = []
    focus_areas = []
    contributing_factors = []

    if rate >= 0.90:
        strengths.append(f"Excellent assignment consistency ({submitted}/{total} submitted)")
    elif rate < 0.75:
        focus_areas.append("Assignment completion rate")
        contributing_factors.append(f"{pending} pending assignment(s) across coursework")

    return {
        "has_data": True,
        "submission_rate": rate,
        "pending_count": pending,
        "strengths": strengths,
        "focus_areas": focus_areas,
        "contributing_factors": contributing_factors,
    }


def analyze_assessments(assessments: AssessmentSummary | None) -> dict[str, Any]:
    """Analyzes GPA and quiz assessments."""
    if not assessments:
        return {"has_data": False}

    strengths = []
    focus_areas = []
    contributing_factors = []

    if assessments.gpa is not None:
        if assessments.gpa >= 8.0:
            strengths.append(f"Strong academic standing (GPA {assessments.gpa:.2f})")
        elif assessments.gpa < 6.0:
            focus_areas.append("Overall semester GPA trajectory")
            contributing_factors.append(f"Current GPA is {assessments.gpa:.2f}")

    if assessments.average_quiz_score is not None:
        if assessments.average_quiz_score >= 80.0:
            strengths.append(f"High quiz performance ({assessments.average_quiz_score:.0f}% avg)")
        elif assessments.average_quiz_score < 60.0:
            focus_areas.append("Quiz assessment preparation")
            contributing_factors.append(f"Recent quiz average is {assessments.average_quiz_score:.0f}%")

    return {
        "has_data": True,
        "strengths": strengths,
        "focus_areas": focus_areas,
        "contributing_factors": contributing_factors,
    }


def analyze_engagement(engagement: EngagementSummary | None) -> dict[str, Any]:
    """Analyzes portal and LMS activity metrics."""
    if not engagement:
        return {"has_data": False}

    strengths = []
    focus_areas = []
    contributing_factors = []

    logins = engagement.lms_logins_last_30_days
    materials = engagement.study_materials_accessed or engagement.resources_accessed

    if logins is not None:
        if logins >= 20:
            strengths.append("High LMS engagement and active portal usage")
        elif logins < 5:
            focus_areas.append("LMS resource access")
            contributing_factors.append(f"Low LMS activity ({logins} logins in last 30 days)")

    return {
        "has_data": True,
        "strengths": strengths,
        "focus_areas": focus_areas,
        "contributing_factors": contributing_factors,
    }


def analyze_trends(trends: TrendInformation | None) -> dict[str, Any]:
    """Analyzes historical momentum and trajectories."""
    if not trends or not trends.grade_trajectory:
        return {"has_data": False}

    strengths = []
    focus_areas = []
    contributing_factors = []

    traj = trends.grade_trajectory.lower()
    if traj in ("upward", "improving"):
        strengths.append("Positive upward academic momentum")
    elif traj in ("downward", "declining"):
        focus_areas.append("Academic trend stabilization")
        contributing_factors.append("Recent performance shows downward trajectory")

    return {
        "has_data": True,
        "trajectory": traj,
        "strengths": strengths,
        "focus_areas": focus_areas,
        "contributing_factors": contributing_factors,
    }


def analyze_historical_academic_performance(perf: dict[str, Any] | None) -> dict[str, Any]:
    """Analyzes authoritative historical portal academic performance (CGPA, SGPA, credits, backlogs)."""
    if not perf or not isinstance(perf, dict):
        return {"has_data": False}

    cgpa = perf.get("cgpa")
    latest_sgpa = perf.get("latest_sgpa")
    sgpa_trend = str(perf.get("sgpa_trend") or "stable").lower()
    total_sems = perf.get("total_semesters_completed") or 0
    total_credits = perf.get("total_credits_earned")
    arrears = perf.get("arrears_count") or 0

    strengths = []
    focus_areas = []
    contributing_factors = []

    if cgpa is not None:
        cgpa_val = float(cgpa)
        if cgpa_val >= 7.5:
            strengths.append(f"Strong overall academic standing (CGPA: {cgpa_val:.2f})")
        elif cgpa_val < 6.0:
            focus_areas.append("CGPA improvement")
            contributing_factors.append(f"Current CGPA is {cgpa_val:.2f}")

    if latest_sgpa is not None:
        sgpa_val = float(latest_sgpa)
        if sgpa_val >= 7.5:
            strengths.append(f"High latest semester performance (SGPA: {sgpa_val:.2f})")

    if sgpa_trend == "improving":
        strengths.append("Consistently improving semester SGPA trajectory")
    elif sgpa_trend == "declining":
        focus_areas.append("Semester SGPA stabilization")
        contributing_factors.append("Latest SGPA trajectory has shown a decline")

    if arrears == 0 and total_sems > 0:
        strengths.append("Clear academic record with zero backlogs")
    elif arrears > 0:
        focus_areas.append(f"Clearing active backlogs ({arrears} backlog{'s' if arrears > 1 else ''})")
        contributing_factors.append(f"{arrears} active backlog course(s) from prior semesters")

    return {
        "has_data": True,
        "cgpa": cgpa,
        "latest_sgpa": latest_sgpa,
        "sgpa_trend": sgpa_trend,
        "total_semesters_completed": total_sems,
        "total_credits_earned": total_credits,
        "arrears_count": arrears,
        "strengths": strengths,
        "focus_areas": focus_areas,
        "contributing_factors": contributing_factors,
    }


def synthesize_academic_insight(
    context: StudentContext,
    query_context: str | None = None,
) -> StudentInsight:
    """
    Main entry point for deterministic academic insight generation.

    Integrates findings across attendance, courses, assignments, quizzes,
    engagement, historical academic performance (CGPA/SGPA), and trends into
    a cohesive, evidence-based StudentInsight.
    """
    student_id = context.student_id

    # 1. Run component analyses
    att_res = analyze_attendance(context.attendance)
    sub_res = analyze_subjects(context.subjects)
    asg_res = analyze_assignments(context.assignments)
    ass_res = analyze_assessments(context.assessments)
    eng_res = analyze_engagement(context.engagement)
    trd_res = analyze_trends(context.trends)
    hist_res = analyze_historical_academic_performance(context.historical_academic_performance)

    # 2. Aggregate findings
    all_strengths = (
        hist_res.get("strengths", [])
        + att_res.get("strengths", [])
        + sub_res.get("strengths", [])
        + asg_res.get("strengths", [])
        + ass_res.get("strengths", [])
        + eng_res.get("strengths", [])
        + trd_res.get("strengths", [])
    )

    all_focus_areas = (
        hist_res.get("focus_areas", [])
        + att_res.get("focus_areas", [])
        + sub_res.get("focus_areas", [])
        + asg_res.get("focus_areas", [])
        + ass_res.get("focus_areas", [])
        + eng_res.get("focus_areas", [])
        + trd_res.get("focus_areas", [])
    )

    all_contributing_factors = (
        hist_res.get("contributing_factors", [])
        + att_res.get("contributing_factors", [])
        + sub_res.get("contributing_factors", [])
        + asg_res.get("contributing_factors", [])
        + ass_res.get("contributing_factors", [])
        + eng_res.get("contributing_factors", [])
        + trd_res.get("contributing_factors", [])
    )

    recommended_areas = sub_res.get("recommended_topics", [])
    if not recommended_areas and all_focus_areas:
        recommended_areas = [f"{fa} regular practice" for fa in all_focus_areas[:3]]

    # 3. Determine support intensity and concerning pattern flags (internal only)
    has_declining_attendance = att_res.get("trend") == "declining" or (att_res.get("percentage", 100) < 70.0)
    has_multiple_focus_subjects = len(sub_res.get("focus_areas", [])) >= 2
    has_low_submissions = asg_res.get("submission_rate", 1.0) < 0.65
    has_multiple_backlogs = (hist_res.get("arrears_count") or 0) >= 2

    concerning_count = sum([has_declining_attendance, has_multiple_focus_subjects, has_low_submissions, has_multiple_backlogs])
    has_concerning_patterns = concerning_count >= 2

    if has_concerning_patterns:
        support_intensity = "intensive"
    elif len(all_focus_areas) > 0:
        support_intensity = "guided"
    else:
        support_intensity = "standard"

    # 4. Generate evidence-based summary & explanation
    q_lower = (query_context or "").lower()
    is_cgpa_query = "cgpa" in q_lower or "sgpa" in q_lower or "gpa" in q_lower

    if is_cgpa_query and hist_res.get("has_data"):
        cgpa_val = hist_res.get("cgpa")
        sgpa_val = hist_res.get("latest_sgpa")
        trend_val = hist_res.get("sgpa_trend", "stable")
        sems_val = hist_res.get("total_semesters_completed", 0)
        summary = f"Current CGPA is {cgpa_val} with latest SGPA of {sgpa_val} (Semester {sems_val}) and {trend_val} academic trajectory."
        explanation = f"Academic standing is established from {sems_val} completed semesters of examination records."
    elif not all_strengths and not all_focus_areas:
        summary = "Student academic profile is on track with steady baseline engagement."
        explanation = "Available records indicate consistent ongoing progress."
    elif all_strengths and not all_focus_areas:
        summary = f"Student demonstrates strong performance across {', '.join(all_strengths[:2])}."
        explanation = "Consistent attendance and academic trajectory are driving positive outcomes."
    elif all_focus_areas and not all_strengths:
        summary = f"Opportunities identified to reinforce {', '.join(all_focus_areas[:2])} through structured study."
        explanation = f"Focusing on {', '.join(all_contributing_factors[:2])} will provide the highest impact."
    else:
        summary = f"Strong performance in {', '.join(all_strengths[:2])}, with focused practice recommended in {', '.join(all_focus_areas[:2])}."
        explanation = f"Leveraging strengths while dedicating structured study time to {all_focus_areas[0]} will maintain balanced academic momentum."

    return StudentInsight(
        student_id=student_id,
        overall_summary=summary,
        strengths=all_strengths,
        focus_areas=all_focus_areas,
        subject_insights=sub_res.get("subject_insights", []),
        contributing_factors=all_contributing_factors,
        recommended_areas_of_attention=recommended_areas,
        explanation=explanation,
        support_intensity=support_intensity,
        has_concerning_patterns=has_concerning_patterns,
        metadata={
            "analysis_mode": "deterministic_rules",
            "has_attendance_data": att_res.get("has_data", False),
            "has_subjects_data": sub_res.get("has_data", False),
            "has_assignments_data": asg_res.get("has_data", False),
            "has_historical_data": hist_res.get("has_data", False),
            "historical_performance": context.historical_academic_performance or {},
        },
    )
