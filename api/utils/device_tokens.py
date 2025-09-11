from jose import jwt
from fastapi import HTTPException, status
from utils.settings import SECRET_KEY, JWT_HASH_ALGORITHM
import datetime

def create_jwt(payload: dict, exp_minutes: int = 15) -> str:
    payload = payload.copy()
    payload['exp'] = int((datetime.datetime.utcnow() + datetime.timedelta(minutes=exp_minutes)).timestamp())
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_HASH_ALGORITHM)

def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_HASH_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired.")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

def get_current_user(token: str):
    payload = decode_jwt(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found in token.")
    return user_id
