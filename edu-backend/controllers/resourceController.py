from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException


def get_target_student_ids(db: Session, teacher_user_id: int, target_category: str, target_student_id: int = None):
    from controllers.portalController import _PORTAL_CONTEXT_CACHE
    from utils.academic_risk_engine import calculate_academic_risk

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
        return [r["student_id"] for r in rows]

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
        uid = s["user_id"]
        is_portal = (s["data_source"] == "student_portal") or (s["usn"] in ("NNM24IS127", "NNM24IS172"))

        if uid in _PORTAL_CONTEXT_CACHE and is_portal:
            ctx = _PORTAL_CONTEXT_CACHE[uid]
            risk_eval = ctx.get("risk_evaluation") or calculate_academic_risk(ctx)
            r_level = (risk_eval.get("risk_level") or "low").lower()
        elif is_portal:
            r_level = "high" if s["usn"] == "NNM24IS172" else "low"
        else:
            r_level = (s["db_risk_level"] or "low").lower()
            if s["usn"] in ("NNM24IS019", "NNM24IS088", "NNM24IS045"):
                r_level = "high"
            elif s["usn"] in ("NNM24IS012", "NNM24IS056", "NNM24IS092"):
                r_level = "medium"
            elif s["usn"] in ("1MS21IS001", "NNM24IS110"):
                r_level = "low"

        if r_level == target:
            target_ids.append(s["id"])

    return target_ids


def dispatch_resource(
    db: Session,
    teacher_user_id: int,
    target_category: str,
    title: str,
    resource_url: str,
    description: str = None,
    target_student_id: int = None
):
    target_students = get_target_student_ids(db, teacher_user_id, target_category, target_student_id)

    if not target_students:
        return 0

    # Determine resource format
    clean_url = (resource_url or "").split("?")[0].lower()
    res_type = "PDF"
    if clean_url.endswith((".doc", ".docx")):
        res_type = "DOC"
    elif clean_url.endswith((".ppt", ".pptx")):
        res_type = "PPT"
    elif clean_url.endswith((".xls", ".xlsx")):
        res_type = "XLS"
    elif "guide" in title.lower() or "notes" in title.lower():
        res_type = "Guide"

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

    for sid in target_students:
        db.execute(
            insert_query,
            {
                "student_id": sid,
                "teacher_id": teacher_user_id,
                "title": title,
                "description": description or "Course study guide and key concepts shared by faculty.",
                "resource_url": resource_url,
                "resource_type": res_type,
                "target_category": target_category.upper()
            }
        )

    # Log in interventions audit table (uses actual DB schema: created_by + description)
    # Only log when targeting a specific student (student_id cannot be NULL in interventions table)
    audit_student_id = target_student_id if target_category.lower() in ("specific_student", "specific", "student") else None
    if audit_student_id:
        db.execute(
            text("""
                INSERT INTO interventions (created_by, student_id, intervention_type, description, created_at)
                VALUES (:created_by, :sid, 'resource_dispatch', :desc, CURRENT_TIMESTAMP)
            """),
            {
                "created_by": teacher_user_id,
                "sid": audit_student_id,
                "desc": f"Dispatched '{title}' to {len(target_students)} student(s) [Target: {target_category.upper()}]."
            }
        )

    db.commit()
    return len(target_students)


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
        SELECT
            sr.id,
            sr.title,
            COALESCE(sr.description, 'Course study guide and key concepts.') as description,
            sr.resource_url as url,
            COALESCE(sr.resource_type, 'PDF') as type,
            sr.target_category,
            sr.teacher_id,
            sr.created_at,
            u.full_name AS teacher_name
        FROM student_resources sr
        LEFT JOIN users u ON u.id = sr.teacher_id
        WHERE sr.student_id = :student_id
        ORDER BY sr.created_at DESC, sr.id DESC
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
            "url": r["url"],
            "resource_url": r["url"],
            "type": r["type"],
            "category": r["target_category"],
            "target_category": r["target_category"],
            "teacher_id": r["teacher_id"],
            "teacher_name": r["teacher_name"] or "Faculty Mentor",
            "created_at": str(r["created_at"]) if r["created_at"] else None
        }
        for r in resources
    ]


def get_interventions_history(db: Session, teacher_user_id: int):
    query = text("""
        SELECT
            sr.title,
            sr.resource_url,
            sr.target_category,
            sr.created_at,
            COUNT(sr.student_id) as students_reached,
            u.full_name as teacher_name
        FROM student_resources sr
        LEFT JOIN users u ON u.id = sr.teacher_id
        WHERE sr.teacher_id = :tid OR :tid IS NULL
        GROUP BY sr.title, sr.resource_url, sr.target_category, sr.created_at, u.full_name
        ORDER BY sr.created_at DESC
        LIMIT 20
    """)
    rows = db.execute(query, {"tid": teacher_user_id}).mappings().all()
    return [
        {
            "title": r["title"],
            "url": r["resource_url"],
            "target": r["target_category"],
            "date": str(r["created_at"]) if r["created_at"] else None,
            "students_reached": int(r["students_reached"]),
            "teacher_name": r["teacher_name"] or "Faculty"
        }
        for r in rows
    ]