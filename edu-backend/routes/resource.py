from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from db import get_db
from controllers.resourceController import (
    dispatch_resource,
    get_student_resources,
    get_interventions_history
)
from middlewares.teacherOnly import teacher_only
from middlewares.auth import get_current_user


router = APIRouter(
    prefix="/api/interventions",
    tags=["interventions"]
)


class ResourceRequest(BaseModel):
    target_category: str
    title: str
    resource_url: str
    description: Optional[str] = None
    target_student_id: Optional[int] = None


@router.post("/resource")
def send_resource(
    data: ResourceRequest,
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
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

    target = data.target_category.lower().strip()

    if target not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target category '{data.target_category}'. Allowed: all, high, medium, low, specific_student, my_mentees."
        )

    count = dispatch_resource(
        db,
        current_user["user_id"],
        target,
        data.title,
        data.resource_url,
        data.description,
        data.target_student_id
    )

    return {
        "success": True,
        "message": f"Resource dispatched successfully to {count} student(s).",
        "students_reached": count
    }


@router.get("/resources")
def get_resources(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_student_resources(
        db,
        current_user["user_id"]
    )


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):
    return {
        "history": get_interventions_history(db, current_user["user_id"])
    }