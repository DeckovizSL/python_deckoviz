
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    """User model that matches JWT token payload structure"""
    token_type: str
    exp: int  # Expiration time as Unix timestamp
    iat: int  # Issued at time as Unix timestamp
    jti: str  # JWT ID
    id: str = Field(alias="user_id")  # Duplicate of user_id for convenience
    
    # Optional fields that might be in the token
    sub: Optional[str] = None
    
    class Config:
        # Allow extra fields from JWT token
        extra = "allow"
