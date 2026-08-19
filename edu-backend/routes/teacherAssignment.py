from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from controllers.teacherAssignmentController import get_teacher_assignments
from middlewares.auth import get_current_user


router = APIRouter(
    prefix="/api/teacher",
    tags=["teacher"]
)


@router.get("/assignments")
def teacher_assignments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_teacher_assignments(db, current_user["user_id"])