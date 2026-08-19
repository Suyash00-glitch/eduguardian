from sqlalchemy import text
from fastapi import HTTPException

def get_student_roster(
    db,
    department,
    semester,
    section,
    page,
    page_size,
    risk
):

    offset = (page - 1) * page_size

    count_query = text("""
        select count(*)
        from students s
        where s.department = :department
        and s.semester = :semester
        and s.section = :section
    """)

    total_students = db.execute(
        count_query,
        {
            "department": department,
            "semester": semester,
            "section": section
        }
    ).scalar()

    query = text("""
        select
            s.id,
            s.usn,
            u.full_name,

            coalesce(
                rp.risk_level,
                'low'
            ) as risk_level,

            coalesce(
                (
                    select avg(ar.attendance_percentage)
                    from attendance_records ar
                    where ar.student_id = s.id
                ),
                0
            ) as attendance,

            coalesce(
                (
                    select
                        (sum(qr.marks_obtained) /
                        nullif(sum(qr.max_marks), 0)) * 100
                    from quiz_results qr
                    where qr.student_id = s.id
                ),
                0
            ) as quiz_average

        from students s

        join users u
            on s.user_id = u.id

        left join lateral (
            select
                risk_level
            from risk_predictions
            where student_id = s.id
            order by created_at desc
            limit 1
        ) rp
            on true

        where s.department = :department
        and s.semester = :semester
        and s.section = :section

        order by u.full_name

        limit :page_size
        offset :offset
    """)

    params = {
        "department": department,
        "semester": semester,
        "section": section,
        "page_size": page_size,
        "offset": offset
    }

    if risk != "all":
        query = text("""
            select
                s.id,
                s.usn,
                u.full_name,
                coalesce(rp.risk_level, 'low') as risk_level,

                coalesce(
                    (
                        select avg(ar.attendance_percentage)
                        from attendance_records ar
                        where ar.student_id = s.id
                    ),
                    0
                ) as attendance,

                coalesce(
                    (
                        select
                            (sum(qr.marks_obtained) /
                            nullif(sum(qr.max_marks), 0)) * 100
                        from quiz_results qr
                        where qr.student_id = s.id
                    ),
                    0
                ) as quiz_average

            from students s

            join users u
                on s.user_id = u.id

            left join lateral (
                select risk_level
                from risk_predictions
                where student_id = s.id
                order by created_at desc
                limit 1
            ) rp
                on true

            where s.department = :department
            and s.semester = :semester
            and s.section = :section
            and coalesce(rp.risk_level, 'low') = :risk

            order by u.full_name

            limit :page_size
            offset :offset
        """)

        params["risk"] = risk

    results = db.execute(query, params).fetchall()

    students = []

    for row in results:

        students.append({
            "id": row.id,
            "usn": row.usn,
            "name": row.full_name,
            "risk_level": row.risk_level,
            "attendance": round(float(row.attendance), 2),
            "quiz_average": round(float(row.quiz_average), 2)
        })

    total_pages = (
        total_students + page_size - 1
    ) // page_size

    return {
        "students": students,
        "page": page,
        "page_size": page_size,
        "total_students": total_students,
        "total_pages": total_pages
    }

def get_student_profile(db, user_id: int):

    row = db.execute(
        text("""
            SELECT
                u.id AS user_id,
                u.full_name,
                u.email,
                s.id AS student_id,
                s.usn,
                s.department,
                s.semester,
                s.section
            FROM users u
            JOIN students s
                ON s.user_id = u.id
            WHERE u.id = :user_id
        """),
        {"user_id": user_id}
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="student profile not found"
        )

    return {
        "id": row["student_id"],
        "userId": row["user_id"],
        "name": row["full_name"],
        "email": row["email"],
        "usn": row["usn"],
        "department": row["department"],
        "semester": row["semester"],
        "section": row["section"],
    }





def get_student_attendance(db, user_id):

    result = db.execute(
        text("""
            SELECT
                ar.subject_code,
                ar.subject_name,
                ar.classes_held,
                ar.classes_attended,
                ar.attendance_percentage
            FROM attendance_records ar
            JOIN students s
                ON s.id = ar.student_id
            WHERE s.user_id = :user_id
            ORDER BY ar.subject_code
        """),
        {
            "user_id": user_id
        }
    )

    rows = result.mappings().all()

    return {
        "attendance": [
            {
                "subjectCode": row["subject_code"],
                "subjectName": row["subject_name"],
                "classesHeld": row["classes_held"],
                "classesAttended": row["classes_attended"],
                "percentage": (
                    float(row["attendance_percentage"])
                    if row["attendance_percentage"] is not None
                    else 0
                )
            }
            for row in rows
        ]
    }