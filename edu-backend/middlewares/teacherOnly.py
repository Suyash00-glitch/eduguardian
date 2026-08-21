from fastapi import Depends, HTTPException

from middlewares.auth import get_current_user


def teacher_only(
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "teacher":
        raise HTTPException(
            status_code=403,
            detail="teacher access required"
        )

    return current_user