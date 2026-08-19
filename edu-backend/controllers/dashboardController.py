from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException


def get_dashboard_summary(db: Session, user_id: int):

    # -------------------------
    # GET STUDENT
    # -------------------------
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


    # -------------------------
    # ATTENDANCE
    # -------------------------
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
        attendance_percentage = round(
            (attended_classes / total_classes) * 100,
            2
        )
    else:
        attendance_percentage = 0


    # -------------------------
    # ASSIGNMENTS
    # -------------------------
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

    missed_assignments = max(
        total_assignments - completed_assignments,
        0
    )


    # -------------------------
    # RETURN DASHBOARD DATA
    # -------------------------

    return {
        "attendance": attendance_percentage,

        # For now no historical attendance table exists
        # to calculate a real change.
        "attendanceChange": 0,

        # Until marks/quiz integration is connected.
        "averageScore": 0,
        "scoreChange": 0,

        "assignments": {
            "total": total_assignments,
            "completed": completed_assignments,
            "missed": missed_assignments,
        },

        # LMS is a separate feature.
        "lmsActivity": 0,

        # AI model can be connected later.
        "recoveryProbability": 0,

        "supportSignal": {
            "status": "Available",
            "message": "Your academic data is being analyzed."
        },
    }