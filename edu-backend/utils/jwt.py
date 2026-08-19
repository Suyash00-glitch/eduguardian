from jose import jwt
from datetime import datetime, timedelta
from config import secret_key

algorithm = "HS256"


def create_token(user_id, role):

    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }

    token = jwt.encode(
        payload,
        secret_key,
        algorithm=algorithm
    )

    return token