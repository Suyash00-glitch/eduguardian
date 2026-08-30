from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from middlewares.auth import get_current_user
from controllers.goalController import (
    get_student_goals,
    get_one_student_goal,
    create_student_goal,
    update_student_goal,
    delete_student_goal,
    toggle_milestone,
    add_milestone,
    delete_milestone,
)

router = APIRouter(
    prefix="/api/goals",
    tags=["goals"]
)


class MilestoneInput(BaseModel):
    title: str
    completed: Optional[bool] = False


class GoalCreateRequest(BaseModel):
    title: str
    category: Optional[str] = "Academic"
    target: Optional[str] = "100%"
    due_date: Optional[date] = None
    milestones: Optional[List[MilestoneInput]] = []


class GoalUpdateRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    target: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None


class MilestoneAddRequest(BaseModel):
    title: str


@router.get("")
def list_goals(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="student access required")
    return get_student_goals(db, current_user["user_id"])


@router.get("/{goal_id}")
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="student access required")
    return get_one_student_goal(db, current_user["user_id"], goal_id)


@router.post("")
def create_goal(
    data: GoalCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="student access required")
    return create_student_goal(db, current_user["user_id"], data.model_dump())


@router.put("/{goal_id}")
def update_goal(
    goal_id: int,
    data: GoalUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="student access required")
    return update_student_goal(db, current_user["user_id"], goal_id, data.model_dump(exclude_unset=True))


@router.delete("/{goal_id}")
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="student access required")
    return delete_student_goal(db, current_user["user_id"], goal_id)


@router.post("/{goal_id}/milestones")
def add_goal_milestone(
    goal_id: int,
    data: MilestoneAddRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="student access required")
    return add_milestone(db, current_user["user_id"], goal_id, data.title)


@router.patch("/{goal_id}/milestones/{milestone_id}")
def toggle_goal_milestone(
    goal_id: int,
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="student access required")
    return toggle_milestone(db, current_user["user_id"], goal_id, milestone_id)


@router.delete("/{goal_id}/milestones/{milestone_id}")
def delete_goal_milestone(
    goal_id: int,
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="student access required")
    return delete_milestone(db, current_user["user_id"], goal_id, milestone_id)
