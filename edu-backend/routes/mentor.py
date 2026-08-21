from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from db import get_db
from controllers.mentorController import (
    get_mentors,
    create_mentor,
    update_mentor,
    delete_mentor,
    assign_mentor,
    unassign_mentor,
    get_my_mentees,
    get_student_mentor
)
from middlewares.teacherOnly import teacher_only
from middlewares.auth import get_current_user


router = APIRouter(
    prefix="/api/mentors",
    tags=["mentors"]
)


class MentorCreateRequest(BaseModel):
    name: str
    email: str
    employee_id: str
    department: Optional[str] = "ISE"
    designation: Optional[str] = "Assistant Professor"
    capacity: Optional[int] = 5
    is_active: Optional[bool] = True
    phone: Optional[str] = None


class MentorUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None
    phone: Optional[str] = None


class MentorAssignmentRequest(BaseModel):
    student_id: int
    mentor_id: int


class MentorUnassignRequest(BaseModel):
    assignment_id: int


@router.get("")
def list_mentors(
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):
    return {
        "mentors": get_mentors(db),
        "teachers": get_mentors(db)  # Support both keys for backward compatibility
    }


@router.post("")
def add_mentor(
    data: MentorCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):
    return create_mentor(db, data.dict())


@router.put("/{mentor_id}")
def edit_mentor(
    mentor_id: int,
    data: MentorUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):
    return update_mentor(db, mentor_id, data.dict(exclude_unset=True))


@router.delete("/{mentor_id}")
def remove_mentor(
    mentor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):
    return delete_mentor(db, mentor_id)


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


@router.post("/unassign")
def unassign(
    data: MentorUnassignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):
    return unassign_mentor(db, data.assignment_id)


@router.delete("/assignments/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):
    return unassign_mentor(db, assignment_id)


@router.get("/me/students")
def my_mentees(
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):
    mentees_list = get_my_mentees(
        db,
        current_user["user_id"]
    )
    return {
        "students": mentees_list,
        "mentees": mentees_list  # Support both keys
    }


@router.get("/my-mentor")
def student_mentor(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    mentor_info = get_student_mentor(db, current_user["user_id"])
    return {
        "has_mentor": mentor_info is not None,
        "mentor": mentor_info
    }