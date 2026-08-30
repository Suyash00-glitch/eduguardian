from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException
from utils.password import hash_password


def get_mentors(db: Session):
    query = text("""
        SELECT
            t.id,
            t.user_id,
            u.full_name,
            u.email,
            t.employee_id,
            t.department,
            COALESCE(t.designation, 'Assistant Professor') AS designation,
            COALESCE(t.capacity, 5) AS capacity,
            COALESCE(t.is_active, true) AS is_active,
            t.phone,
            (
                SELECT COUNT(*)
                FROM mentor_assignments ma
                WHERE ma.mentor_id = t.id
                  AND ma.status = 'active'
            ) AS current_load
        FROM teachers t
        JOIN users u ON u.id = t.user_id
        ORDER BY t.is_active DESC, u.full_name ASC
    """)

    rows = db.execute(query).mappings().all()

    mentors = []
    for r in rows:
        load = int(r["current_load"])
        cap = int(r["capacity"])
        active = bool(r["is_active"])
        status = "INACTIVE" if not active else ("FULL" if load >= cap else "AVAILABLE")

        mentors.append({
            "id": r["id"],
            "user_id": r["user_id"],
            "name": r["full_name"],
            "full_name": r["full_name"],
            "email": r["email"],
            "employee_id": r["employee_id"],
            "department": r["department"],
            "designation": r["designation"],
            "capacity": cap,
            "max_capacity": cap,
            "current_load": load,
            "available_slots": max(0, cap - load),
            "is_active": active,
            "phone": r["phone"],
            "status": status
        })

    return mentors


def create_mentor(db: Session, data: dict):
    name = data.get("name") or data.get("full_name")
    email = (data.get("email") or "").strip().lower()
    emp_id = (data.get("employee_id") or "").strip().upper()
    department = data.get("department") or "ISE"
    designation = data.get("designation") or "Assistant Professor"
    capacity = int(data.get("capacity") or 5)
    is_active = bool(data.get("is_active", True))
    phone = data.get("phone")

    if not name or not email or not emp_id:
        raise HTTPException(status_code=400, detail="Name, Email, and Employee ID are required.")

    # Check if employee_id exists
    existing_teacher = db.execute(
        text("SELECT id FROM teachers WHERE UPPER(employee_id) = :emp_id"),
        {"emp_id": emp_id}
    ).mappings().first()
    if existing_teacher:
        raise HTTPException(status_code=400, detail=f"A mentor with Employee ID '{emp_id}' already exists.")

    # Check if email exists
    existing_user = db.execute(
        text("SELECT id FROM users WHERE LOWER(email) = :email"),
        {"email": email}
    ).mappings().first()

    if existing_user:
        user_id = existing_user["id"]
        # Update user role to teacher
        db.execute(
            text("UPDATE users SET full_name = :name, role = 'teacher' WHERE id = :uid"),
            {"name": name, "uid": user_id}
        )
    else:
        # Create user
        pwd_hash = hash_password("mentor123")
        res = db.execute(
            text("""
                INSERT INTO users (full_name, email, password_hash, role)
                VALUES (:name, :email, :pwd, 'teacher')
                RETURNING id
            """),
            {"name": name, "email": email, "pwd": pwd_hash}
        ).mappings().first()
        user_id = res["id"]

    # Create teacher record
    res_teacher = db.execute(
        text("""
            INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active, phone)
            VALUES (:uid, :emp_id, :dept, :desig, :cap, :act, :phone)
            RETURNING id
        """),
        {
            "uid": user_id,
            "emp_id": emp_id,
            "dept": department,
            "desig": designation,
            "cap": capacity,
            "act": is_active,
            "phone": phone
        }
    ).mappings().first()

    db.commit()

    return {
        "success": True,
        "message": "Mentor added successfully.",
        "mentor_id": res_teacher["id"],
        "user_id": user_id
    }


def update_mentor(db: Session, mentor_id: int, data: dict):
    teacher = db.execute(
        text("SELECT id, user_id FROM teachers WHERE id = :id"),
        {"id": mentor_id}
    ).mappings().first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Mentor not found.")

    user_id = teacher["user_id"]
    name = data.get("name") or data.get("full_name")
    email = data.get("email")
    emp_id = data.get("employee_id")
    department = data.get("department")
    designation = data.get("designation")
    capacity = data.get("capacity")
    is_active = data.get("is_active")
    phone = data.get("phone")

    if name or email:
        updates = []
        params = {"uid": user_id}
        if name:
            updates.append("full_name = :name")
            params["name"] = name
        if email:
            updates.append("email = :email")
            params["email"] = email.strip().lower()
        db.execute(text(f"UPDATE users SET {', '.join(updates)} WHERE id = :uid"), params)

    t_updates = []
    t_params = {"tid": mentor_id}
    if emp_id:
        t_updates.append("employee_id = :emp_id")
        t_params["emp_id"] = emp_id.strip().upper()
    if department:
        t_updates.append("department = :dept")
        t_params["dept"] = department
    if designation:
        t_updates.append("designation = :desig")
        t_params["desig"] = designation
    if capacity is not None:
        t_updates.append("capacity = :cap")
        t_params["cap"] = int(capacity)
    if is_active is not None:
        t_updates.append("is_active = :act")
        t_params["act"] = bool(is_active)
    if phone is not None:
        t_updates.append("phone = :phone")
        t_params["phone"] = phone

    if t_updates:
        db.execute(text(f"UPDATE teachers SET {', '.join(t_updates)} WHERE id = :tid"), t_params)

    db.commit()
    return {"success": True, "message": "Mentor updated successfully."}


