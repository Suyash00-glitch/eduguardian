from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException


def get_student_id_for_user(db: Session, user_id: int) -> int:
    student = db.execute(
        text("SELECT id FROM students WHERE user_id = :uid"),
        {"uid": user_id}
    ).mappings().first()
    if student:
        return student["id"]
    # Fallback if student record not separate
    return user_id


def recompute_goal_progress(db: Session, goal_id: int):
    milestones = db.execute(
        text("SELECT id, completed FROM goal_milestones WHERE goal_id = :gid"),
        {"gid": goal_id}
    ).mappings().all()

    total = len(milestones)
    if total == 0:
        return

    completed_count = sum(1 for m in milestones if m["completed"])
    progress = int(round((completed_count / total) * 100))

    if progress == 100:
        status = "completed"
    elif progress >= 50:
        status = "on-track"
    else:
        status = "in-progress"

    db.execute(
        text("""
            UPDATE student_goals
            SET progress = :prog, status = :status, updated_at = CURRENT_TIMESTAMP
            WHERE id = :gid
        """),
        {"prog": progress, "status": status, "gid": goal_id}
    )


def get_student_goals(db: Session, user_id: int):
    student_id = get_student_id_for_user(db, user_id)

    goals = db.execute(
        text("""
            SELECT id, student_id, title, category, target, progress, status, due_date, created_at, updated_at
            FROM student_goals
            WHERE student_id = :sid
            ORDER BY 
                CASE 
                    WHEN status = 'in-progress' THEN 1
                    WHEN status = 'on-track' THEN 2
                    WHEN status = 'completed' THEN 3
                    ELSE 4
                END,
                id ASC
        """),
        {"sid": student_id}
    ).mappings().all()

    result = []
    for g in goals:
        milestones = db.execute(
            text("""
                SELECT id, goal_id, title, completed, completed_at, created_at
                FROM goal_milestones
                WHERE goal_id = :gid
                ORDER BY id ASC
            """),
            {"gid": g["id"]}
        ).mappings().all()

        result.append({
            "id": g["id"],
            "student_id": g["student_id"],
            "title": g["title"],
            "category": g["category"] or "Academic",
            "target": g["target"] or "100%",
            "progress": int(g["progress"] or 0),
            "status": g["status"] or "in-progress",
            "due_date": str(g["due_date"]) if g["due_date"] else None,
            "created_at": str(g["created_at"]) if g["created_at"] else None,
            "updated_at": str(g["updated_at"]) if g["updated_at"] else None,
            "milestones": [
                {
                    "id": m["id"],
                    "goal_id": m["goal_id"],
                    "title": m["title"],
                    "completed": bool(m["completed"]),
                    "completed_at": str(m["completed_at"]) if m["completed_at"] else None,
                    "created_at": str(m["created_at"]) if m["created_at"] else None
                }
                for m in milestones
            ]
        })

    return result


def get_one_student_goal(db: Session, user_id: int, goal_id: int):
    student_id = get_student_id_for_user(db, user_id)

    goal = db.execute(
        text("""
            SELECT id, student_id, title, category, target, progress, status, due_date, created_at, updated_at
            FROM student_goals
            WHERE id = :gid AND student_id = :sid
        """),
        {"gid": goal_id, "sid": student_id}
    ).mappings().first()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")

    milestones = db.execute(
        text("""
            SELECT id, goal_id, title, completed, completed_at, created_at
            FROM goal_milestones
            WHERE goal_id = :gid
            ORDER BY id ASC
        """),
        {"gid": goal["id"]}
    ).mappings().all()

    return {
        "id": goal["id"],
        "student_id": goal["student_id"],
        "title": goal["title"],
        "category": goal["category"] or "Academic",
        "target": goal["target"] or "100%",
        "progress": int(goal["progress"] or 0),
        "status": goal["status"] or "in-progress",
        "due_date": str(goal["due_date"]) if goal["due_date"] else None,
        "created_at": str(goal["created_at"]) if goal["created_at"] else None,
        "updated_at": str(goal["updated_at"]) if goal["updated_at"] else None,
        "milestones": [
            {
                "id": m["id"],
                "goal_id": m["goal_id"],
                "title": m["title"],
                "completed": bool(m["completed"]),
                "completed_at": str(m["completed_at"]) if m["completed_at"] else None,
                "created_at": str(m["created_at"]) if m["created_at"] else None
            }
            for m in milestones
        ]
    }


