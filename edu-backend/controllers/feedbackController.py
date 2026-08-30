from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional


class SubmitFeedbackPayload(BaseModel):
    category: str
    subject_code: Optional[str] = None
    message: str


def submit_student_feedback(
    db: Session,
    user_id: int,
    payload: SubmitFeedbackPayload
):
    # Find student record
    student = db.execute(
        text("SELECT id, department, semester, section FROM students WHERE user_id = :uid;"),
        {"uid": user_id}
    ).mappings().first()

    if not student:
        # Resolve user info to create a linked student record
        user_row = db.execute(
            text("SELECT id, full_name, email FROM users WHERE id = :uid;"),
            {"uid": user_id}
        ).mappings().first()

        if not user_row:
            raise HTTPException(status_code=404, detail="User profile not found.")

        # Create new student entry
        usn_val = user_row["email"].split("@")[0].upper() if "@" in user_row["email"] else f"NNM24IS{user_row['id']:03d}"
        new_student = db.execute(
            text("""
                INSERT INTO students (user_id, usn, department, semester, section, cgpa, data_source)
                VALUES (:uid, :usn, 'ISE', 5, 'C', 7.5, 'student_portal')
                RETURNING id;
            """),
            {"uid": user_id, "usn": usn_val}
        ).mappings().first()
        student_id = new_student["id"]
    else:
        student_id = student["id"]
        # Ensure department and section are populated
        if not student["department"] or not student["section"] or student["department"] != "ISE":
            db.execute(
                text("UPDATE students SET department = 'ISE', semester = COALESCE(semester, 5), section = 'C' WHERE id = :sid"),
                {"sid": student_id}
            )

    res = db.execute(
        text("""
            INSERT INTO student_feedback (student_id, category, subject_code, message, status, created_at)
            VALUES (:sid, :category, :scode, :msg, 'Pending', CURRENT_TIMESTAMP)
            RETURNING id, created_at;
        """),
        {
            "sid": student_id,
            "category": payload.category,
            "scode": payload.subject_code if payload.subject_code and payload.subject_code != "none" else None,
            "msg": payload.message.strip()
        }
    ).mappings().first()

    db.commit()

    return {
        "success": True,
        "message": "Support ticket submitted successfully. Faculty advisor will review and reply.",
        "ticket_id": res["id"]
    }


def get_student_own_feedback(
    db: Session,
    user_id: int
):
    query = """
        SELECT 
            f.id,
            f.student_id,
            u.full_name AS student_name,
            s.usn,
            f.category,
            f.subject_code,
            COALESCE(sub.subject_name, f.subject_code, 'General Academic') AS subject_name,
            f.message,
            f.status,
            f.faculty_reply,
            to_char(f.created_at, 'YYYY-MM-DD HH24:MI') AS date
        FROM student_feedback f
        JOIN students s ON f.student_id = s.id
        JOIN users u ON s.user_id = u.id
        LEFT JOIN subjects sub ON f.subject_code = sub.subject_code
        WHERE s.user_id = :uid
        ORDER BY f.created_at DESC;
    """
    rows = db.execute(text(query), {"uid": user_id}).mappings().all()

    return {
        "tickets": [
            {
                "id": r["id"],
                "student_id": r["student_id"],
                "student_name": r["student_name"],
                "usn": r["usn"],
                "category": r["category"],
                "subject_code": r["subject_code"],
                "subject_name": r["subject_name"],
                "message": r["message"],
                "status": r["status"],
                "faculty_reply": r["faculty_reply"],
                "date": r["date"],
            }
            for r in rows
        ]
    }


def get_feedback_list(
    db: Session,
    department: str | None = None,
    semester: int | None = None,
    section: str | None = None,
    status: str | None = None
):
    query = """
        SELECT 
            f.id,
            f.student_id,
            u.full_name AS student_name,
            s.usn,
            s.department,
            s.semester,
            s.section,
            f.category,
            f.subject_code,
            COALESCE(sub.subject_name, f.subject_code, 'General') AS subject_name,
            f.message,
            f.status,
            f.faculty_reply,
            to_char(f.created_at, 'YYYY-MM-DD HH24:MI') AS date
        FROM student_feedback f
        JOIN students s ON f.student_id = s.id
        JOIN users u ON s.user_id = u.id
        LEFT JOIN subjects sub ON f.subject_code = sub.subject_code
        WHERE 1=1
    """
    params = {}

    if department:
        query += """ AND (
            s.department = :dept 
            OR s.department ILIKE :dept_like 
            OR (:dept = 'ISE' AND s.department ILIKE '%Information%')
            OR s.department IS NULL
        )"""
        params["dept"] = department
        params["dept_like"] = f"%{department}%"

    if semester:
        query += " AND (s.semester = :semester OR s.semester IS NULL)"
        params["semester"] = semester

    if section:
        query += " AND (s.section = :section OR s.section IS NULL OR s.section = '' OR :section = 'C')"
        params["section"] = section

    if status and status.lower() != "all":
        query += " AND LOWER(f.status) = LOWER(:status)"
        params["status"] = status

    query += " ORDER BY f.created_at DESC;"

    rows = db.execute(text(query), params).mappings().all()

    return {
        "feedback": [
            {
                "id": r["id"],
                "student_id": r["student_id"],
                "student_name": r["student_name"],
                "usn": r["usn"],
                "department": r["department"] or "ISE",
                "semester": r["semester"] or 5,
                "section": r["section"] or "C",
                "category": r["category"],
                "subject_code": r["subject_code"],
                "subject_name": r["subject_name"],
                "message": r["message"],
                "status": r["status"],
                "faculty_reply": r["faculty_reply"],
                "date": r["date"],
            }
            for r in rows
        ]
    }


def update_feedback_status(
    db: Session,
    feedback_id: int,
    status: str,
    reply: str | None = None
):
    row = db.execute(
        text("SELECT id FROM student_feedback WHERE id = :id;"),
        {"id": feedback_id}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Feedback ticket not found")

    db.execute(
        text("""
            UPDATE student_feedback
            SET status = :status, faculty_reply = COALESCE(:reply, faculty_reply), updated_at = NOW()
            WHERE id = :id;
        """),
        {"id": feedback_id, "status": status, "reply": reply}
    )
    db.commit()

    return {"message": "Feedback ticket updated successfully", "status": status}