def delete_mentor(db: Session, mentor_id: int):
    teacher = db.execute(
        text("SELECT id FROM teachers WHERE id = :id"),
        {"id": mentor_id}
    ).mappings().first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Mentor not found.")

    # Soft delete / deactivate mentor
    db.execute(
        text("UPDATE teachers SET is_active = false WHERE id = :id"),
        {"id": mentor_id}
    )
    # Cancel active assignments
    db.execute(
        text("UPDATE mentor_assignments SET status = 'cancelled' WHERE mentor_id = :id AND status = 'active'"),
        {"id": mentor_id}
    )
    db.commit()
    return {"success": True, "message": "Mentor deactivated and assignments archived."}


def assign_mentor(
    db: Session,
    student_id: int,
    mentor_id: int,
    assigned_by: int
):
    # 1. Check mentor exists and is active
    mentor = db.execute(
        text("""
            SELECT id, user_id, capacity, is_active
            FROM teachers
            WHERE id = :mentor_id
        """),
        {"mentor_id": mentor_id}
    ).mappings().first()

    if mentor is None:
        return {
            "success": False,
            "message": "Mentor not found."
        }

    if not mentor["is_active"]:
        return {
            "success": False,
            "message": "Cannot assign to an inactive mentor."
        }

    # 2. Check student exists
    student = db.execute(
        text("SELECT id, usn FROM students WHERE id = :sid"),
        {"sid": student_id}
    ).mappings().first()
    if not student:
        return {
            "success": False,
            "message": "Student not found."
        }

    # 3. Check mentor capacity
    max_cap = int(mentor["capacity"] or 5)
    load = db.execute(
        text("""
            SELECT COUNT(*) AS count
            FROM mentor_assignments
            WHERE mentor_id = :mentor_id
              AND status = 'active'
        """),
        {"mentor_id": mentor_id}
    ).scalar() or 0

    if load >= max_cap:
        return {
            "success": False,
            "message": f"Mentor is already at full capacity ({load}/{max_cap})."
        }

    # 4. Check if student already has an active mentor
    existing = db.execute(
        text("""
            SELECT id, mentor_id
            FROM mentor_assignments
            WHERE student_id = :student_id
              AND status = 'active'
        """),
        {"student_id": student_id}
    ).mappings().first()

    if existing:
        return {
            "success": False,
            "message": "Student already has an active mentor assignment."
        }

    # 5. Create assignment
    db.execute(
        text("""
            INSERT INTO mentor_assignments (student_id, mentor_id, assigned_by, status, assigned_at)
            VALUES (:student_id, :mentor_id, :assigned_by, 'active', CURRENT_TIMESTAMP)
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
        "message": "Mentor assigned successfully."
    }


def unassign_mentor(db: Session, assignment_id: int):
    res = db.execute(
        text("UPDATE mentor_assignments SET status = 'cancelled' WHERE id = :id"),
        {"id": assignment_id}
    )
    db.commit()
    return {"success": True, "message": "Mentee unassigned successfully."}


def get_my_mentees(db: Session, user_id: int):
    from controllers.portalController import _PORTAL_CONTEXT_CACHE
    from utils.academic_risk_engine import calculate_academic_risk

    # Find teacher record for logged-in user
    teacher = db.execute(
        text("SELECT id, user_id, employee_id FROM teachers WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).mappings().first()

    if teacher is None:
        # If user is admin (e.g. user_id 2 or 10), get all active mentees or first teacher
        first_t = db.execute(text("SELECT id FROM teachers ORDER BY id ASC LIMIT 1")).mappings().first()
        if not first_t:
            return []
        teacher_id = first_t["id"]
    else:
        teacher_id = teacher["id"]

    # Get students actively assigned to this mentor
    rows = db.execute(
        text("""
            SELECT
                ma.id AS assignment_id,
                s.id AS student_id,
                s.user_id AS student_user_id,
                u.full_name AS name,
                s.usn,
                s.department,
                s.semester,
                s.section,
                s.data_source,
                rp.risk_level as db_risk_level,
                rp.support_signal as db_support_signal,
                (SELECT avg(ar.attendance_percentage) FROM attendance_records ar WHERE ar.student_id = s.id) as avg_attendance,
                (SELECT (sum(qr.marks_obtained) / nullif(sum(qr.max_marks), 0)) * 100 FROM quiz_results qr WHERE qr.student_id = s.id) as quiz_average,
                ma.assigned_at,
                ma.status
            FROM mentor_assignments ma
            JOIN students s ON s.id = ma.student_id
            JOIN users u ON u.id = s.user_id
            LEFT JOIN LATERAL (
                SELECT risk_level, support_signal
                FROM risk_predictions
                WHERE student_id = s.id
                ORDER BY created_at DESC
                LIMIT 1
            ) rp ON TRUE
            WHERE ma.mentor_id = :teacher_id
              AND ma.status = 'active'
            ORDER BY u.full_name
        """),
        {"teacher_id": teacher_id}
    ).mappings().all()

    mentees = []

    for row in rows:
        uid = row["student_user_id"]
        is_portal = (row["data_source"] == "student_portal") or (row["usn"] in ("NNM24IS127", "NNM24IS172"))

        ctx = _PORTAL_CONTEXT_CACHE.get(uid)
        if not ctx and is_portal:
            try:
                from controllers.portalController import get_authenticated_student_context
                ctx = get_authenticated_student_context(db, uid)
            except Exception:
                ctx = None

        if ctx and is_portal:
            risk_eval = calculate_academic_risk(ctx)
            hist_perf = ctx.get("historical_academic_performance", {})
            r_level = (risk_eval.get("risk_level") or "low").upper()
            cgpa = hist_perf.get("cgpa")
            latest_sgpa = hist_perf.get("latest_sgpa")
            backlogs = hist_perf.get("arrears_count", 0)
            reason = (risk_eval.get("factors") or ["Strong academic trajectory"])[0]
        else:
            # Demo student
            r_level = (row["db_risk_level"] or "LOW").upper()
            cgpa = 6.80 if r_level == "MEDIUM" else (5.24 if r_level == "HIGH" else 9.20)
            latest_sgpa = 6.50 if r_level == "MEDIUM" else (4.50 if r_level == "HIGH" else 9.40)
            backlogs = 1 if r_level == "MEDIUM" else (3 if r_level == "HIGH" else 0)
            reason = row["db_support_signal"] or "Scheduled for periodic faculty mentoring"

        mentees.append({
            "assignment_id": row["assignment_id"],
            "student_id": row["student_id"],
            "id": row["student_id"],
            "name": row["name"],
            "usn": row["usn"],
            "department": row["department"],
            "semester": row["semester"],
            "section": row["section"],
            "data_source": "student_portal" if is_portal else "demo",
            "cgpa": cgpa,
            "latest_sgpa": latest_sgpa,
            "backlogs": backlogs,
            "risk_level": r_level,
            "attendance": round(float(row["avg_attendance"]), 1) if row["avg_attendance"] is not None else None,
            "quiz_average": round(float(row["quiz_average"]), 1) if row["quiz_average"] is not None else None,
            "reason": reason,
            "assigned_at": str(row["assigned_at"]) if row["assigned_at"] else None,
            "status": "Active"
        })

    return mentees


def get_student_mentor(db: Session, student_user_id: int):
    # Find student ID
    student = db.execute(
        text("SELECT id FROM students WHERE user_id = :uid"),
        {"uid": student_user_id}
    ).mappings().first()
    if not student:
        return None

    row = db.execute(
        text("""
            SELECT
                ma.id AS assignment_id,
                t.id AS mentor_id,
                u.full_name AS mentor_name,
                u.email AS mentor_email,
                t.employee_id,
                t.department,
                COALESCE(t.designation, 'Assistant Professor') AS designation,
                t.phone,
                ma.assigned_at
            FROM mentor_assignments ma
            JOIN teachers t ON t.id = ma.mentor_id
            JOIN users u ON u.id = t.user_id
            WHERE ma.student_id = :student_id
              AND ma.status = 'active'
            ORDER BY ma.assigned_at DESC
            LIMIT 1
        """),
        {"student_id": student["id"]}
    ).mappings().first()

    if not row:
        return None

    return {
        "mentor_id": row["mentor_id"],
        "name": row["mentor_name"],
        "email": row["mentor_email"],
        "employee_id": row["employee_id"],
        "department": row["department"],
        "designation": row["designation"],
        "phone": row["phone"],
        "assigned_at": str(row["assigned_at"]) if row["assigned_at"] else None
    }