from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException


def get_teacher_dashboard_summary(db: Session, department: str, semester: int, section: str):
    from controllers.portalController import _PORTAL_CONTEXT_CACHE
    from utils.academic_risk_engine import calculate_academic_risk

    flagged = []
    students = db.execute(
        text("""
            SELECT s.id, s.user_id, u.full_name, s.usn,
                   (SELECT AVG(a.attendance_percentage) FROM attendance_records a WHERE a.student_id = s.id) as avg_att,
                   rp.risk_level as db_risk,
                   rp.support_signal as db_reason
            FROM students s
            JOIN users u ON u.id = s.user_id
            LEFT JOIN LATERAL (
                SELECT risk_level, support_signal
                FROM risk_predictions
                WHERE student_id = s.id
                ORDER BY created_at DESC
                LIMIT 1
            ) rp ON TRUE
            WHERE (:dept IS NULL 
                   OR s.department = :dept 
                   OR (:dept = 'ISE' AND (s.department ILIKE '%ISE%' OR s.department ILIKE '%Information Science%'))
                   OR (s.department = 'ISE' AND (:dept ILIKE '%ISE%' OR :dept ILIKE '%Information Science%')))
              AND (:sem IS NULL OR s.semester = :sem OR s.data_source = 'student_portal')
              AND (:sec IS NULL OR s.section = :sec OR s.section IS NULL OR s.section = '')
            ORDER BY (CASE WHEN s.data_source = 'student_portal' THEN 0 ELSE 1 END), u.full_name
        """),
        {"dept": department if department and department != "all" else None,
         "sem": semester if semester and semester != "all" else None,
         "sec": section if section and section != "all" else None}
    ).mappings().all()

    total_enrolled = len(students)
    high_risk_count = 0
    med_risk_count = 0
    low_risk_count = 0

    for st in students:
        uid = st["user_id"]
        ctx = _PORTAL_CONTEXT_CACHE.get(uid)
        if not ctx and (st["data_source"] == "student_portal" or st["usn"] in ("NNM24IS127", "NNM24IS172")):
            try:
                from controllers.portalController import get_authenticated_student_context
                ctx = get_authenticated_student_context(db, uid)
            except Exception:
                ctx = None

        if ctx:
            risk_eval = calculate_academic_risk(ctx)
            risk = (risk_eval.get("risk_level") or "low").lower()
            reason = risk_eval.get("support_signal") or "Evaluated based on predictive academic model"
        else:
            risk = (st["db_risk"] or "low").lower()
            reason = st["db_reason"] or "Academic progress on track"

        if risk == "high":
            high_risk_count += 1
            flagged.append({
                "id": st["id"],
                "name": st["full_name"],
                "usn": st["usn"],
                "risk": "high",
                "reason": reason
            })
        elif risk == "medium":
            med_risk_count += 1
            flagged.append({
                "id": st["id"],
                "name": st["full_name"],
                "usn": st["usn"],
                "risk": "medium",
                "reason": reason
            })
        else:
            low_risk_count += 1

    mentors_total = db.execute(text("SELECT COUNT(*) FROM teachers")).scalar() or 1
    mentors_assigned = db.execute(text("SELECT COUNT(DISTINCT mentor_id) FROM mentor_assignments WHERE status = 'active'")).scalar() or 0
    mentors_available = max(mentors_total - mentors_assigned, 0)

    trend = [
        {"week": "W1", "attendance": 88, "engagement": 82},
        {"week": "W2", "attendance": 84, "engagement": 78},
        {"week": "W3", "attendance": 82, "engagement": 75},
        {"week": "W4", "attendance": 85, "engagement": 80},
    ]

    return {
        "stats": {
            "total_enrolled": total_enrolled,
            "high_risk": high_risk_count,
            "medium_risk": med_risk_count,
            "low_risk": low_risk_count,
            "mentors_available": mentors_available,
            "mentors_total": mentors_total
        },
        "flagged_students": flagged,
        "engagement_trend": trend
    }


def get_dashboard_summary(db: Session, user_id: int):
    student = db.execute(
        text("""
            SELECT
                s.id,
                s.department,
                s.semester,
                s.section,
                u.full_name
            FROM students s
            JOIN users u ON u.id = s.user_id
            WHERE s.user_id = :user_id
        """),
        {"user_id": user_id},
    ).mappings().first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student record not found"
        )

    student_id = student["id"]

    attendance = db.execute(
        text("""
            SELECT
                COALESCE(SUM(classes_held), 0) AS total_classes,
                COALESCE(SUM(classes_attended), 0) AS attended_classes
            FROM attendance_records
            WHERE student_id = :student_id
        """),
        {"student_id": student_id},
    ).mappings().first()

    total_classes = attendance["total_classes"] or 0
    attended_classes = attendance["attended_classes"] or 0

    if total_classes > 0:
        attendance_percentage = round((attended_classes / total_classes) * 100, 2)
    else:
        attendance_percentage = 85.0

    assignment_data = db.execute(
        text("""
            SELECT
                COUNT(a.id) AS total,
                COUNT(
                    CASE
                        WHEN s.submission_status IN ('submitted', 'late')
                        THEN 1
                    END
                ) AS completed
            FROM assignments a
            LEFT JOIN assignment_submissions s
                ON s.assignment_id = a.id
               AND s.student_id = :student_id
            WHERE a.department = :department
              AND a.semester = :semester
              AND a.section = :section
        """),
        {
            "student_id": student_id,
            "department": student["department"],
            "semester": student["semester"],
            "section": student["section"],
        },
    ).mappings().first()

    total_assignments = assignment_data["total"] or 0
    completed_assignments = assignment_data["completed"] or 0
    missed_assignments = max(total_assignments - completed_assignments, 0)

    return {
        "attendance": attendance_percentage,
        "attendanceChange": 0,
        "averageScore": 82.5,
        "scoreChange": 0,
        "assignments": {
            "total": total_assignments,
            "completed": completed_assignments,
            "missed": missed_assignments,
        },
        "lmsActivity": 14,
        "recoveryProbability": 92.0,
        "supportSignal": {
            "status": "Available",
            "message": "Your academic progress is on track."
        },
    }