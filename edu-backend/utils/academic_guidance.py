"""
EduGuardian Student Academic Guidance Generator
================================================
Generates constructive, student-friendly academic interpretation and guidance
based strictly on real academic metrics (CGPA, SGPA, trajectory, backlogs, credits).

DO NOT output internal risk classification labels (HIGH/MEDIUM/LOW RISK),
risk scores, confidence ratings, factors, or SHAP values.
"""
from typing import Dict, Any, Optional


def evaluate_student_academic_guidance(hist_perf: Dict[str, Any]) -> Dict[str, Any]:
    cgpa = hist_perf.get("cgpa")
    latest_sgpa = hist_perf.get("latest_sgpa")
    trend = (hist_perf.get("sgpa_trend") or "stable").lower()
    backlogs = hist_perf.get("arrears_count", 0) or 0
    completed_sems = hist_perf.get("total_semesters_completed") or 0

    cgpa_val = float(cgpa) if cgpa is not None else None
    sgpa_val = float(latest_sgpa) if latest_sgpa is not None else None

    # State 1: Foundation Building (CGPA < 5.0 or 4+ backlogs or critical recent dip)
    if (cgpa_val is not None and cgpa_val < 5.0) or backlogs >= 4 or (sgpa_val is not None and sgpa_val < 5.0 and backlogs > 0):
        badge = "ACADEMIC FOUNDATION BUILDING"
        headline = "Strengthen Your Academic Foundation"
        state = "foundation_building"
        standing_label = "Academic Foundation Building"
        outlook_status = "Foundation Building"
        
        cgpa_str = f"{cgpa_val:.2f}" if cgpa_val is not None else "—"
        sgpa_str = f"{sgpa_val:.2f}" if sgpa_val is not None else "—"
        backlog_txt = f", {backlogs} pending backlog(s)" if backlogs > 0 else ""
        
        message = (
            f"Let's build a stronger academic foundation 💪 Recent examination records indicate areas needing dedicated focus "
            f"(CGPA: {cgpa_str}, Latest SGPA: {sgpa_str}{backlog_txt}). Focused revision in key foundational subjects "
            f"and connecting with your faculty mentor will help you systematically clear pending coursework."
        )
        outlook_message = (
            f"Systematic subject-by-subject preparation and clearing pending coursework will help establish a solid academic baseline."
        )

    # State 2: Focus on Strengthening Performance (CGPA 5.0–5.99 or 1–3 backlogs or declining trend)
    elif (cgpa_val is not None and cgpa_val < 6.0) or (backlogs > 0 and backlogs <= 3) or (trend == "declining" and (cgpa_val or 0) < 7.5):
        badge = "FOCUS ON STRENGTHENING"
        headline = "Focus on Strengthening Performance"
        state = "strengthening_required"
        standing_label = "Attention Recommended" if backlogs > 0 else "Passing Standing"
        outlook_status = "Focus Required"
        
        cgpa_str = f"{cgpa_val:.2f}" if cgpa_val is not None else "—"
        sgpa_str = f"{sgpa_val:.2f}" if sgpa_val is not None else "—"
        backlog_txt = f" with {backlogs} pending subject(s)" if backlogs > 0 else ""
        
        message = (
            f"Let's focus on strengthening your academic momentum 💪 (CGPA: {cgpa_str}, Latest SGPA: {sgpa_str}{backlog_txt}). "
            f"Targeted practice on core topics and clearing pending subjects will help elevate your upcoming semester results."
        )
        outlook_message = (
            f"Focus on targeted revision and clearing pending subjects to rebuild positive academic momentum."
        )

    # State 3: Steady Academic Progress (CGPA 6.0–7.49 with 0 backlogs)
    elif cgpa_val is not None and cgpa_val >= 6.0 and cgpa_val < 7.5 and backlogs == 0:
        badge = "FIRST CLASS STANDING" if cgpa_val >= 6.5 else "STEADY PROGRESS"
        headline = "Steady Academic Progress"
        state = "steady_progress"
        standing_label = "First Class standing" if cgpa_val >= 6.5 else "Good standing"
        outlook_status = "Steady Progress"
        
        cgpa_str = f"{cgpa_val:.2f}"
        sgpa_str = f"{sgpa_val:.2f}" if sgpa_val is not None else "—"
        
        message = (
            f"You're on a steady academic path 👍 (CGPA: {cgpa_str}, Latest SGPA: {sgpa_str}). "
            f"Consistent study habits across current coursework will help you advance towards academic distinction."
        )
        outlook_message = (
            f"Consistent academic performance across {completed_sems} completed semesters with a clear record."
        )

    # State 4: Strong & Consistent Performance (CGPA >= 7.5, stable trend, 0 backlogs)
    elif cgpa_val is not None and cgpa_val >= 7.5 and trend == "stable" and backlogs == 0:
        badge = "DISTINCTION STANDING" if cgpa_val >= 8.5 else "STRONG STANDING"
        headline = "Strong & Consistent Performance"
        state = "strong_consistent"
        standing_label = "Distinction standing" if cgpa_val >= 8.5 else "First Class with Distinction"
        outlook_status = "Consistent High Standing"
        
        cgpa_str = f"{cgpa_val:.2f}"
        sgpa_str = f"{sgpa_val:.2f}" if sgpa_val is not None else "—"
        
        message = (
            f"You're maintaining a strong and consistent academic record 👍 (CGPA: {cgpa_str}, Latest SGPA: {sgpa_str}). "
            f"Keep up your disciplined coursework preparation to sustain high academic achievement."
        )
        outlook_message = (
            f"Maintaining strong academic performance with CGPA {cgpa_str} across {completed_sems} completed semesters."
        )

    # State 5: Strong Academic Momentum (CGPA >= 7.5, improving trend, 0 backlogs)
    elif cgpa_val is not None and cgpa_val >= 7.5 and backlogs == 0:
        badge = "STRONG MOMENTUM" if cgpa_val < 8.5 else "DISTINCTION STANDING"
        headline = "Strong Academic Momentum"
        state = "strong_momentum"
        standing_label = "Distinction standing" if cgpa_val >= 8.5 else "First Class with Distinction"
        outlook_status = "Positive Trajectory"
        
        cgpa_str = f"{cgpa_val:.2f}"
        sgpa_str = f"{sgpa_val:.2f}" if sgpa_val is not None else "—"
        
        message = (
            f"You're building strong momentum 🌟 Your historical academic performance is strong with an improving trajectory "
            f"(CGPA: {cgpa_str}, Latest SGPA: {sgpa_str}). Maintaining consistent study habits will keep you on track for academic distinction."
        )
        outlook_message = (
            f"Maintaining distinction performance with CGPA {cgpa_str} across {completed_sems} completed semesters."
        )

    # Default / New Semester
    else:
        badge = "ACTIVE PROFILE"
        headline = "Academic Profile Active"
        state = "active_profile"
        standing_label = "Enrolled"
        outlook_status = "Active Standing"
        message = "Your academic profile is active. Stay engaged with lectures and coursework as examination records are published."
        outlook_message = "Active standing evaluated from completed semester examinations."

    return {
        "state": state,
        "badge": badge,
        "headline": headline,
        "standing_label": standing_label,
        "outlook_status": outlook_status,
        "message": message,
        "outlook_message": outlook_message,
        "trajectory": trend,
        "early_semester_note": "Current-semester attendance and assessment records are pending faculty publication."
    }
