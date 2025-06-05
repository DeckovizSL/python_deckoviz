from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from database.connection import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, index=True)  # replaces Django's AutoField
    image_id = Column(String, unique=True, index=True, nullable=False)
    external_url = Column(String, nullable=True)
    file = Column(String, nullable=True)   # store file path or URL
    music = Column(String, nullable=True)  # store file path or URL
    uploaded_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    uploaded_by = relationship("User", back_populates="uploaded_images")
    metadata = Column(JSON, nullable=True)
    view = Column(String, default='private', nullable=True)
    is_active = Column(Boolean, default=True)
