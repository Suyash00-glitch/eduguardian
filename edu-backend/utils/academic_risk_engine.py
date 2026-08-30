"""
EduGuardian Predictive Academic Risk Engine
============================================
Implements a multi-horizon predictive academic risk framework combining:
1. Deep Historical Marksheet Intelligence (40% foundation weight when live data present, 100% early-semester):
   - Cumulative CGPA standing and academic band
   - Multi-semester SGPA velocity and trajectory slope
   - Active backlogs and historical cleared arrears (conceptual struggle patterns)
   - Subject-level low grade density (borderline passes D/E/P)
2. Live Current-Semester Signals (60% velocity weight):
   - Real-time Attendance % (critical leading indicator against the university 75% cutoff)
   - Continuous internal evaluation / quiz performance
   - Assignment submission regularity and LMS engagement
3. Cross-Feature Interaction & Predictive Alerting:
   - High historical vulnerability + borderline attendance triggers proactive risk escalation
   - Explainable risk attribution factors and calibrated recovery probability
"""

from typing import Dict, Any, List, Optional


CURRENT_SIGNAL_WEIGHTS = {
    "attendance": 0.40,
    "quiz": 0.30,
    "assignments": 0.15,
    "lms": 0.15
}


def _evaluate_historical_foundation(
    cgpa: Optional[float],
    latest_sgpa: Optional[float],
    sgpa_trend: str,
    arrears_count: int,
    cleared_backlogs: list,
    hist_semesters: list
) -> Dict[str, Any]:
    """
    Analyzes historical marksheets across all prior semesters to compute
    the student's foundational academic resilience score (0 = no risk, 100 = critical risk).
    """
    hist_factors: List[str] = []
    base_score = 15.0

    # 1. CGPA Cumulative Standing Evaluation
    eval_cgpa = cgpa if cgpa is not None else (latest_sgpa if latest_sgpa is not None else 7.5)

    if eval_cgpa >= 8.5:
        base_score = 8.0
        hist_factors.append(f"Distinction cumulative standing (CGPA: {eval_cgpa:.2f})")
    elif eval_cgpa >= 7.5:
        base_score = 16.0
        hist_factors.append(f"First-class academic standing (CGPA: {eval_cgpa:.2f})")
    elif eval_cgpa >= 6.5:
        base_score = 32.0
        hist_factors.append(f"Consistent cumulative standing (CGPA: {eval_cgpa:.2f})")
    elif eval_cgpa >= 5.5:
        base_score = 52.0
        hist_factors.append(f"Moderate cumulative standing (CGPA: {eval_cgpa:.2f}) — subject strengthening advised")
    else:
        base_score = 74.0
        hist_factors.append(f"Low cumulative foundation (CGPA: {eval_cgpa:.2f}) — high foundational vulnerability")

    # 2. SGPA Multi-Semester Trajectory
    if latest_sgpa is not None:
        hist_factors.append(f"Latest completed semester SGPA: {latest_sgpa:.2f}")

    if sgpa_trend == "improving":
        base_score = max(5.0, base_score - 8.0)
        hist_factors.append("Positive SGPA recovery trajectory across recent terms")
    elif sgpa_trend == "declining":
        base_score = min(92.0, base_score + 14.0)
        hist_factors.append("Declining SGPA trajectory across consecutive semesters")

    # 3. Active Backlogs & Arrears
    if arrears_count > 0:
        base_score = min(96.0, base_score + (arrears_count * 18.0))
        hist_factors.append(f"{arrears_count} active uncleared backlog/arrear(s)")

    # 4. Cleared Historical Backlogs (Summer / Supplementary sessions)
    cleared_count = len(cleared_backlogs) if isinstance(cleared_backlogs, list) else 0
    if cleared_count > 0:
        # Prior failures, even if cleared, indicate foundational vulnerability in technical prerequisites
        cleared_penalty = min(22.0, cleared_count * 5.5)
        base_score = min(90.0, base_score + cleared_penalty)
        hist_factors.append(
            f"{cleared_count} prior subject failure(s) cleared in Summer/Supplementary exams"
        )

    # 5. Deep Marksheet Inspection: Low-grade density (D / E / P / GP <= 5.0)
    low_grade_count = 0
    for sem in hist_semesters:
        if isinstance(sem, dict):
            for sub in sem.get("subject_results", []):
                if isinstance(sub, dict):
                    gp = sub.get("grade_point")
                    grade = str(sub.get("grade") or "").upper()
                    if (gp is not None and 0 < gp <= 5.0) or grade in ("D", "E", "P", "PASS"):
                        low_grade_count += 1

    if low_grade_count >= 4:
        base_score = min(92.0, base_score + 8.0)
        hist_factors.append(f"{low_grade_count} historical borderline pass grades (Grade Point ≤ 5.0)")

    return {
        "foundation_risk_score": float(round(base_score, 1)),
        "eval_cgpa": eval_cgpa,
        "arrears_count": arrears_count,
        "cleared_count": cleared_count,
        "low_grade_count": low_grade_count,
        "factors": hist_factors
    }


