from fastapi import APIRouter, Depends, HTTPException, Body, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, Optional

from db import get_db
from middlewares.auth import get_current_user
from controllers.recoveryController import (
    get_student_recovery_plan,
    save_student_recovery_plan,
    toggle_recovery_task,
    add_ai_study_plan,
    get_default_recovery_plan_for_student
)

router = APIRouter(
    prefix="/api/recovery",
    tags=["recovery"]
)


@router.get("/plan")
def get_recovery_plan(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves the authenticated student's active recovery & study plan.
    If none exists, dynamically constructs a personalized blueprint.
    """
    user_id = current_user["user_id"]
    return get_student_recovery_plan(db, user_id)


@router.post("/plan")
def save_recovery_plan(
    plan: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Updates the authenticated student's recovery plan.
    """
    user_id = current_user["user_id"]
    return save_student_recovery_plan(db, user_id, plan)


@router.post("/tasks/{task_id}/toggle")
def toggle_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Toggles a task's completion status and recalculates plan progress.
    """
    user_id = current_user["user_id"]
    return toggle_recovery_task(db, user_id, task_id)


@router.post("/ai-sync")
def sync_ai_plan(
    payload: Dict[str, Any] = Body(...),
    x_internal_student_id: str = Header(None, alias="X-Internal-Student-Id"),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Called when the AI Coach or Study Planner generates a new plan or recommended milestones.
    Automatically incorporates the AI plan into the student's active recovery plan.
    """
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            from middlewares.auth import decode_access_token
            payload_token = decode_access_token(token)
            user_id = payload_token.get("user_id")
        except Exception:
            pass

    if not user_id and x_internal_student_id:
        clean = x_internal_student_id.strip()
        row = db.execute(
            text("""
                SELECT u.id FROM users u
                LEFT JOIN students s ON s.user_id = u.id
                WHERE LOWER(u.email) = :c OR LOWER(s.usn) = :c OR CAST(s.id AS TEXT) = :c OR CAST(u.id AS TEXT) = :c
                LIMIT 1
            """),
            {"c": clean.lower()}
        ).mappings().first()
        if row:
            user_id = row["id"]

    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return add_ai_study_plan(db, user_id, payload)


@router.post("/ai-generate")
def generate_fresh_ai_plan(
    payload: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generates a fresh, context-tailored AI Recovery Blueprint based on the student's
    latest marksheets, risk radar, and subjects.
    """
    user_id = current_user["user_id"]
    from controllers.portalController import get_authenticated_student_context, _PORTAL_CONTEXT_CACHE
    ctx = _PORTAL_CONTEXT_CACHE.get(user_id)
    if not ctx:
        try:
            ctx = get_authenticated_student_context(db, user_id)
        except Exception:
            ctx = None

    user_row = {
        "full_name": current_user.get("full_name"),
        "email": current_user.get("email")
    }

    prompt = payload.get("prompt", "")
    fresh_plan = get_default_recovery_plan_for_student(ctx, user_row, custom_prompt=prompt)
    return save_student_recovery_plan(db, user_id, fresh_plan)
