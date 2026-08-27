from sqlalchemy.orm import Session
from controllers.mentorController import get_mentors


def get_teachers(db: Session):
    return get_mentors(db)