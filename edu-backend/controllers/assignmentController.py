from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from datetime import date
from pathlib import Path
from uuid import uuid4
import os
import uuid
from math import ceil

def get_assignments(
    db: Session,
    department: str,
    semester: int,
    section: str,
    subject_code: str
):
    result = db.execute(
        text("""
            SELECT
                a.id,
                a.department,
                a.semester,
                a.section,
                a.subject_code,
                a.assignment_name,
                a.max_marks,
                a.due_date,
                a.created_at,
                a.resource_name,
                a.resource_url,
                (
                    SELECT COUNT(*)
                    FROM assignment_submissions sub
                    WHERE sub.assignment_id = a.id
                      AND sub.submission_status IN ('submitted', 'late', 'graded')
                ) AS submitted_count
            FROM assignments a
            WHERE a.department = :department
              AND a.semester = :semester
              AND a.section = :section
              AND a.subject_code = :subject_code
            ORDER BY a.created_at DESC
        """),
        {
            "department": department,
            "semester": semester,
            "section": section,
            "subject_code": subject_code,
        },
    )

    rows = result.mappings().all()

    return {
        "assignments": [dict(row) for row in rows]
    }


async def create_assignment(
    db: Session,
    user_id: int,
    department: str,
    semester: int,
    section: str,
    subject_code: str,
    assignment_name: str,
    max_marks: float,
    due_date: date,
    resource: UploadFile | None = None
):
    teacher_row = db.execute(
        text("""
            SELECT id
            FROM teachers
            WHERE user_id = :uid
        """),
        {"uid": user_id},
    ).mappings().first()

    if teacher_row is None:
        raise HTTPException(
            status_code=403,
            detail="Teacher record not found for this user"
        )

    teacher_id = teacher_row["id"]
    resource_name = None
    resource_url = None

    # Handle resource file
    if resource is not None and getattr(resource, "filename", None):
        allowed_types = {
            "application/pdf",
            "image/jpeg",
            "image/png",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }

        extension = Path(resource.filename).suffix.lower()
        allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}

        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Allowed: PDF, JPG, PNG, DOC, DOCX"
            )

        upload_dir = Path("uploads/assignments")
        upload_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid4().hex}{extension}"
        file_path = upload_dir / filename

        contents = await resource.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size must be less than 10 MB"
            )

        with open(file_path, "wb") as f:
            f.write(contents)

        resource_name = resource.filename
        resource_url = f"/uploads/assignments/{filename}"

    result = db.execute(
        text("""
            INSERT INTO assignments
                (
                    department,
                    semester,
                    section,
                    subject_code,
                    created_by,
                    assignment_name,
                    max_marks,
                    due_date,
                    resource_name,
                    resource_url
                )
            VALUES
                (
                    :department,
                    :semester,
                    :section,
                    :subject_code,
                    :created_by,
                    :assignment_name,
                    :max_marks,
                    :due_date,
                    :resource_name,
                    :resource_url
                )
            RETURNING
                id,
                department,
                semester,
                section,
                subject_code,
                assignment_name,
                max_marks,
                due_date,
                created_at,
                resource_name,
                resource_url
        """),
        {
            "department": department,
            "semester": semester,
            "section": section,
            "subject_code": subject_code,
            "created_by": teacher_id,
            "assignment_name": assignment_name,
            "max_marks": max_marks,
            "due_date": due_date,
            "resource_name": resource_name,
            "resource_url": resource_url,
        },
    )

    row = result.mappings().first()
    if row is None:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create assignment"
        )

    db.commit()
    return dict(row)


