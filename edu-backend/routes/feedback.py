from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from db import get_db
from middlewares.auth import get_current_user
from controllers.feedbackController import (
    get_feedback_list,
    update_feedback_status,
    submit_student_feedback,
    get_student_own_feedback,
    SubmitFeedbackPayload
)

router = APIRouter(
    prefix="/api/feedback",
    tags=["feedback"]
)


class FeedbackUpdatePayload(BaseModel):
    status: str
    reply: Optional[str] = None


@router.post("")
def create_feedback_ticket(
    payload: SubmitFeedbackPayload,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return submit_student_feedback(db, current_user["user_id"], payload)


@router.get("/my")
def list_student_own_tickets(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return get_student_own_feedback(db, current_user["user_id"])


@router.get("")
def list_feedback(
    department: str | None = Query(None),
    semester: int | None = Query(None),
    section: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return get_feedback_list(db, department, semester, section, status)


@router.patch("/{feedback_id}")
def update_feedback(
    feedback_id: int,
    payload: FeedbackUpdatePayload,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return update_feedback_status(db, feedback_id, payload.status, payload.reply)
