from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from middlewares.auth import get_current_user
from controllers.dashboardController import get_dashboard_summary


router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"]
)


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_dashboard_summary(
        db,
        current_user["user_id"]
    )