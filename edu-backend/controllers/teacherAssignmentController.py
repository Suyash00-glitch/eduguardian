from sqlalchemy import text


def get_teacher_assignments(db, user_id: int):
    teacher_row = db.execute(
        text("SELECT id FROM teachers WHERE user_id = :uid"),
        {"uid": user_id},
    ).mappings().first()

    if teacher_row is None:
        return {"assignments": []}

    teacher_id = teacher_row["id"]

    rows = db.execute(
        text("""
            SELECT
                ta.department,
                ta.semester,
                ta.section,
                ta.subject_code,
                s.subject_name,
                ta.is_class_admin
            FROM teacher_assignments ta
            LEFT JOIN subjects s ON s.subject_code = ta.subject_code
            WHERE ta.teacher_id = :teacher_id
            ORDER BY ta.is_class_admin DESC, ta.section, ta.subject_code
        """),
        {"teacher_id": teacher_id},
    ).mappings().all()

    assignments = []
    for row in rows:
        assignments.append({
            "department": row["department"],
            "semester": row["semester"],
            "section": row["section"],
            "subject_code": row["subject_code"],
            "subject_name": row["subject_name"],
            "is_class_admin": row["is_class_admin"],
        })

    return {"assignments": assignments}