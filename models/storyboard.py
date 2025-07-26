from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.connection import Base

class Storyboard(Base):
    __tablename__ = "storyboards"

    id = Column(Integer, primary_key=True, index=True)
    tenant = Column(String, index=True, nullable=False)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    width = Column(Integer, default=1600)
    height = Column(Integer, default=896)

    frames = relationship("StoryboardFrame", back_populates="storyboard")

class StoryboardFrame(Base):
    __tablename__ = "storyboard_frames"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    storyboard_id = Column(Integer, ForeignKey("storyboards.id"))

    storyboard = relationship("Storyboard", back_populates="frames") 