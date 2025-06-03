
# Pydantic models for API validation
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    role: str  # 'user', 'assistant', or 'system'
    content: str
    user_id: Optional[str] = None  # Can be None for assistant/system messages
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: str
    chat_id: str
    role: str
    content: str
    user_id: Optional[str] = None
    created_at: datetime
    is_read: bool = False
    tokens: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ChatCreate(BaseModel):
    """Schema for creating a new chat"""
    session_id: str
    user_id: str  # UUID from Django User model
    title: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatUpdate(BaseModel):
    """Schema for updating an existing chat"""
    title: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Schema for chat response"""
    id: str
    user_id: str
    session_id: str
    title: Optional[str] = None
    model: str
    system_prompt: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    user_id: str  # UUID from Django User model
    title: Optional[str] = None
    description: Optional[str] = None
    

class ChatSessionUpdate(BaseModel):
    """Schema for updating an existing chat session"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    
    
class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""
    id: str
    user_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    chats_count: Optional[int] = None  # Count of chats in this session
    
    class Config:
        from_attributes = True


class ChatSessionDetailedResponse(ChatSessionResponse):
    """Schema for detailed chat session response including chats"""
    chats: List[ChatResponse] = []
    
    class Config:
        from_attributes = True

class RequestMessage(BaseModel):
    """Schema for request message"""
    message: Optional[str] = None

class AIConversationMessage(BaseModel):
    """Schema for personal painter message"""
    id: str
    session_id: str
    role: str
    content: str 

    class Config:
        from_attributes = True

class PersonalPainterChatResponse(BaseModel):
    """Schema for personal painter chat response"""
    id: str
    session_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[AIConversationMessage] = []
    
    class Config:
        from_attributes = True