def get_student_assignments(db: Session, user_id: int):
    student = db.execute(
        text("""
            SELECT id, department, semester, section
            FROM students
            WHERE user_id = :user_id
        """),
        {"user_id": user_id},
    ).mappings().first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student record not found"
        )

    result = db.execute(
        text("""
            SELECT
                a.id,
                a.subject_code,
                COALESCE(sub.subject_name, a.subject_code) AS subject_name,
                a.assignment_name,
                a.max_marks,
                a.due_date,
                a.created_at,
                a.resource_name,
                a.resource_url,
                s.id AS submission_id,
                s.submission_status,
                s.submission_date,
                s.marks_obtained,
                s.feedback,
                s.file_name AS sub_file_name,
                s.file_url AS sub_file_url
            FROM assignments a
            LEFT JOIN subjects sub
                ON sub.subject_code = a.subject_code
            LEFT JOIN assignment_submissions s
                ON s.assignment_id = a.id
               AND s.student_id = :student_id
            WHERE a.department = :department
              AND a.semester = :semester
              AND a.section = :section
            ORDER BY a.due_date ASC NULLS LAST, a.created_at DESC
        """),
        {
            "student_id": student["id"],
            "department": student["department"],
            "semester": student["semester"],
            "section": student["section"],
        },
    )

    rows = result.mappings().all()
    assignments = []
    today = date.today()

    for row in rows:
        marks_obtained = row["marks_obtained"]
        submission_status = row["submission_status"]
        due_date_val = row["due_date"]

        # Calculate logical status
        if marks_obtained is not None:
            status = "graded"
        elif submission_status in ("submitted", "late"):
            status = "submitted"
        elif due_date_val is not None and due_date_val < today:
            status = "overdue"
        else:
            status = "pending"

        is_locked = (due_date_val is not None and due_date_val < today) and status not in ("submitted", "graded")

        assignments.append({
            "id": row["id"],
            "subjectCode": row["subject_code"],
            "subjectName": row["subject_name"],
            "title": row["assignment_name"],
            "description": f"Assignment for {row['subject_name']}",
            "maxMarks": float(row["max_marks"]) if row["max_marks"] is not None else 0.0,
            "dueDate": row["due_date"].isoformat() if row["due_date"] else None,
            "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
            "status": status,
            "isLocked": is_locked,
            "submissionStatus": submission_status or ("not_submitted" if not is_locked else "missed"),
            "submissionDate": row["submission_date"].isoformat() if row["submission_date"] else None,
            "marks": float(marks_obtained) if marks_obtained is not None else None,
            "feedback": row["feedback"] or "",
            "submittedFile": {
                "name": row["sub_file_name"],
                "url": row["sub_file_url"]
            } if row["sub_file_url"] else None,
            "resourceName": row["resource_name"],
            "resourceUrl": row["resource_url"],
        })

    return {
        "assignments": assignments
    }


def get_one_student_assignment(db: Session, user_id: int, assignment_id: int):
    student = db.execute(
        text("""
            SELECT id, department, semester, section
            FROM students
            WHERE user_id = :user_id
        """),
        {"user_id": user_id},
    ).mappings().first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student record not found"
        )

    row = db.execute(
        text("""
            SELECT
                a.id,
                a.department,
                a.semester,
                a.section,
                a.subject_code,
                COALESCE(sub.subject_name, a.subject_code) AS subject_name,
                a.assignment_name,
                a.max_marks,
                a.due_date,
                a.created_at,
                a.resource_name,
                a.resource_url,
                s.id AS submission_id,
                s.submission_status,
                s.submission_date,
                s.marks_obtained,
                s.feedback,
                s.file_name AS sub_file_name,
                s.file_url AS sub_file_url
            FROM assignments a
            LEFT JOIN subjects sub
                ON sub.subject_code = a.subject_code
            LEFT JOIN assignment_submissions s
                ON s.assignment_id = a.id
               AND s.student_id = :student_id
            WHERE a.id = :assignment_id
              AND a.department = :department
              AND a.semester = :semester
              AND a.section = :section
        """),
        {
            "assignment_id": assignment_id,
            "student_id": student["id"],
            "department": student["department"],
            "semester": student["semester"],
            "section": student["section"],
        }
    ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found for your class"
        )

    today = date.today()
    due_date_val = row["due_date"]
    marks_obtained = row["marks_obtained"]
    submission_status = row["submission_status"]

    if marks_obtained is not None:
        status = "graded"
    elif submission_status in ("submitted", "late"):
        status = "submitted"
    elif due_date_val is not None and due_date_val < today:
        status = "overdue"
    else:
        status = "pending"

    is_locked = (due_date_val is not None and due_date_val < today) and status not in ("submitted", "graded")

    return {
        "id": row["id"],
        "subjectCode": row["subject_code"],
        "subjectName": row["subject_name"],
        "title": row["assignment_name"],
        "assignmentName": row["assignment_name"],
        "description": f"Assignment for {row['subject_name']}. Please review all questions and submit before the due date.",
        "maxMarks": float(row["max_marks"]) if row["max_marks"] is not None else 0.0,
        "dueDate": row["due_date"].isoformat() if row["due_date"] else None,
        "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
        "status": status,
        "isLocked": is_locked,
        "submissionStatus": submission_status or ("not_submitted" if not is_locked else "missed"),
        "submissionDate": row["submission_date"].isoformat() if row["submission_date"] else None,
        "marks": float(marks_obtained) if marks_obtained is not None else None,
        "marksObtained": float(marks_obtained) if marks_obtained is not None else None,
        "feedback": row["feedback"] or "",
        "submission": {
            "id": row["submission_id"],
            "status": submission_status,
            "submissionDate": row["submission_date"].isoformat() if row["submission_date"] else None,
            "marks": float(marks_obtained) if marks_obtained is not None else None,
            "feedback": row["feedback"] or "",
            "fileName": row["sub_file_name"],
            "fileUrl": row["sub_file_url"]
        } if row["submission_id"] else None,
        "submittedFile": {
            "name": row["sub_file_name"],
            "url": row["sub_file_url"]
        } if row["sub_file_url"] else None,
        "resourceName": row["resource_name"],
        "resourceUrl": row["resource_url"],
    }


