from sqlalchemy import text
from utils.password import verify_password
from utils.jwt import create_token
from utils.password import hash_password, verify_password



def signup_user(
    db,
    full_name,
    email,
    password,
    role,
    usn=None,
    department=None,
    semester=None,
    section=None,
    employee_id=None
):

    role = role.strip().lower()
    email = email.strip().lower()

    if usn:
        usn = usn.strip().upper()

    if department:
        department = department.strip().upper()

    if section:
        section = section.strip().upper()

    existing = db.execute(
        text("""
            select id
            from users
            where email = :email
        """),
        {"email": email}
    ).fetchone()

    if existing:
        return None

    try:

        password_hash = hash_password(password)

        user_result = db.execute(
            text("""
                insert into users
                (
                    full_name,
                    email,
                    password_hash,
                    role
                )
                values
                (
                    :full_name,
                    :email,
                    :password_hash,
                    :role
                )
                returning id
            """),
            {
                "full_name": full_name,
                "email": email,
                "password_hash": password_hash,
                "role": role
            }
        )

        user_id = user_result.fetchone().id

        if role == "student":

            db.execute(
                text("""
                    insert into students
                    (
                        user_id,
                        usn,
                        department,
                        semester,
                        section
                    )
                    values
                    (
                        :user_id,
                        :usn,
                        :department,
                        :semester,
                        :section
                    )
                """),
                {
                    "user_id": user_id,
                    "usn": usn,
                    "department": department,
                    "semester": semester,
                    "section": section
                }
            )

        elif role == "teacher":

            db.execute(
                text("""
                    insert into teachers
                    (
                        user_id,
                        employee_id,
                        department
                    )
                    values
                    (
                        :user_id,
                        :employee_id,
                        :department
                    )
                """),
                {
                    "user_id": user_id,
                    "employee_id": employee_id,
                    "department": department
                }
            )

        else:
            db.rollback()
            return None

        db.commit()

        return {
            "user_id": user_id,
            "role": role,
            "message": "signup successful"
        }

    except Exception as e:
        db.rollback()
        raise e


def login_user(db, email, password):

    query = text("""
        SELECT
            u.id,
            u.full_name,
            u.email,
            u.password_hash,
            u.role,
            u.is_active,
            s.usn,
            s.department,
            s.semester,
            s.section
        FROM users u
        LEFT JOIN students s
            ON s.user_id = u.id
        WHERE u.email = :email
    """)

    result = db.execute(
        query,
        {"email": email.strip().lower()}
    ).fetchone()

    if not result:
        return None

    if not result.is_active:
        return None

    if not verify_password(
        password,
        result.password_hash
    ):
        return None

    token = create_token(
        result.id,
        result.role
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": result.id,
            "full_name": result.full_name,
            "email": result.email,
            "role": result.role,
            "usn": result.usn,
            "department": result.department,
            "semester": result.semester,
            "section": result.section
        }
    }


   