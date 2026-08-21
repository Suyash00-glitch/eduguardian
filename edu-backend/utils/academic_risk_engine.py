"""
EduGuardian Academic Risk Calculation Framework
================================================
Implements the multi-signal academic risk engine with:
- Dynamic available-weight normalization across current semester indicators (attendance, quiz, assignments, LMS)
- Deep historical academic performance evaluation (CGPA, SGPA, trajectory/trend, backlogs/arrears, subject-level marks card)
- Explicit early-semester handling: when current attendance/assessments are pending faculty upload, evaluates historical academic standing with calibrated confidence ("low" / "partial")
- Plain-language explainability and SHAP-like feature contributions
"""

from typing import Dict, Any, List, Optional

CURRENT_SIGNAL_WEIGHTS = {
    "attendance": 0.35,
    "quiz": 0.30,
    "assignments": 0.20,
    "lms": 0.15
}


def calculate_academic_risk(student_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes explainable academic risk and recovery probability from a normalized StudentContext.
    Combines current-term signals (when available) with historical academic performance.
    """
    available_signals: List[str] = []
    missing_signals: List[str] = []

    # ── 1. Inspect Current Attendance Signal ──────────────────────────────
    att_data = student_context.get("attendance", {})
    attendance_val: Optional[float] = None
    if att_data.get("status") == "available" and att_data.get("value") is not None:
        attendance_val = float(att_data["value"])
        available_signals.append("attendance")
    else:
        missing_signals.append("attendance")

    # ── 2. Inspect Current Quiz / Assessment Signal ───────────────────────
    quiz_data = student_context.get("current_assessments", {})
    quiz_val: Optional[float] = None
    if quiz_data.get("status") == "available" and quiz_data.get("value") is not None:
        quiz_val = float(quiz_data["value"])
        available_signals.append("quiz")
    else:
        missing_signals.append("quiz")

    # ── 3. Inspect Current Assignment Health ─────────────────────────────
    asgn_data = student_context.get("assignments", {})
    missed_assignments: Optional[int] = None
    if asgn_data.get("status") == "available" and asgn_data.get("value") is not None:
        missed_assignments = int(asgn_data.get("missed_count", 0))
        available_signals.append("assignments")
    else:
        missing_signals.append("assignments")

    # ── 4. Inspect LMS Engagement ─────────────────────────────────────────
    lms_data = student_context.get("lms_engagement", {})
    lms_val: Optional[float] = None
    if lms_data.get("status") == "available" and lms_data.get("value") is not None:
        lms_val = float(lms_data["value"])
        available_signals.append("lms")
    else:
        missing_signals.append("lms")

    # ── 5. Inspect Historical Academic Performance & Marks Card ──────────
    hist_perf = student_context.get("historical_academic_performance", {})
    hist_semesters = student_context.get("historical_semesters", [])

    cgpa: Optional[float] = hist_perf.get("cgpa")
    latest_sgpa: Optional[float] = hist_perf.get("latest_sgpa")
    sgpa_trend: str = hist_perf.get("sgpa_trend", "insufficient_data")
    arrears_count: int = int(hist_perf.get("arrears_count", 0))
    failed_history: list = hist_perf.get("failed_subjects_history", [])
    total_sems_completed: int = int(hist_perf.get("total_semesters_completed", len(hist_semesters)))

    # Fallback to scan historical_semesters if hist_perf was empty
    if cgpa is None and hist_semesters:
        for s in reversed(hist_semesters):
            if isinstance(s, dict) and s.get("cgpa") is not None:
                cgpa = float(s["cgpa"])
                break
    if latest_sgpa is None and hist_semesters:
        for s in reversed(hist_semesters):
            if isinstance(s, dict) and s.get("sgpa") is not None:
                latest_sgpa = float(s["sgpa"])
                break

    has_historical = (cgpa is not None or latest_sgpa is not None or len(hist_semesters) > 0)

    # ── SCENARIO A: EARLY SEMESTER / CURRENT METRICS PENDING ───────────────
    # If no current-semester metrics exist (attendance/assessments pending faculty upload)
    if len(available_signals) == 0:
        if has_historical:
            # Derive explainable risk score from historical academic evidence
            hist_risk_score = 15.0  # default baseline
            hist_factors: List[str] = []

            # CGPA / Standing Evaluation
            eval_cgpa = cgpa if cgpa is not None else (latest_sgpa if latest_sgpa is not None else 7.5)

            if eval_cgpa >= 8.5:
                hist_risk_score = 8.0
                hist_factors.append(f"Distinction cumulative standing (CGPA: {eval_cgpa:.2f})")
            elif eval_cgpa >= 7.5:
                hist_risk_score = 15.0
                hist_factors.append(f"Strong academic performance (CGPA: {eval_cgpa:.2f})")
            elif eval_cgpa >= 6.5:
                hist_risk_score = 30.0
                hist_factors.append(f"Consistent academic performance (CGPA: {eval_cgpa:.2f})")
            elif eval_cgpa >= 5.5:
                hist_risk_score = 48.0
                hist_factors.append(f"Moderate cumulative performance (CGPA: {eval_cgpa:.2f})")
            else:
                hist_risk_score = 72.0
                hist_factors.append(f"Low cumulative academic performance (CGPA: {eval_cgpa:.2f})")

            # SGPA Trajectory / Trend
            if latest_sgpa is not None:
                hist_factors.append(f"Latest semester SGPA: {latest_sgpa:.2f}")

            if sgpa_trend == "improving":
                hist_risk_score = max(5.0, hist_risk_score - 8.0)
                hist_factors.append("Improving semester performance trajectory")
            elif sgpa_trend == "declining":
                hist_risk_score = min(90.0, hist_risk_score + 14.0)
                hist_factors.append("Declining SGPA trajectory in recent semesters")

            # Arrears / Backlogs check
            if arrears_count > 0:
                hist_risk_score = min(95.0, hist_risk_score + (arrears_count * 20.0))
                hist_factors.append(f"{arrears_count} historical backlog/arrear record(s) detected")

            # Classification
            if hist_risk_score >= 60.0 or arrears_count >= 2:
                risk_level = "high"
                recovery_prob = max(35.0, round(100.0 - hist_risk_score, 1))
            elif hist_risk_score >= 35.0 or arrears_count == 1:
                risk_level = "medium"
                recovery_prob = max(60.0, min(80.0, round(100.0 - hist_risk_score, 1)))
            else:
                risk_level = "low"
                recovery_prob = max(84.0, min(96.0, round(100.0 - hist_risk_score, 1)))

            support_summary = (
                f"Current-semester attendance and assessment records are not yet available; "
                f"evaluated based on historical academic performance ({'; '.join(hist_factors)})."
            )

            return {
                "risk_level": risk_level,
                "risk_score": float(round(hist_risk_score, 1)),
                "confidence": "low",
                "risk_basis": "historical_academic_performance",
                "factors": hist_factors,
                "risk_status": "evaluated_historical",
                "recovery_probability": float(recovery_prob),
                "support_signal": support_summary,
                "attendance_change": 0.0,
                "lms_activity_change": 0.0,
                "missed_assignments": 0,
                "available_signals": ["historical_academic_performance"],
                "missing_signals": missing_signals,
                "normalized_weights": {"historical_academic_performance": 1.0},
                "historical_summary": {
                    "cgpa": cgpa,
                    "latest_sgpa": latest_sgpa,
                    "sgpa_trend": sgpa_trend,
                    "arrears_count": arrears_count,
                    "total_semesters_completed": total_sems_completed,
                    "factors": hist_factors
                },
                "shap_explanation": {
                    "cgpa_contribution": round((eval_cgpa - 7.0) * 5.0, 2),
                    "trend_contribution": 5.0 if sgpa_trend == "improving" else (-5.0 if sgpa_trend == "declining" else 0.0),
                    "signals_pending": missing_signals
                }
            }

        # Neither current signals nor historical data
        return {
            "risk_level": "low",
            "risk_score": 15.0,
            "confidence": "low",
            "risk_basis": "baseline_established",
            "factors": ["Current semester academic metrics and historical records are pending"],
            "risk_status": "insufficient_data",
            "recovery_probability": 85.0,
            "support_signal": "Current semester academic metrics and historical records are pending faculty/portal upload. Academic profile is active.",
            "attendance_change": 0.0,
            "lms_activity_change": 0.0,
            "missed_assignments": 0,
            "available_signals": available_signals,
            "missing_signals": missing_signals,
            "normalized_weights": {},
            "shap_explanation": {
                "status": "baseline_established",
                "signals_pending": missing_signals
            }
        }

    # ── SCENARIO B: CURRENT SIGNALS AVAILABLE ──────────────────────────────
    available_weight_sum = sum(CURRENT_SIGNAL_WEIGHTS[s] for s in available_signals)
    normalized_weights = {
        s: round(CURRENT_SIGNAL_WEIGHTS[s] / available_weight_sum, 4)
        for s in available_signals
    }

    if len(available_signals) == 4:
        confidence = "full"
    elif len(available_signals) >= 2:
        confidence = "partial"
    else:
        confidence = "low"

    signal_risks: Dict[str, float] = {}
    factors: List[str] = []

    # Current Attendance
    if attendance_val is not None:
        if attendance_val < 65.0:
            att_risk = 90.0
            factors.append(f"Attendance ({attendance_val:.1f}%) is below 65% minimum requirement")
        elif attendance_val < 80.0:
            att_risk = 50.0
            factors.append(f"Attendance ({attendance_val:.1f}%) is in monitoring band (65-79%)")
        else:
            att_risk = 10.0
        signal_risks["attendance"] = att_risk

    # Current Quiz / Assessment
    if quiz_val is not None:
        if quiz_val < 50.0:
            quiz_risk = 85.0
            factors.append(f"Assessment average ({quiz_val:.1f}%) is below 50%")
        elif quiz_val < 75.0:
            quiz_risk = 45.0
            factors.append(f"Assessment average ({quiz_val:.1f}%) is in moderate band (50-74%)")
        else:
            quiz_risk = 10.0
        signal_risks["quiz"] = quiz_risk

    # Current Assignments
    if missed_assignments is not None:
        if missed_assignments >= 2:
            asgn_risk = 85.0
            factors.append(f"{missed_assignments} overdue/missed assignments")
        elif missed_assignments == 1:
            asgn_risk = 45.0
            factors.append("1 missed assignment recorded")
        else:
            asgn_risk = 10.0
        signal_risks["assignments"] = asgn_risk

    # Current LMS
    if lms_val is not None:
        if lms_val < 40.0:
            lms_risk = 75.0
            factors.append("LMS engagement is below recommended threshold")
        elif lms_val < 70.0:
            lms_risk = 40.0
        else:
            lms_risk = 10.0
        signal_risks["lms"] = lms_risk

    # Weighted Risk Index from current signals
    composite_risk_score = sum(
        signal_risks[s] * normalized_weights[s]
        for s in available_signals
    )

    # Contextual adjustment from historical performance if available
    risk_basis = "current_semester_signals"
    if has_historical and cgpa is not None:
        risk_basis = "current_and_historical"
        if cgpa >= 8.5:
            composite_risk_score = max(5.0, composite_risk_score - 8.0)
            factors.append(f"Historical distinction standing (CGPA: {cgpa:.2f})")
        elif cgpa < 6.0:
            composite_risk_score = min(95.0, composite_risk_score + 10.0)
            factors.append(f"Historical low cumulative standing (CGPA: {cgpa:.2f})")

    # Classification Thresholds
    if composite_risk_score >= 65.0 or (attendance_val is not None and attendance_val < 65.0) or (missed_assignments is not None and missed_assignments >= 2 and (quiz_val is not None and quiz_val < 55.0)):
        risk_level = "high"
        recovery_prob = max(30.0, round(100.0 - composite_risk_score, 1))
    elif composite_risk_score >= 38.0 or (attendance_val is not None and attendance_val < 80.0) or (missed_assignments == 1):
        risk_level = "medium"
        recovery_prob = max(60.0, min(80.0, round(100.0 - composite_risk_score, 1)))
    else:
        risk_level = "low"
        recovery_prob = max(82.0, min(96.0, round(100.0 - composite_risk_score, 1)))

    if factors:
        support_signal = f"Support recommended: {'; '.join(factors)}."
    else:
        support_signal = "Academic engagement and trajectory are consistent and on track."

    shap_explanation = {}
    for s in available_signals:
        diff = signal_risks[s] - 30.0
        shap_explanation[s] = round(diff * normalized_weights[s], 2)

    return {
        "risk_level": risk_level,
        "risk_score": float(round(composite_risk_score, 1)),
        "confidence": confidence,
        "risk_basis": risk_basis,
        "factors": factors,
        "risk_status": "evaluated",
        "recovery_probability": float(recovery_prob),
        "support_signal": support_signal,
        "attendance_change": -5.0 if (attendance_val and attendance_val < 75) else 2.0,
        "lms_activity_change": -8.0 if (lms_val and lms_val < 50) else 4.0,
        "missed_assignments": missed_assignments if missed_assignments is not None else 0,
        "available_signals": available_signals,
        "missing_signals": missing_signals,
        "normalized_weights": normalized_weights,
        "shap_explanation": shap_explanation
    }
