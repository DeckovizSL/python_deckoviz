from pydantic import BaseModel
from typing import Optional

class GenerateArtRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    height: int
    width: int