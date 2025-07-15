from pydantic import BaseModel
from typing import Optional, Dict, Any

class StorySegmentInput(BaseModel):
    text: str
    previous_context: Optional[Dict[str, Any]] = None

class StoryVisualizationOutput(BaseModel):
    prompt: str
    image_url: str 