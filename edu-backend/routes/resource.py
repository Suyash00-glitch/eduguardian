from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from controllers.resourceController import (
    dispatch_resource,
    get_student_resources
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


@router.post("/resource")
def send_resource(
    data: ResourceRequest,
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):

    allowed_categories = [
        "all",
        "high",
        "medium",
        "low"
    ]

    target = data.target_category.lower()

    if target not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail="invalid target category"
        )

    count = dispatch_resource(
        db,
        current_user["user_id"],
        target,
        data.title,
        data.resource_url
    )

    return {
        "message": "resource dispatched successfully",
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