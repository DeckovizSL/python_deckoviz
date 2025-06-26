from pydantic import BaseModel, Field
from typing import Optional

class BookToFramesRequest(BaseModel):
    start_page: int = Field(..., description="Page number to start parsing from (1-indexed)")
    end_page: Optional[int] = Field(None, description="Optional page number to stop parsing at (inclusive, 1-indexed)")
    num_frames: int = Field(..., description="Number of frames to divide the book into")
    height: Optional[int] = Field(512, description="Image height in pixels")
    width: Optional[int] = Field(512, description="Image width in pixels") 