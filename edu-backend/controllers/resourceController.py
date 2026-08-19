from sqlalchemy import text
from sqlalchemy.orm import Session


def dispatch_resource(
    db: Session,
    teacher_id: int,
    target_category: str,
    title: str,
    resource_url: str
):
    target_category = target_category.lower()

    if target_category == "all":
        query = text("""
            SELECT id
            FROM students
        """)

        students = db.execute(query).fetchall()

    else:
        query = text("""
            SELECT id
            FROM students
            WHERE LOWER(risk_level) = :risk
        """)

        students = db.execute(
            query,
            {"risk": target_category}
        ).fetchall()

    if not students:
        return 0

    insert_query = text("""
        INSERT INTO student_resources
        (
            student_id,
            teacher_id,
            title,
            resource_url,
            target_category
        )
        VALUES
        (
            :student_id,
            :teacher_id,
            :title,
            :resource_url,
            :target_category
        )
    """)

    for student in students:
        db.execute(
            insert_query,
            {
                "student_id": student.id,
                "teacher_id": teacher_id,
                "title": title,
                "resource_url": resource_url,
                "target_category": target_category
            }
        )

    db.commit()

    return len(students)


def get_student_resources(
    db: Session,
    student_id: int
):
    query = text("""
        SELECT
            sr.id,
            sr.title,
            sr.resource_url,
            sr.target_category,
            sr.teacher_id,
            u.full_name AS teacher_name
        FROM student_resources sr
        JOIN users u
            ON u.id = sr.teacher_id
        WHERE sr.student_id = :student_id
        ORDER BY sr.id DESC
    """)

    resources = db.execute(
        query,
        {"student_id": student_id}
    ).fetchall()

    return [
        {
            "id": resource.id,
            "title": resource.title,
            "url": resource.resource_url,
            "target_category": resource.target_category,
            "teacher_id": resource.teacher_id,
            "teacher_name": resource.teacher_name,
        }
        for resource in resources
    ]