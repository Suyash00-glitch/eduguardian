from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from fastapi import HTTPException
from middlewares.auth import get_current_user
from db import get_db
from controllers.studentController import (
    get_student_roster,
    get_student_attendance,
    get_student_profile,
    get_student_risk_detail
)
from middlewares.teacherOnly import teacher_only

router = APIRouter(
    prefix="/api/students",
    tags=["students"]
)


@router.get("/roster")
def student_roster(
    department: str = None,
    semester: int = None,
    section: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    risk: str = Query("all"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(teacher_only)
):
    """
    Teacher/Admin only: Retrieves cohort student roster with complete risk assessment.
    """
    return get_student_roster(
        db=db,
        department=department,
        semester=semester,
        section=section,
        page=page,
        page_size=page_size,
        risk=risk
    )


@router.get("/risk-detail/{student_id}")
def student_risk_detail(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(teacher_only)
):
    """
    Teacher/Admin only: Retrieves deep explainable risk signals for a specific student.
    """
    return get_student_risk_detail(db, student_id)


@router.get("/profile")
def student_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="student access required"
        )

    return get_student_profile(
        db,
        current_user["user_id"]
    )


@router.get("/attendance")
def student_attendance(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="student access required"
        )

    return get_student_attendance(
        db,
        current_user["user_id"]
    )


def sanitize_portal_context_for_student(raw_ctx: dict) -> dict:
    if not raw_ctx:
        return {
            "identity": {},
            "academic_guidance": {
                "state": "active_profile",
                "badge": "ACTIVE PROFILE",
                "headline": "Academic Profile Active",
                "standing_label": "Enrolled",
                "outlook_status": "Active Standing",
                "message": "Your academic profile is active.",
                "outlook_message": "Active standing evaluated from completed semester examinations.",
                "trajectory": "stable",
                "early_semester_note": "Current-semester attendance and assessment records are pending faculty publication."
            }
        }
    sanitized = dict(raw_ctx)
    hist_perf = sanitized.get("historical_academic_performance", {})

    from utils.academic_guidance import evaluate_student_academic_guidance
    sanitized["academic_guidance"] = evaluate_student_academic_guidance(hist_perf)

    # Remove internal risk classification from student payload
    sanitized.pop("risk_evaluation", None)
    sanitized.pop("risk_level", None)
    sanitized.pop("risk_score", None)
    sanitized.pop("confidence", None)
    sanitized.pop("factors", None)
    sanitized.pop("shap_explanation", None)
    sanitized.pop("risk_basis", None)

    return sanitized


@router.get("/portal-context")
def student_portal_context(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="student access required"
        )

    from controllers.portalController import get_authenticated_student_context
    raw_ctx = get_authenticated_student_context(
        db=db,
        user_id=current_user["user_id"]
    )
    return sanitize_portal_context_for_student(raw_ctx)


@router.get("/risk-analysis")
def student_risk_analysis(
    db=Depends(get_db),
    current_user=Depends(teacher_only)
):
    """
    Teacher/Admin only: Internal risk analysis endpoint.
    """
    from controllers.portalController import get_authenticated_student_context
    ctx = get_authenticated_student_context(
        db=db,
        user_id=current_user["user_id"]
    )
    return ctx.get("risk_evaluation", {})


@router.get("/internal/context/{identifier}")
def internal_student_context(
    identifier: str,
    db: Session = Depends(get_db)
):
    """
    Internal seam for EduGuardian Chatbot & A2A agent services to retrieve ground-truth StudentContext.
    No student-facing risk classification is returned.
    """
    from controllers.portalController import _PORTAL_CONTEXT_CACHE, get_authenticated_student_context
    from sqlalchemy import text

    clean = str(identifier).strip()

    # 1. Search in-memory portal cache by user_id, USN, email, or student_id
    for uid, ctx in _PORTAL_CONTEXT_CACHE.items():
        ident = ctx.get("identity", {})
        if (
            str(uid) == clean
            or ident.get("usn", "").lower() == clean.lower()
            or ident.get("email", "").lower() == clean.lower()
            or ident.get("student_id", "").lower() == clean.lower()
        ):
            return sanitize_portal_context_for_student(ctx)

    # 2. Search database by email, USN, or ID
    user_row = db.execute(
        text("""
            SELECT u.id FROM users u
            LEFT JOIN students s ON s.user_id = u.id
            WHERE LOWER(u.email) = :id OR LOWER(s.usn) = :id OR CAST(u.id AS TEXT) = :id OR CAST(s.id AS TEXT) = :id
            LIMIT 1
        """),
        {"id": clean.lower()}
    ).mappings().first()

    if user_row:
        raw_ctx = get_authenticated_student_context(db=db, user_id=user_row["id"])
        return sanitize_portal_context_for_student(raw_ctx)

    # 3. Fail closed if not found (Never return another student's context)
    raise HTTPException(status_code=404, detail="Student record not found")
