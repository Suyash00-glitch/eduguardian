from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import date

from db import get_db
from controllers.assignmentController import (
    get_assignments,
    create_assignment,
    get_student_assignments,
    get_student_assignment,
    submit_student_assignment,
      get_teacher_assignment
)
from middlewares.teacherOnly import teacher_only
from middlewares.auth import get_current_user


router = APIRouter(
    prefix="/api/assignments",
    tags=["assignments"]
)


@router.get("")
def list_assignments(
    department: str,
    semester: int,
    section: str,
    subject_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_assignments(
        db,
        department,
        semester,
        section,
        subject_code
    )


@router.post("")
async def add_assignment(
    department: str = Form(...),
    semester: int = Form(...),
    section: str = Form(...),
    subject_code: str = Form(...),
    assignment_name: str = Form(...),
    max_marks: float = Form(...),
    due_date: date = Form(...),

    resource: UploadFile | None = File(None),

    db: Session = Depends(get_db),
    current_user=Depends(teacher_only),
):
    return await create_assignment(
        db=db,
        user_id=current_user["user_id"],
        department=department,
        semester=semester,
        section=section,
        subject_code=subject_code,
        assignment_name=assignment_name,
        max_marks=max_marks,
        due_date=due_date,
        resource=resource
    )


@router.get("/student")
def list_student_assignments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="student access required"
        )

    return get_student_assignments(
        db,
        current_user["user_id"]
    )

@router.get("/student/{assignment_id}")
def get_one_student_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="student access required"
        )

    return get_student_assignment(
        db,
        current_user["user_id"],
        assignment_id
    )

@router.post("/student/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="student access required"
        )

    return await submit_student_assignment(
        db=db,
        user_id=current_user["user_id"],
        assignment_id=assignment_id,
        file=file
    )

@router.get("/teacher/{assignment_id}")
def get_teacher_assignment(
    assignment_id: int,
    page: int = 1,
    page_size: int = 10,
    search: str = "",
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only),
):
    return get_student_assignment(
        db=db,
        user_id=current_user["user_id"],
        assignment_id=assignment_id,
        page=page,
        page_size=page_size,
        search=search
    )