from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from db import get_db
from controllers.resourceController import (
    dispatch_resource_with_file,
    get_student_resources,
    get_interventions_history
)
from middlewares.teacherOnly import teacher_only
from middlewares.auth import get_current_user


router = APIRouter(
    prefix="/api/interventions",
    tags=["interventions"]
)


@router.post("/resource")
async def send_resource(
    target_category: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    resource_url: Optional[str] = Form(None),
    target_student_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(teacher_only)
):
    allowed_categories = [
        "all",
        "entire_cohort",
        "cohort",
        "high",
        "medium",
        "low",
        "specific_student",
        "specific",
        "student",
        "my_mentees",
        "mentees"
    ]

    target = target_category.lower().strip()

    if target not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target category '{target_category}'. Allowed: all, high, medium, low, specific_student, my_mentees."
        )

    count, final_url, res_type = await dispatch_resource_with_file(
        db=db,
        teacher_user_id=current_user["user_id"],
        target_category=target,
        title=title,
        resource_url=resource_url,
        description=description,
        target_student_id=target_student_id,
        file=file
    )

    return {
        "success": True,
        "message": f"Resource ({res_type}) dispatched successfully to {count} student portal(s).",
        "students_reached": count,
        "resource_url": final_url,
        "resource_type": res_type
    }


@router.get("/resources")
def get_resources(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return get_student_resources(
        db,
        current_user["user_id"]
    )


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user = Depends(teacher_only)
):
    return {
        "history": get_interventions_history(db, current_user["user_id"])
    }