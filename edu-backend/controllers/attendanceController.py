from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List


class AttendanceRecordItem(BaseModel):
    student_id: int
    present: bool


class SaveAttendancePayload(BaseModel):
    subject_code: str
    department: str
    semester: int
    section: str
    date: str
    records: List[AttendanceRecordItem]


class QuizResultItem(BaseModel):
    student_id: int
    marks_obtained: float


class SaveQuizResultsPayload(BaseModel):
    subject_code: str
    department: str
    semester: int
    section: str
    quiz_name: str
    max_marks: float
    results: List[QuizResultItem]


def save_attendance(db: Session, payload: SaveAttendancePayload, teacher_id: int):
    # Fetch subject name
    sub_row = db.execute(
        text("SELECT subject_name FROM subjects WHERE subject_code = :code;"),
        {"code": payload.subject_code}
    ).fetchone()
    subject_name = sub_row[0] if sub_row else payload.subject_code

    for rec in payload.records:
        # Check existing attendance record for student and subject
        existing = db.execute(
            text("""
                SELECT id, classes_held, classes_attended
                FROM attendance_records
                WHERE student_id = :sid AND subject_code = :scode;
            """),
            {"sid": rec.student_id, "scode": payload.subject_code}
        ).fetchone()

        if existing:
            new_held = existing.classes_held + 1
            new_attended = existing.classes_attended + (1 if rec.present else 0)
            new_pct = round((new_attended / new_held) * 100.0, 2)
            db.execute(
                text("""
                    UPDATE attendance_records
                    SET classes_held = :held, classes_attended = :att, attendance_percentage = :pct
                    WHERE id = :id;
                """),
                {"held": new_held, "att": new_attended, "pct": new_pct, "id": existing.id}
            )
        else:
            held = 1
            att = 1 if rec.present else 0
            pct = 100.0 if rec.present else 0.0
            db.execute(
                text("""
                    INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
                    VALUES (:sid, :scode, :sname, :held, :att, :pct, 'faculty_entry');
                """),
                {"sid": rec.student_id, "scode": payload.subject_code, "sname": subject_name, "held": held, "att": att, "pct": pct}
            )

    db.commit()
    return {"message": "Attendance successfully recorded", "total_records": len(payload.records)}


def save_quiz_results(db: Session, payload: SaveQuizResultsPayload, teacher_id: int):
    for r in payload.results:
        db.execute(
            text("""
                INSERT INTO quiz_results (student_id, subject_code, quiz_name, marks_obtained, max_marks, quiz_date)
                VALUES (:sid, :scode, :qname, :marks, :max_m, CURRENT_DATE);
            """),
            {
                "sid": r.student_id,
                "scode": payload.subject_code,
                "qname": payload.quiz_name,
                "marks": r.marks_obtained,
                "max_m": payload.max_marks
            }
        )

    db.commit()
    return {"message": "Assessment marks successfully recorded", "total_results": len(payload.results)}
