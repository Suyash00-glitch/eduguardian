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
            FROM assignments
            WHERE department = :department
              AND semester = :semester
              AND section = :section
              AND subject_code = :subject_code
            ORDER BY created_at DESC
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
    resource: UploadFile | None
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
            detail="teacher record not found for this user"
        )

    teacher_id = teacher_row["id"]

    resource_name = None
    resource_url = None

    # -----------------------------
    # HANDLE RESOURCE FILE
    # -----------------------------

    if resource is not None:

        allowed_types = {
            "application/pdf",
            "image/jpeg",
            "image/png"
        }

        if resource.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, JPG, JPEG and PNG files are allowed"
            )

        extension = Path(resource.filename).suffix.lower()

        allowed_extensions = {
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png"
        }

        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type"
            )

        # Create upload directory
        upload_dir = Path("uploads/assignments")
        upload_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # Unique filename
        filename = f"{uuid4().hex}{extension}"

        file_path = upload_dir / filename

        # Save file
        contents = await resource.read()

        # 10 MB limit
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size must be less than 10 MB"
            )

        with open(file_path, "wb") as f:
            f.write(contents)

        resource_name = resource.filename
        resource_url = f"/uploads/assignments/{filename}"

    # -----------------------------
    # CREATE ASSIGNMENT
    # -----------------------------

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
            detail="failed to create assignment"
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
            detail="student record not found"
        )

    result = db.execute(
        text("""
            SELECT
                a.id,
                a.subject_code,
                a.assignment_name,
                a.max_marks,
                a.due_date,
                a.created_at,
                a.resource_name,
                a.resource_url,

                s.submission_status,
                s.submission_date,
                s.marks_obtained

            FROM assignments a

            LEFT JOIN LATERAL (
                SELECT
                    submission_status,
                    submission_date,
                    marks_obtained
                FROM assignment_submissions
                WHERE student_id = :student_id
                  AND subject_code = a.subject_code
                  AND assignment_name = a.assignment_name
                ORDER BY created_at DESC
                LIMIT 1
            ) s ON TRUE

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

    for row in rows:
        submission_status = row["submission_status"]
        due_date = row["due_date"]

        if submission_status in ("submitted", "late"):
            status = "submitted"
        elif submission_status == "missed":
            status = "overdue"
        elif due_date is not None and due_date < date.today():
            status = "overdue"
        else:
            status = "pending"

        assignments.append({
            "id": row["id"],
            "subjectCode": row["subject_code"],
            "subjectName": row["subject_code"],
            "title": row["assignment_name"],
            "description": "",
            "maxMarks": float(row["max_marks"]) if row["max_marks"] is not None else 0,
            "dueDate": row["due_date"],
            "status": status,
            "submissionStatus": submission_status,
            "submissionDate": row["submission_date"],
            "marks": (
                float(row["marks_obtained"])
                if row["marks_obtained"] is not None
                else None
            ),
            "resourceName": row["resource_name"],
            "resourceUrl": row["resource_url"],
        })

    return {
        "assignments": assignments
    }

def get_student_assignment(
    db: Session,
    user_id: int,
    assignment_id: int,
    page: int = 1,
    page_size: int = 10,
    search: str = ""
):
    teacher = db.execute(
        text("""
            SELECT t.id
            FROM teachers t
            WHERE t.user_id = :user_id
        """),
        {"user_id": user_id}
    ).mappings().first()

    if not teacher:
        raise HTTPException(
            status_code=403,
            detail="Teacher record not found"
        )

    teacher_id = teacher["id"]

    assignment = db.execute(
        text("""
            SELECT
                a.id,
                a.department,
                a.semester,
                a.section,
                a.subject_code,
                s.subject_name,
                a.assignment_name,
                a.max_marks,
                a.due_date,
                a.created_at,
                a.resource_name,
                a.resource_url
            FROM assignments a
            LEFT JOIN subjects s
                ON s.subject_code = a.subject_code
            WHERE a.id = :assignment_id
              AND a.created_by = :teacher_id
        """),
        {
            "assignment_id": assignment_id,
            "teacher_id": teacher_id
        }
    ).mappings().first()

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    search_value = f"%{search.strip()}%"

    total_result = db.execute(
        text("""
            SELECT COUNT(*)
            FROM students st
            WHERE st.department = :department
              AND st.semester = :semester
              AND st.section = :section
              AND (
                    :search = '%%'
                    OR st.usn ILIKE :search
                    OR EXISTS (
                        SELECT 1
                        FROM users u
                        WHERE u.id = st.user_id
                          AND u.full_name ILIKE :search
                    )
              )
        """),
        {
            "department": assignment["department"],
            "semester": assignment["semester"],
            "section": assignment["section"],
            "search": search_value
        }
    )

    total = total_result.scalar() or 0

    offset = (page - 1) * page_size

    result = db.execute(
        text("""
            SELECT
                st.id AS student_id,
                st.usn,
                u.full_name AS name,

                sub.id AS submission_id,
                sub.submission_status,
                sub.submission_date,
                sub.marks_obtained,

                sub.file_name AS submission_file_name,
                sub.file_url AS submission_file_url,
                sub.file_type AS submission_file_type

            FROM students st

            JOIN users u
                ON u.id = st.user_id

            LEFT JOIN assignment_submissions sub
                ON sub.student_id = st.id
               AND sub.assignment_id = :assignment_id

            WHERE st.department = :department
              AND st.semester = :semester
              AND st.section = :section

              AND (
                    :search = '%%'
                    OR st.usn ILIKE :search
                    OR u.full_name ILIKE :search
              )

            ORDER BY st.usn

            LIMIT :page_size
            OFFSET :offset
        """),
        {
            "assignment_id": assignment_id,
            "department": assignment["department"],
            "semester": assignment["semester"],
            "section": assignment["section"],
            "search": search_value,
            "page_size": page_size,
            "offset": offset
        }
    )

    students = [dict(row) for row in result.mappings().all()]

    total_pages = max(
        1,
        (total + page_size - 1) // page_size
    )

    return {
        "assignment": dict(assignment),
        "submissions": {
            "students": students,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    }

async def submit_student_assignment(
    db: Session,
    user_id: int,
    assignment_id: int,
    file: UploadFile
):
    # -----------------------------
    # Find student
    # -----------------------------
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
            detail="student record not found"
        )

    # -----------------------------
    # Find assignment
    # -----------------------------
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
            detail="assignment not found"
        )

    # -----------------------------
    # Validate file
    # -----------------------------
    allowed_types = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, JPG, PNG, DOC and DOCX files are allowed"
        )

    # -----------------------------
    # Save file
    # -----------------------------
    upload_dir = Path("uploads/submissions")
    upload_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    original_name = file.filename or "submission"

    extension = Path(original_name).suffix

    unique_name = (
        f"{uuid.uuid4().hex}{extension}"
    )

    file_path = upload_dir / unique_name

    contents = await file.read()

    # 10 MB limit
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be below 10 MB"
        )

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    file_url = f"/uploads/submissions/{unique_name}"

    # -----------------------------
    # Determine late/submitted
    # -----------------------------
    today = date.today()

    if assignment["due_date"] and today > assignment["due_date"]:
        submission_status = "late"
    else:
        submission_status = "submitted"

    # -----------------------------
    # Insert submission
    # -----------------------------
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
                :submission_status,
                :submission_date,
                NULL,
                :file_name,
                :file_url,
                :file_type
            )
            RETURNING
                id,
                submission_status,
                submission_date,
                file_name,
                file_url,
                file_type
        """),
        {
            "student_id": student["id"],
            "assignment_id": assignment_id,
            "submission_status": submission_status,
            "submission_date": today,
            "file_name": original_name,
            "file_url": file_url,
            "file_type": file.content_type,
        }
    )

    row = result.mappings().first()

    db.commit()

    return {
        "success": True,
        "submission": dict(row)
    }

