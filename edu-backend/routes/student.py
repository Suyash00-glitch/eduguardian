from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from fastapi import HTTPException
from middlewares.auth import get_current_user
from db import get_db
from controllers.studentController import (get_student_roster,get_student_attendance)
from middlewares.teacherOnly import teacher_only
from controllers.studentController import get_student_profile

router = APIRouter(
    prefix="/api/students",
    tags=["students"]
)


@router.get("/roster")
def student_roster(
    department: str,
    semester: int,
    section: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    risk: str = Query("all"),

    db: Session = Depends(get_db),

    current_user: dict = Depends(teacher_only)
):

    return get_student_roster(
        db,
        department,
        semester,
        section,
        page,
        page_size,
        risk
    )



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