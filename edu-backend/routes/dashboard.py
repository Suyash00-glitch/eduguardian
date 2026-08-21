from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from middlewares.auth import get_current_user
from controllers.dashboardController import get_dashboard_summary, get_teacher_dashboard_summary


router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"]
)


@router.get("/summary")
def dashboard_summary(
    department: str = None,
    semester: int = None,
    section: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.get("role") in ("teacher", "admin") or department:
        dept = department or "ISE"
        sem = semester or 5
        sec = section or "C"
        return get_teacher_dashboard_summary(db, dept, sem, sec)

    return get_dashboard_summary(
        db,
        current_user["user_id"]
    )