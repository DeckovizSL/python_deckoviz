from pydantic import BaseModel, Field
from typing import List, Optional

class VisualFrame(BaseModel):
    title: str
    image_url: str
    reflection_text: str
    mood: str
    style: str

class VisualJournalEntry(BaseModel):
    title: str
    frames: List[VisualFrame]
    overall_mood: str
    date: str
    saved_to: str

class UserInput(BaseModel):
    text: str
    width: Optional[int] = Field(default=768, ge=256, le=1536, description="Image width in pixels (256-1536)")
    height: Optional[int] = Field(default=768, ge=256, le=1536, description="Image height in pixels (256-1536)")
