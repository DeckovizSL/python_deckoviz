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
    num_frames: Optional[int] = Field(default=1, ge=1, le=6, description="Number of frames to generate (1-6)")

class VisualJournalHistoryEntry(BaseModel):
    id: str
    title: str
    overall_mood: str
    date: str
    created_at: str
    frame_count: int
    preview_image_url: str  # URL of the first frame for preview
    all_frame_urls: List[str]  # URLs of all frames for thumbnail grid
    frame_titles: List[str]  # Titles of all frames
    original_text_preview: str  # First 100 characters of original text
    journey_summary: str  # Summary describing the journey/experience
