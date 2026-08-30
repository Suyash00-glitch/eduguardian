from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from middlewares.teacherOnly import teacher_only
from controllers.attendanceController import (
    save_attendance,
    save_quiz_results,
    SaveAttendancePayload,
    SaveQuizResultsPayload,
)

router = APIRouter(
    tags=["attendance_and_marks"]
)


@router.post("/api/attendance")
def record_attendance(
    payload: SaveAttendancePayload,
    db: Session = Depends(get_db),
    current_user = Depends(teacher_only),
):
    return save_attendance(db, payload, current_user.get("user_id", 0))


@router.post("/api/quiz-results")
def record_quiz_results(
    payload: SaveQuizResultsPayload,
    db: Session = Depends(get_db),
    current_user = Depends(teacher_only),
):
    return save_quiz_results(db, payload, current_user.get("user_id", 0))
