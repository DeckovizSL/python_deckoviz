from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.connection import Base

class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant = Column(String, unique=True, index=True)
    session_id = Column(String, unique=True, index=True)
    status = Column(String, default="active")  # active, completed, abandoned
    started_at = Column(DateTime(timezone=False), default=datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=False), nullable=True)
    
    # Relationship to chat messages
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("onboarding_sessions.session_id"))
    message_type = Column(String, default="human", nullable=False)  # human, ai, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=False), default=datetime.now(timezone.utc))
    message_metadata = Column(Text, nullable=True)  # JSON string for additional data
    
    # Relationship back to session
    session = relationship("OnboardingSession", back_populates="messages")
