from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db import get_db
from controllers.mentorController import (
    assign_mentor,
    get_my_mentees
)
from middlewares.teacherOnly import teacher_only


router = APIRouter(
    prefix="/api/mentors",
    tags=["mentors"]
)


class MentorAssignmentRequest(BaseModel):
    student_id: int
    mentor_id: int


@router.post("/assign")
def assign(
    data: MentorAssignmentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):

    result = assign_mentor(
        db,
        data.student_id,
        data.mentor_id,
        current_user["user_id"]
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result

@router.get("/me/students")
def my_mentees(
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):
    return {
        "students": get_my_mentees(
            db,
            current_user["user_id"]
        )
    }