def calculate_academic_risk(student_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes predictive, explainable academic risk and recovery probability.
    Synthesizes historical marksheet foundation with current live signals.
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

    # ── 5. Inspect Historical Academic Performance & Marksheets ──────────
    hist_perf = student_context.get("historical_academic_performance", {})
    hist_semesters = student_context.get("historical_semesters", [])

    cgpa: Optional[float] = hist_perf.get("cgpa")
    latest_sgpa: Optional[float] = hist_perf.get("latest_sgpa")
    sgpa_trend: str = hist_perf.get("sgpa_trend", "insufficient_data")
    arrears_count: int = int(hist_perf.get("arrears_count", 0))
    cleared_backlogs: list = hist_perf.get("cleared_backlogs", [])
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

    # Compute Historical Foundation Metrics
    hist_eval = _evaluate_historical_foundation(
        cgpa=cgpa,
        latest_sgpa=latest_sgpa,
        sgpa_trend=sgpa_trend,
        arrears_count=arrears_count,
        cleared_backlogs=cleared_backlogs,
        hist_semesters=hist_semesters
    )
    hist_foundation_score = hist_eval["foundation_risk_score"]
    hist_factors = hist_eval["factors"]

    # ── SCENARIO A: EARLY SEMESTER / LIVE SIGNALS NOT YET UPLOADED ────────
    if len(available_signals) == 0:
        if has_historical:
            # Calibrate risk classification from historical marksheet foundation
            if hist_foundation_score >= 60.0 or arrears_count >= 2:
                risk_level = "high"
                recovery_prob = max(35.0, round(100.0 - hist_foundation_score, 1))
            elif hist_foundation_score >= 35.0 or arrears_count == 1 or len(cleared_backlogs) >= 2:
                risk_level = "medium"
                recovery_prob = max(58.0, min(80.0, round(100.0 - hist_foundation_score, 1)))
            else:
                risk_level = "low"
                recovery_prob = max(84.0, min(96.0, round(100.0 - hist_foundation_score, 1)))

            support_summary = (
                f"Predictive baseline evaluated from historical marksheets: {'; '.join(hist_factors)}. "
                f"Current semester attendance and internal evaluations are pending."
            )

            return {
                "risk_level": risk_level,
                "risk_score": float(round(hist_foundation_score, 1)),
                "confidence": "low",
                "risk_basis": "historical_marksheets_foundation",
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
                    "cleared_backlogs_count": len(cleared_backlogs),
                    "total_semesters_completed": total_sems_completed,
                    "factors": hist_factors
                },
                "shap_explanation": {
                    "cgpa_contribution": round((hist_eval["eval_cgpa"] - 7.0) * 5.0, 2),
                    "cleared_arrears_contribution": round(len(cleared_backlogs) * 4.0, 2),
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
            "support_signal": "Academic profile is active. Historical records and live attendance pending.",
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

    # ── SCENARIO B: LIVE SIGNALS AVAILABLE (PREDICTIVE SYNTHESIS) ─────────
    # 1. Compute Live Signals Velocity Score
    available_weight_sum = sum(CURRENT_SIGNAL_WEIGHTS[s] for s in available_signals)
    normalized_weights = {
        s: round(CURRENT_SIGNAL_WEIGHTS[s] / available_weight_sum, 4)
        for s in available_signals
    }

    signal_risks: Dict[str, float] = {}
    live_factors: List[str] = []

    # Current Attendance Risk (Institutional 75% Threshold Alignment)
    if attendance_val is not None:
        if attendance_val < 65.0:
            att_risk = 92.0
            live_factors.append(f"Critical attendance shortage ({attendance_val:.1f}%) — severe detention risk (<65%)")
        elif attendance_val < 75.0:
            att_risk = 76.0
            live_factors.append(f"Attendance ({attendance_val:.1f}%) is below mandatory university 75% cutoff")
        elif attendance_val < 85.0:
            att_risk = 42.0
            live_factors.append(f"Attendance ({attendance_val:.1f}%) is in monitoring band (75–84%)")
        else:
            att_risk = 10.0
            live_factors.append(f"Healthy attendance standing ({attendance_val:.1f}%)")
        signal_risks["attendance"] = att_risk

    # Current Quiz / Assessments Risk
    if quiz_val is not None:
        if quiz_val < 45.0:
            quiz_risk = 88.0
            live_factors.append(f"Current internal assessment average ({quiz_val:.1f}%) is below passing standard (45%)")
        elif quiz_val < 65.0:
            quiz_risk = 48.0
            live_factors.append(f"Current internal assessment average ({quiz_val:.1f}%) is moderate (45–64%)")
        else:
            quiz_risk = 10.0
        signal_risks["quiz"] = quiz_risk

    # Current Assignments Risk
    if missed_assignments is not None:
        if missed_assignments >= 2:
            asgn_risk = 85.0
            live_factors.append(f"{missed_assignments} overdue/missed assignments recorded")
        elif missed_assignments == 1:
            asgn_risk = 45.0
            live_factors.append("1 missed assignment recorded")
        else:
            asgn_risk = 10.0
        signal_risks["assignments"] = asgn_risk

    # Current LMS Engagement Risk
    if lms_val is not None:
        if lms_val < 40.0:
            lms_risk = 75.0
            live_factors.append("LMS digital engagement is below recommended active threshold")
        elif lms_val < 70.0:
            lms_risk = 40.0
        else:
            lms_risk = 10.0
        signal_risks["lms"] = lms_risk

    # Weighted Live Score
    live_signals_score = sum(
        signal_risks[s] * normalized_weights[s]
        for s in available_signals
    )

    # 2. Predictive Multi-Horizon Fusion (Historical Foundation + Live Velocity)
    if has_historical:
        # Synthesize 40% Historical Foundation + 60% Live Current Velocity
        fused_risk_score = (0.40 * hist_foundation_score) + (0.60 * live_signals_score)
        risk_basis = "predictive_multivariate (historical_marksheets + live_signals)"
        combined_factors = live_factors + hist_factors
    else:
        fused_risk_score = live_signals_score
        risk_basis = "live_semester_signals"
        combined_factors = live_factors

    # 3. Cross-Feature Interaction Rules & Escalation Multipliers
    # Multiplier 1: Low Historical Foundation (CGPA < 5.8) + Sub-75% Attendance
    if (cgpa is not None and cgpa < 5.8) and (attendance_val is not None and attendance_val < 75.0):
        fused_risk_score = min(98.0, max(fused_risk_score, 82.0))
        combined_factors.insert(0, "Compound Risk Alert: Low historical CGPA combined with attendance shortage")

    # Multiplier 2: Cleared Prior Backlogs + Attendance < 80%
    if len(cleared_backlogs) >= 2 and (attendance_val is not None and attendance_val < 80.0):
        fused_risk_score = min(92.0, max(fused_risk_score, 62.0))
        combined_factors.insert(0, "Vulnerability Alert: Multiple prior subject failures and borderline attendance")

    # Multiplier 3: High Distinction Standing (CGPA >= 8.5) + Attendance >= 85%
    if (cgpa is not None and cgpa >= 8.5) and (attendance_val is not None and attendance_val >= 85.0):
        fused_risk_score = min(fused_risk_score, 12.0)

    # 4. Final Calibrated Classification
    if fused_risk_score >= 60.0 or (attendance_val is not None and attendance_val < 65.0) or (arrears_count >= 2):
        risk_level = "high"
        recovery_prob = max(30.0, round(100.0 - fused_risk_score, 1))
    elif fused_risk_score >= 35.0 or (attendance_val is not None and attendance_val < 75.0) or (arrears_count == 1):
        risk_level = "medium"
        recovery_prob = max(58.0, min(80.0, round(100.0 - fused_risk_score, 1)))
    else:
        risk_level = "low"
        recovery_prob = max(84.0, min(96.0, round(100.0 - fused_risk_score, 1)))

    # Confidence calibration
    if len(available_signals) >= 3 and has_historical:
        confidence = "full"
    elif len(available_signals) >= 1 or has_historical:
        confidence = "partial"
    else:
        confidence = "low"

    if combined_factors:
        support_signal = f"Predictive assessment: {'; '.join(combined_factors[:4])}."
    else:
        support_signal = "Academic engagement and marksheet trajectory are consistent and on track."

    shap_explanation = {}
    for s in available_signals:
        diff = signal_risks[s] - 30.0
        shap_explanation[s] = round(diff * normalized_weights[s], 2)

    if has_historical:
        shap_explanation["historical_foundation"] = round((hist_foundation_score - 30.0) * 0.40, 2)

    return {
        "risk_level": risk_level,
        "risk_score": float(round(fused_risk_score, 1)),
        "confidence": confidence,
        "risk_basis": risk_basis,
        "factors": combined_factors,
        "risk_status": "evaluated_predictive",
        "recovery_probability": float(recovery_prob),
        "support_signal": support_signal,
        "attendance_change": -5.0 if (attendance_val and attendance_val < 75) else 2.0,
        "lms_activity_change": -8.0 if (lms_val and lms_val < 50) else 4.0,
        "missed_assignments": missed_assignments if missed_assignments is not None else 0,
        "available_signals": available_signals,
        "missing_signals": missing_signals,
        "normalized_weights": normalized_weights,
        "historical_summary": {
            "cgpa": cgpa,
            "latest_sgpa": latest_sgpa,
            "sgpa_trend": sgpa_trend,
            "arrears_count": arrears_count,
            "cleared_backlogs_count": len(cleared_backlogs),
            "total_semesters_completed": total_sems_completed,
            "factors": hist_factors
        },
        "shap_explanation": shap_explanation
    }

