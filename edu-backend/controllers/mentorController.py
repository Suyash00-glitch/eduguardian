from sqlalchemy import text
from sqlalchemy.orm import Session


MAX_MENTOR_CAPACITY = 5


def assign_mentor(
    db: Session,
    student_id: int,
    mentor_id: int,
    assigned_by: int
):
    # Check mentor exists
    mentor = db.execute(
        text("""
            SELECT id
            FROM teachers
            WHERE id = :mentor_id
        """),
        {"mentor_id": mentor_id}
    ).mappings().first()

    if mentor is None:
        return {
            "success": False,
            "message": "mentor not found"
        }

    # Count only ACTIVE assignments
    load = db.execute(
        text("""
            SELECT COUNT(*) AS count
            FROM mentor_assignments
            WHERE mentor_id = :mentor_id
              AND status = 'active'
        """),
        {"mentor_id": mentor_id}
    ).scalar()

    if load >= MAX_MENTOR_CAPACITY:
        return {
            "success": False,
            "message": "mentor is already at full capacity"
        }

    # Check if student already has an ACTIVE mentor
    existing = db.execute(
        text("""
            SELECT id
            FROM mentor_assignments
            WHERE student_id = :student_id
              AND status = 'active'
        """),
        {"student_id": student_id}
    ).mappings().first()

    if existing:
        return {
            "success": False,
            "message": "student already has an active mentor"
        }

    # Create assignment
    db.execute(
        text("""
            INSERT INTO mentor_assignments
            (
                student_id,
                mentor_id,
                assigned_by,
                status
            )
            VALUES
            (
                :student_id,
                :mentor_id,
                :assigned_by,
                'active'
            )
        """),
        {
            "student_id": student_id,
            "mentor_id": mentor_id,
            "assigned_by": assigned_by
        }
    )

    db.commit()

    return {
        "success": True,
        "message": "mentor assigned successfully"
    }

def get_my_mentees(db: Session, user_id: int):

    # Find teacher record for logged-in user
    teacher = db.execute(
        text("""
            SELECT id
            FROM teachers
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).mappings().first()

    if teacher is None:
        return []

    teacher_id = teacher["id"]

    # Get students actively assigned to this mentor
    rows = db.execute(
        text("""
            SELECT
                s.id,
                u.full_name AS name,
                s.usn,
                s.department,
                s.semester,
                s.section,

                ma.assigned_at

            FROM mentor_assignments ma

            JOIN students s
                ON s.id = ma.student_id

            JOIN users u
                ON u.id = s.user_id

            WHERE ma.mentor_id = :teacher_id
              AND ma.status = 'active'

            ORDER BY u.full_name
        """),
        {"teacher_id": teacher_id}
    ).mappings().all()

    mentees = []

    for row in rows:
        mentees.append({
            "id": row["id"],
            "name": row["name"],
            "usn": row["usn"],
            "department": row["department"],
            "semester": row["semester"],
            "section": row["section"],
            "assigned_at": row["assigned_at"]
        })

    return mentees