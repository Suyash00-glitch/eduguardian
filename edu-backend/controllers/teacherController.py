from sqlalchemy import text
from sqlalchemy.orm import Session


MAX_MENTOR_CAPACITY = 5


def get_teachers(db: Session):

    query = text("""
        SELECT
            t.id,
            t.user_id,
            u.full_name,
            u.email,
            t.employee_id,
            t.department,

            COUNT(ma.id) AS current_load

        FROM teachers t

        JOIN users u
            ON u.id = t.user_id

        LEFT JOIN mentor_assignments ma
            ON ma.mentor_id = t.id
            AND ma.status = 'active'

        GROUP BY
            t.id,
            t.user_id,
            u.full_name,
            u.email,
            t.employee_id,
            t.department

        ORDER BY u.full_name
    """)

    result = db.execute(query)

    teachers = []

    for row in result:
        teachers.append({
            "id": row.id,
            "user_id": row.user_id,
            "full_name": row.full_name,
            "email": row.email,
            "employee_id": row.employee_id,
            "department": row.department,
            "current_load": row.current_load,
            "max_capacity": MAX_MENTOR_CAPACITY
        })

    return teachers