async def submit_student_assignment(
    db: Session,
    user_id: int,
    assignment_id: int,
    file: UploadFile
):
    student = db.execute(
        text("""
            SELECT id, department, semester, section
            FROM students
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).mappings().first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student record not found"
        )

    assignment = db.execute(
        text("""
            SELECT
                id,
                department,
                semester,
                section,
                subject_code,
                due_date,
                max_marks
            FROM assignments
            WHERE id = :assignment_id
              AND department = :department
              AND semester = :semester
              AND section = :section
        """),
        {
            "assignment_id": assignment_id,
            "department": student["department"],
            "semester": student["semester"],
            "section": student["section"],
        }
    ).mappings().first()

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found for your class"
        )

    # STRICT DEADLINE ENFORCEMENT
    today = date.today()
    if assignment["due_date"] and today > assignment["due_date"]:
        raise HTTPException(
            status_code=400,
            detail=f"Submission closed. The deadline for this assignment was {assignment['due_date']}."
        )

    # Validate file
    allowed_types = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/x-zip-compressed",
    }

    original_name = file.filename or "submission"
    extension = Path(original_name).suffix.lower()
    allowed_exts = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".zip"}

    if extension not in allowed_exts and (file.content_type and file.content_type not in allowed_types):
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOC, DOCX, JPG, PNG, and ZIP files are allowed"
        )

    upload_dir = Path("uploads/submissions")
    upload_dir.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}{extension or '.pdf'}"
    file_path = upload_dir / unique_name

    contents = await file.read()
    if len(contents) > 15 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be below 15 MB"
        )

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    file_url = f"/uploads/submissions/{unique_name}"

    # UPSERT submission record
    existing_sub = db.execute(
        text("""
            SELECT id
            FROM assignment_submissions
            WHERE student_id = :student_id
              AND assignment_id = :assignment_id
        """),
        {"student_id": student["id"], "assignment_id": assignment_id}
    ).mappings().first()

    if existing_sub:
        db.execute(
            text("""
                UPDATE assignment_submissions
                SET submission_status = 'submitted',
                    submission_date = :submission_date,
                    file_name = :file_name,
                    file_url = :file_url,
                    file_type = :file_type,
                    created_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """),
            {
                "id": existing_sub["id"],
                "submission_date": today,
                "file_name": original_name,
                "file_url": file_url,
                "file_type": file.content_type or "application/octet-stream",
            }
        )
        sub_id = existing_sub["id"]
    else:
        result = db.execute(
            text("""
                INSERT INTO assignment_submissions (
                    student_id,
                    assignment_id,
                    submission_status,
                    submission_date,
                    marks_obtained,
                    file_name,
                    file_url,
                    file_type
                )
                VALUES (
                    :student_id,
                    :assignment_id,
                    'submitted',
                    :submission_date,
                    NULL,
                    :file_name,
                    :file_url,
                    :file_type
                )
                RETURNING id
            """),
            {
                "student_id": student["id"],
                "assignment_id": assignment_id,
                "submission_date": today,
                "file_name": original_name,
                "file_url": file_url,
                "file_type": file.content_type or "application/octet-stream",
            }
        )
        sub_id = result.scalar()

    db.commit()

    return {
        "success": True,
        "submission": {
            "id": sub_id,
            "submission_status": "submitted",
            "submission_date": today.isoformat(),
            "file_name": original_name,
            "file_url": file_url
        }
    }


def get_teacher_assignment(
    db: Session,
    user_id: int,
    assignment_id: int,
    page: int = 1,
    page_size: int = 10,
    search: str = "",
):
    teacher = db.execute(
        text("""
            SELECT id
            FROM teachers
            WHERE user_id = :user_id
        """),
        {"user_id": user_id},
    ).mappings().first()

    if teacher is None:
        raise HTTPException(
            status_code=403,
            detail="Teacher record not found"
        )

    assignment = db.execute(
        text("""
            SELECT
                a.id,
                a.department,
                a.semester,
                a.section,
                a.subject_code,
                COALESCE(sub.subject_name, a.subject_code) AS subject_name,
                a.assignment_name,
                a.max_marks,
                a.due_date,
                a.created_at,
                a.resource_name,
                a.resource_url
            FROM assignments a
            LEFT JOIN subjects sub
                ON sub.subject_code = a.subject_code
            WHERE a.id = :assignment_id
        """),
        {"assignment_id": assignment_id},
    ).mappings().first()

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    search_value = f"%{search.strip()}%"

    count_result = db.execute(
        text("""
            SELECT COUNT(*)
            FROM students s
            JOIN users u ON u.id = s.user_id
            WHERE s.department = :department
              AND s.semester = :semester
              AND s.section = :section
              AND (
                    :search = ''
                    OR s.usn ILIKE :search_value
                    OR u.full_name ILIKE :search_value
              )
        """),
        {
            "department": assignment["department"],
            "semester": assignment["semester"],
            "section": assignment["section"],
            "search": search.strip(),
            "search_value": search_value,
        },
    )

    total = count_result.scalar() or 0
    total_pages = max(1, ceil(total / page_size))
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * page_size

    rows = db.execute(
        text("""
            SELECT
                s.id AS student_id,
                s.usn,
                u.full_name AS name,
                subm.id AS submission_id,
                subm.submission_status,
                subm.submission_date,
                subm.marks_obtained,
                subm.feedback,
                subm.file_name,
                subm.file_url
            FROM students s
            JOIN users u ON u.id = s.user_id
            LEFT JOIN assignment_submissions subm
                ON subm.student_id = s.id
               AND subm.assignment_id = :assignment_id
            WHERE s.department = :department
              AND s.semester = :semester
              AND s.section = :section
              AND (
                    :search = ''
                    OR s.usn ILIKE :search_value
                    OR u.full_name ILIKE :search_value
              )
            ORDER BY s.usn
            LIMIT :page_size
            OFFSET :offset
        """),
        {
            "assignment_id": assignment_id,
            "department": assignment["department"],
            "semester": assignment["semester"],
            "section": assignment["section"],
            "search": search.strip(),
            "search_value": search_value,
            "page_size": page_size,
            "offset": offset,
        },
    ).mappings().all()

    students = []
    for row in rows:
        marks = float(row["marks_obtained"]) if row["marks_obtained"] is not None else None
        raw_status = row["submission_status"]
        if marks is not None:
            display_status = "graded"
        elif raw_status in ("submitted", "late"):
            display_status = "submitted"
        else:
            display_status = "not_submitted"

        students.append({
            "student_id": row["student_id"],
            "usn": row["usn"],
            "name": row["name"],
            "submission_id": row["submission_id"],
            "submission_status": raw_status or ("submitted" if marks is not None else None),
            "display_status": display_status,
            "submission_date": row["submission_date"].isoformat() if row["submission_date"] else None,
            "marks_obtained": marks,
            "feedback": row["feedback"] or "",
            "submission_file_name": row["file_name"],
            "submission_file_url": row["file_url"],
            "file_name": row["file_name"],
            "file_url": row["file_url"],
        })

    return {
        "assignment": dict(assignment),
        "submissions": {
            "students": students,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    }


def grade_student_submission(
    db: Session,
    user_id: int,
    assignment_id: int,
    student_id: int,
    marks_obtained: float,
    feedback: str = ""
):
    teacher = db.execute(
        text("SELECT id FROM teachers WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).mappings().first()

    if not teacher:
        raise HTTPException(status_code=403, detail="Teacher record not found")

    assignment = db.execute(
        text("SELECT id, max_marks FROM assignments WHERE id = :id"),
        {"id": assignment_id}
    ).mappings().first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    max_marks = float(assignment["max_marks"] or 100.0)
    if marks_obtained < 0 or marks_obtained > max_marks:
        raise HTTPException(
            status_code=400,
            detail=f"Marks obtained must be between 0 and {max_marks}"
        )

    # Check if submission exists
    sub = db.execute(
        text("""
            SELECT id
            FROM assignment_submissions
            WHERE assignment_id = :assignment_id
              AND student_id = :student_id
        """),
        {"assignment_id": assignment_id, "student_id": student_id}
    ).mappings().first()

    today = date.today()
    if sub:
        db.execute(
            text("""
                UPDATE assignment_submissions
                SET marks_obtained = :marks,
                    feedback = :feedback,
                    submission_status = 'graded'
                WHERE id = :id
            """),
            {
                "id": sub["id"],
                "marks": marks_obtained,
                "feedback": feedback.strip() if feedback else None,
            }
        )
    else:
        db.execute(
            text("""
                INSERT INTO assignment_submissions (
                    student_id,
                    assignment_id,
                    submission_status,
                    submission_date,
                    marks_obtained,
                    feedback
                )
                VALUES (
                    :student_id,
                    :assignment_id,
                    'graded',
                    :today,
                    :marks,
                    :feedback
                )
            """),
            {
                "student_id": student_id,
                "assignment_id": assignment_id,
                "today": today,
                "marks": marks_obtained,
                "feedback": feedback.strip() if feedback else None,
            }
        )

    db.commit()

    return {
        "success": True,
        "assignment_id": assignment_id,
        "student_id": student_id,
        "marks_obtained": marks_obtained,
        "feedback": feedback,
        "status": "graded"
    }
