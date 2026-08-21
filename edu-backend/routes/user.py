from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db import get_db
from controllers.userController import signup_user, login_user


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)


class SignupRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str

    usn: str | None = None
    department: str | None = None
    semester: int | None = None
    section: str | None = None

    employee_id: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str



class BulkSignupRequest(BaseModel):
    students: list[SignupRequest]


@router.post("/signup/bulk")
def bulk_signup(
    data: BulkSignupRequest,
    db: Session = Depends(get_db)
):
    results = []

    for student in data.students:

        result = signup_user(
            db,
            student.full_name,
            student.email,
            student.password,
            student.role,
            student.usn,
            student.department,
            student.semester,
            student.section,
            student.employee_id
        )

        results.append({
            "email": student.email,
            "success": result is not None
        })

    return {
        "message": "bulk signup completed",
        "results": results
    }



@router.post("/signup")
def signup(
    data: SignupRequest,
    db: Session = Depends(get_db)
):

    if data.role not in ["student", "teacher"]:
        raise HTTPException(
            status_code=400,
            detail="invalid role"
        )

    if data.role == "student":

        if not data.usn:
            raise HTTPException(
                status_code=400,
                detail="usn is required for students"
            )

    if data.role == "teacher":

        if not data.employee_id:
            raise HTTPException(
                status_code=400,
                detail="employee id is required for teachers"
            )

    result = signup_user(
        db,
        data.full_name,
        data.email,
        data.password,
        data.role,
        data.usn,
        data.department,
        data.semester,
        data.section,
        data.employee_id
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="email already registered"
        )

    return result


@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    result = login_user(
        db,
        data.email,
        data.password
    )

    if not result:
        raise HTTPException(
            status_code=401,
            detail="invalid email or password"
        )

    return result


class PortalLoginRequest(BaseModel):
    mobile: str
    password: str
    captcha: str | None = None
    terms_accepted: bool = True


class DemoLoginRequest(BaseModel):
    identifier: str = "student@eduguardian.ai"


@router.post("/portal-login")
def portal_login(
    data: PortalLoginRequest,
    db: Session = Depends(get_db)
):
    from controllers.portalController import portal_login_student
    return portal_login_student(
        db=db,
        mobile=data.mobile,
        password=data.password,
        captcha=data.captcha
    )


@router.post("/demo-login")
def demo_login(
    data: DemoLoginRequest,
    db: Session = Depends(get_db)
):
    from controllers.portalController import demo_login_student
    return demo_login_student(
        db=db,
        identifier=data.identifier
    )