from pydantic import BaseModel, Field
from typing import List, Optional

class StoryboardFrameCreate(BaseModel):
    prompt: str

class StoryboardFrame(BaseModel):
    id: int
    prompt: str
    image_url: Optional[str] = None
    storyboard_id: int

    class Config:
        orm_mode = True

class StoryboardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    width: Optional[int] = 1600
    height: Optional[int] = 896
    frames: List[StoryboardFrameCreate] = []

class Storyboard(BaseModel):
    id: int
    tenant: str
    title: str
    description: Optional[str] = None
    width: int
    height: int
    frames: List[StoryboardFrame] = []
    
    class Config:
        orm_mode = True
        
class StoryboardList(BaseModel):
    storyboards: List[Storyboard]

class AIStoryGenerationRequest(BaseModel):
    short_instruction: str
    
class AIStoryFrameSuggestion(BaseModel):
    suggested_prompt: str

class StoryboardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None 