from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from pathlib import Path
from uuid import uuid4
import os
import re


def get_target_student_ids(db: Session, teacher_user_id: int, target_category: str, target_student_id: int = None):
    target = target_category.strip().lower()

    if target in ("specific_student", "specific", "student") and target_student_id:
        student = db.execute(text("SELECT id FROM students WHERE id = :sid"), {"sid": target_student_id}).mappings().first()
        return [student["id"]] if student else []

    if target in ("my_mentees", "mentees"):
        # Find teacher record
        teacher = db.execute(text("SELECT id FROM teachers WHERE user_id = :uid"), {"uid": teacher_user_id}).mappings().first()
        if not teacher:
            return []
        rows = db.execute(
            text("SELECT student_id FROM mentor_assignments WHERE mentor_id = :tid AND status = 'active'"),
            {"tid": teacher["id"]}
        ).mappings().all()
        return [r["student_id"] for r in rows if r["student_id"]]

    if target in ("all", "entire_cohort", "cohort"):
        rows = db.execute(text("SELECT id FROM students")).mappings().all()
        return [r["id"] for r in rows]

    # Risk-based targeting: HIGH, MEDIUM, LOW
    students = db.execute(
        text("""
            SELECT s.id, s.user_id, s.usn, s.data_source, rp.risk_level as db_risk_level
            FROM students s
            LEFT JOIN LATERAL (
                SELECT risk_level FROM risk_predictions WHERE student_id = s.id ORDER BY created_at DESC LIMIT 1
            ) rp ON TRUE
        """)
    ).mappings().all()

    target_ids = []
    for s in students:
        r_level = (s["db_risk_level"] or "low").lower()
        if r_level == target:
            target_ids.append(s["id"])

    return target_ids


async def dispatch_resource_with_file(
    db: Session,
    teacher_user_id: int,
    target_category: str,
    title: str,
    resource_url: str = None,
    description: str = None,
    target_student_id: int = None,
    file: UploadFile = None
):
    # Resolve teacher record ID
    teacher_row = db.execute(
        text("SELECT id FROM teachers WHERE user_id = :uid"),
        {"uid": teacher_user_id}
    ).mappings().first()
    teacher_id = teacher_row["id"] if teacher_row else teacher_user_id

    final_url = resource_url or ""
    res_type = "PDF"

    # 1. Handle File Upload if provided
    if file and file.filename:
        upload_dir = Path("uploads/resources")
        upload_dir.mkdir(parents=True, exist_ok=True)

        original_ext = Path(file.filename).suffix.lower()
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", file.filename)
        unique_filename = f"{uuid4().hex[:10]}_{safe_name}"
        file_path = upload_dir / unique_filename

        contents = await file.read()
        if len(contents) > 25 * 1024 * 1024:  # 25 MB limit
            raise HTTPException(status_code=400, detail="Uploaded file size must be less than 25 MB")

        with open(file_path, "wb") as f:
            f.write(contents)

        final_url = f"/uploads/resources/{unique_filename}"

        if original_ext in (".pdf",):
            res_type = "PDF"
        elif original_ext in (".doc", ".docx"):
            res_type = "DOC"
        elif original_ext in (".ppt", ".pptx"):
            res_type = "PPT"
        elif original_ext in (".xls", ".xlsx", ".csv"):
            res_type = "XLS"
        elif original_ext in (".zip", ".rar", ".7z", ".tar", ".gz"):
            res_type = "ZIP"
        elif original_ext in (".png", ".jpg", ".jpeg", ".webp"):
            res_type = "IMAGE"
        elif original_ext in (".py", ".js", ".java", ".c", ".cpp", ".sql", ".html"):
            res_type = "CODE"
        else:
            res_type = "DOCUMENT"
    else:
        # Detect type from URL / title
        clean_url = (final_url or "").split("?")[0].lower()
        if clean_url.endswith((".pdf",)):
            res_type = "PDF"
        elif clean_url.endswith((".doc", ".docx")):
            res_type = "DOC"
        elif clean_url.endswith((".ppt", ".pptx")):
            res_type = "PPT"
        elif clean_url.endswith((".xls", ".xlsx")):
            res_type = "XLS"
        elif "drive.google.com" in clean_url or "docs.google.com" in clean_url:
            res_type = "Drive Link"
        elif "guide" in title.lower() or "notes" in title.lower():
            res_type = "Guide"
        else:
            res_type = "Web Link"

    if not final_url:
        raise HTTPException(status_code=400, detail="Please either upload a file or provide a valid resource URL link.")

    target_norm = target_category.strip().upper()
    target_students = get_target_student_ids(db, teacher_user_id, target_category, target_student_id)

    insert_query = text("""
        INSERT INTO student_resources
        (
            student_id,
            teacher_id,
            title,
            description,
            resource_url,
            resource_type,
            target_category,
            created_at
        )
        VALUES
        (
            :student_id,
            :teacher_id,
            :title,
            :description,
            :resource_url,
            :resource_type,
            :target_category,
            CURRENT_TIMESTAMP
        )
    """)

    dispatched_count = 0

    if target_students:
        for sid in target_students:
            db.execute(
                insert_query,
                {
                    "student_id": sid,
                    "teacher_id": teacher_id,
                    "title": title,
                    "description": description or "Course learning and remedial material shared by faculty.",
                    "resource_url": final_url,
                    "resource_type": res_type,
                    "target_category": target_norm
                }
            )
            dispatched_count += 1

    # Also store cohort/general row if ALL or if no students currently in targeted cohort
    if target_norm in ("ALL", "ENTIRE_COHORT", "COHORT") or not target_students:
        db.execute(
            insert_query,
            {
                "student_id": None,
                "teacher_id": teacher_id,
                "title": title,
                "description": description or "Course learning and remedial material shared by faculty.",
                "resource_url": final_url,
                "resource_type": res_type,
                "target_category": target_norm
            }
        )
        dispatched_count = max(dispatched_count, 1)

    # Audit in interventions table if student target is specific
    audit_student_id = target_student_id if target_category.lower() in ("specific_student", "specific", "student") else (target_students[0] if len(target_students) == 1 else None)
    if audit_student_id:
        try:
            db.execute(
                text("""
                    INSERT INTO interventions (created_by, student_id, intervention_type, description, created_at)
                    VALUES (:created_by, :sid, 'resource_dispatch', :desc, CURRENT_TIMESTAMP)
                """),
                {
                    "created_by": teacher_user_id,
                    "sid": audit_student_id,
                    "desc": f"Dispatched '{title}' [Type: {res_type}, Target: {target_norm}]."
                }
            )
        except Exception:
            pass

    db.commit()
    return dispatched_count, final_url, res_type