def get_teacher_assignment(
    db: Session,
    user_id: int,
    assignment_id: int,
    page: int = 1,
    page_size: int = 10,
    search: str = "",
):
    # Get teacher ID
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

    teacher_id = teacher["id"]

    # Get assignment
    assignment = db.execute(
        text("""
            SELECT
                a.id,
                a.department,
                a.semester,
                a.section,
                a.subject_code,
                sub.subject_name,
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
              AND a.created_by = :teacher_id
        """),
        {
            "assignment_id": assignment_id,
            "teacher_id": teacher_id,
        },
    ).mappings().first()

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    # Search
    search_value = f"%{search.strip()}%"

    # Count students
    count_result = db.execute(
        text("""
            SELECT COUNT(*)
            FROM students s
            WHERE s.department = :department
              AND s.semester = :semester
              AND s.section = :section
              AND (
                    :search = ''
                    OR s.usn ILIKE :search_value
                    OR EXISTS (
                        SELECT 1
                        FROM users u
                        WHERE u.id = s.user_id
                          AND u.full_name ILIKE :search_value
                    )
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

    # Get students + submission
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
                subm.file_name,
                subm.file_url

            FROM students s

            JOIN users u
                ON u.id = s.user_id

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
        students.append({
            "student_id": row["student_id"],
            "usn": row["usn"],
            "name": row["name"],

            "submission_id": row["submission_id"],
            "submission_status": row["submission_status"],
            "submission_date": row["submission_date"],

            "marks_obtained": (
                float(row["marks_obtained"])
                if row["marks_obtained"] is not None
                else None
            ),

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

