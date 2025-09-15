
from jose import jwt
from fastapi import HTTPException,status
from api.utils.settings import SECRET_KEY, JWT_HASH_ALGORITHM

def verify_access_token(token:str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=JWT_HASH_ALGORITHM)
        # user_id: str = payload.get("sub") 
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.")

def create_access_token(payload:dict) -> str:
    try:
        token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_HASH_ALGORITHM)
        return token
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.")


async def get_current_user(token: str):
    """Decode JWT, fetch Tenant, and enforce authentication"""
    return verify_access_token(token) 