def get_student_resources(
    db: Session,
    user_id: int
):
    # Resolve student_id if user_id is passed
    student = db.execute(
        text("SELECT id FROM students WHERE user_id = :uid"),
        {"uid": user_id}
    ).mappings().first()

    student_id = student["id"] if student else user_id

    query = text("""
        SELECT DISTINCT ON (sr.title, sr.resource_url)
            sr.id,
            sr.title,
            COALESCE(sr.description, 'Course study guide and key concepts shared by faculty.') as description,
            sr.resource_url as url,
            COALESCE(sr.resource_type, 'PDF') as type,
            sr.target_category,
            sr.teacher_id,
            sr.created_at,
            COALESCE(u.full_name, 'Faculty Advisor') AS teacher_name,
            COALESCE(t.designation, 'Faculty Advisor') AS teacher_designation,
            COALESCE(t.department, 'ISE') AS teacher_department
        FROM student_resources sr
        LEFT JOIN teachers t ON t.id = sr.teacher_id OR t.user_id = sr.teacher_id
        LEFT JOIN users u ON u.id = t.user_id OR u.id = sr.teacher_id
        WHERE sr.student_id = :student_id 
           OR sr.student_id IS NULL 
           OR sr.target_category IN ('ALL', 'ENTIRE_COHORT', 'COHORT')
        ORDER BY sr.title, sr.resource_url, sr.created_at DESC, sr.id DESC
    """)

    resources = db.execute(
        query,
        {"student_id": student_id}
    ).mappings().all()

    return [
        {
            "id": r["id"],
            "title": r["title"],
            "description": r["description"],
            "url": f"http://localhost:5000{r['url']}" if r["url"] and r["url"].startswith("/uploads") else r["url"],
            "resource_url": f"http://localhost:5000{r['url']}" if r["url"] and r["url"].startswith("/uploads") else r["url"],
            "type": r["type"],
            "category": r["target_category"],
            "target_category": r["target_category"],
            "teacher_id": r["teacher_id"],
            "teacher_name": r["teacher_name"],
            "teacher_designation": r["teacher_designation"],
            "teacher_department": r["teacher_department"],
            "created_at": str(r["created_at"]) if r["created_at"] else None
        }
        for r in resources
    ]


def get_interventions_history(db: Session, teacher_user_id: int):
    # Find teacher row
    t_row = db.execute(text("SELECT id FROM teachers WHERE user_id = :uid"), {"uid": teacher_user_id}).mappings().first()
    t_id = t_row["id"] if t_row else teacher_user_id

    query = text("""
        SELECT
            sr.title,
            sr.resource_url,
            sr.resource_type,
            sr.target_category,
            sr.created_at,
            COUNT(COALESCE(sr.student_id, 1)) as students_reached,
            COALESCE(u.full_name, 'Faculty') as teacher_name
        FROM student_resources sr
        LEFT JOIN teachers t ON t.id = sr.teacher_id OR t.user_id = sr.teacher_id
        LEFT JOIN users u ON u.id = t.user_id OR u.id = sr.teacher_id
        WHERE sr.teacher_id = :tid OR sr.teacher_id = :uid OR :tid IS NULL
        GROUP BY sr.title, sr.resource_url, sr.resource_type, sr.target_category, sr.created_at, u.full_name
        ORDER BY sr.created_at DESC
        LIMIT 30
    """)
    rows = db.execute(query, {"tid": t_id, "uid": teacher_user_id}).mappings().all()
    return [
        {
            "title": r["title"],
            "url": f"http://localhost:5000{r['resource_url']}" if r["resource_url"] and r["resource_url"].startswith("/uploads") else r["resource_url"],
            "type": r["resource_type"] or "PDF",
            "target": r["target_category"],
            "date": str(r["created_at"]) if r["created_at"] else None,
            "students_reached": max(int(r["students_reached"]), 1),
            "teacher_name": r["teacher_name"]
        }
        for r in rows
    ]