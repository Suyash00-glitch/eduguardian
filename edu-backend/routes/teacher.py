from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from controllers.teacherController import get_teachers
from middlewares.teacherOnly import teacher_only


router = APIRouter(
    prefix="/api/teachers",
    tags=["teachers"]
)


@router.get("")
def teachers(
    db: Session = Depends(get_db),
    current_user=Depends(teacher_only)
):
    return {
        "teachers": get_teachers(db)
    }


