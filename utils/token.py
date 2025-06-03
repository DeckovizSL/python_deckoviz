from datetime import datetime
from typing import Optional, Dict, Any
from jose import jwt
import jose
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from utils.settings import get_settings
from schemas.user import User

settings = get_settings()

# Get the secret key from environment variables
# SECRET_KEY = settings.secret_key.strip() 
SECRET_KEY="IU4ILBuRKCfBes1Sa7gUxMgVa6EbfwzZHhX4KB7uyL5wtsyPsjQkT-PtTSRNDUGyddpUsbf0kmyZCGYhe6DfIQ"
ALGORITHM = settings.jwt_hash_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
 

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token and return its payload.
    
    Args:
        token: The JWT token to decode
        
    Returns:
        The decoded token payload as a dictionary
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    try: 
        # Try decoding with different options
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM], 
            options={
                "verify_aud": False,
                "verify_iss": False,
                "verify_sub": False,
                "verify_jti": False,
                "verify_exp": True,  # Keep expiration check
                "verify_iat": False,
                "verify_nbf": False
            }
        )
        return payload
        
    except jose.ExpiredSignatureError as e: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jose.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current user from a JWT token.
    
    Args:
        token: JWT token from the Authorization header
        
    Returns:
        Dictionary containing the user information from the token
        
    Raises:
        HTTPException: If the token is invalid or the user is not found
    """
    decoded_payload = decode_token(token)
    
    # Check for user_id in different possible fields
    user_id = decoded_payload.get("sub") or decoded_payload.get("user_id")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload - no user identifier found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Ensure user_id field exists for the User model
    if "user_id" not in decoded_payload and "sub" in decoded_payload:
        decoded_payload["user_id"] = decoded_payload["sub"]
    elif "user_id" not in decoded_payload:
        decoded_payload["user_id"] = user_id
        
    # Ensure id field exists for backward compatibility
    decoded_payload["id"] = user_id
    
    # Create User model from decoded payload
    try:
        return User(**decoded_payload)
    except Exception as e: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error processing user data: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_token(token: str) -> bool:
    """
    Verify if a token is valid (not expired and properly signed).
    
    Args:
        token: The JWT token to verify
        
    Returns:
        True if the token is valid, False otherwise
    """
    try:
        decode_token(token)
        return True
    except HTTPException:
        return False

def get_token_expiration(token: str) -> Optional[datetime]:
    """
    Get the expiration datetime of a token.
    
    Args:
        token: The JWT token
        
    Returns:
        The expiration datetime or None if the token is invalid
    """
    try:
        payload = decode_token(token)
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp)
        return None
    except HTTPException:
        return None