def create_student_goal(db: Session, user_id: int, data: dict):
    student_id = get_student_id_for_user(db, user_id)

    title = (data.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Goal title is required.")

    category = data.get("category", "Academic")
    target = data.get("target", "100%")
    due_date = data.get("due_date")
    milestones_input = data.get("milestones", [])

    created = db.execute(
        text("""
            INSERT INTO student_goals (student_id, title, category, target, progress, status, due_date, created_at, updated_at)
            VALUES (:sid, :title, :category, :target, 0, 'in-progress', :due_date, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
        """),
        {
            "sid": student_id,
            "title": title,
            "category": category,
            "target": target,
            "due_date": due_date
        }
    ).mappings().first()

    goal_id = created["id"]

    # Insert initial milestones if provided
    if isinstance(milestones_input, list):
        for item in milestones_input:
            m_title = item.get("title") if isinstance(item, dict) else str(item)
            m_title = (m_title or "").strip()
            if m_title:
                m_completed = item.get("completed", False) if isinstance(item, dict) else False
                db.execute(
                    text("""
                        INSERT INTO goal_milestones (goal_id, title, completed, created_at)
                        VALUES (:gid, :title, :comp, CURRENT_TIMESTAMP)
                    """),
                    {"gid": goal_id, "title": m_title, "comp": m_completed}
                )

    recompute_goal_progress(db, goal_id)
    db.commit()

    return get_one_student_goal(db, user_id, goal_id)


def update_student_goal(db: Session, user_id: int, goal_id: int, data: dict):
    student_id = get_student_id_for_user(db, user_id)

    # Check goal exists and belongs to student
    existing = db.execute(
        text("SELECT id FROM student_goals WHERE id = :gid AND student_id = :sid"),
        {"gid": goal_id, "sid": student_id}
    ).mappings().first()

    if not existing:
        raise HTTPException(status_code=404, detail="Goal not found.")

    title = data.get("title")
    category = data.get("category")
    target = data.get("target")
    due_date = data.get("due_date")
    status = data.get("status")

    updates = []
    params = {"gid": goal_id}

    if title is not None:
        updates.append("title = :title")
        params["title"] = title.strip()
    if category is not None:
        updates.append("category = :category")
        params["category"] = category
    if target is not None:
        updates.append("target = :target")
        params["target"] = target
    if due_date is not None:
        updates.append("due_date = :due_date")
        params["due_date"] = due_date
    if status is not None:
        updates.append("status = :status")
        params["status"] = status

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        query_str = f"UPDATE student_goals SET {', '.join(updates)} WHERE id = :gid"
        db.execute(text(query_str), params)
        db.commit()

    return get_one_student_goal(db, user_id, goal_id)


def delete_student_goal(db: Session, user_id: int, goal_id: int):
    student_id = get_student_id_for_user(db, user_id)

    existing = db.execute(
        text("SELECT id FROM student_goals WHERE id = :gid AND student_id = :sid"),
        {"gid": goal_id, "sid": student_id}
    ).mappings().first()

    if not existing:
        raise HTTPException(status_code=404, detail="Goal not found.")

    db.execute(text("DELETE FROM goal_milestones WHERE goal_id = :gid"), {"gid": goal_id})
    db.execute(text("DELETE FROM student_goals WHERE id = :gid"), {"gid": goal_id})
    db.commit()

    return {"success": True, "message": "Goal deleted successfully."}


def toggle_milestone(db: Session, user_id: int, goal_id: int, milestone_id: int):
    student_id = get_student_id_for_user(db, user_id)

    # Verify ownership
    goal = db.execute(
        text("SELECT id FROM student_goals WHERE id = :gid AND student_id = :sid"),
        {"gid": goal_id, "sid": student_id}
    ).mappings().first()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")

    milestone = db.execute(
        text("SELECT id, completed FROM goal_milestones WHERE id = :mid AND goal_id = :gid"),
        {"mid": milestone_id, "gid": goal_id}
    ).mappings().first()

    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found.")

    new_status = not milestone["completed"]
    completed_at = datetime.utcnow() if new_status else None

    db.execute(
        text("""
            UPDATE goal_milestones
            SET completed = :comp, completed_at = :cat
            WHERE id = :mid
        """),
        {"comp": new_status, "cat": completed_at, "mid": milestone_id}
    )

    recompute_goal_progress(db, goal_id)
    db.commit()

    return get_one_student_goal(db, user_id, goal_id)


def add_milestone(db: Session, user_id: int, goal_id: int, title: str):
    student_id = get_student_id_for_user(db, user_id)

    goal = db.execute(
        text("SELECT id FROM student_goals WHERE id = :gid AND student_id = :sid"),
        {"gid": goal_id, "sid": student_id}
    ).mappings().first()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")

    clean_title = (title or "").strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Milestone title is required.")

    db.execute(
        text("""
            INSERT INTO goal_milestones (goal_id, title, completed, created_at)
            VALUES (:gid, :title, false, CURRENT_TIMESTAMP)
        """),
        {"gid": goal_id, "title": clean_title}
    )

    recompute_goal_progress(db, goal_id)
    db.commit()

    return get_one_student_goal(db, user_id, goal_id)


def delete_milestone(db: Session, user_id: int, goal_id: int, milestone_id: int):
    student_id = get_student_id_for_user(db, user_id)

    goal = db.execute(
        text("SELECT id FROM student_goals WHERE id = :gid AND student_id = :sid"),
        {"gid": goal_id, "sid": student_id}
    ).mappings().first()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")

    db.execute(
        text("DELETE FROM goal_milestones WHERE id = :mid AND goal_id = :gid"),
        {"mid": milestone_id, "gid": goal_id}
    )

    recompute_goal_progress(db, goal_id)
    db.commit()

    return get_one_student_goal(db, user_id, goal_id)
