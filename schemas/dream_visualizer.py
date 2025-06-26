from pydantic import BaseModel, Field, validator
from typing import Optional

class DreamVisualizeRequest(BaseModel):
    height: Optional[int] = Field(512, description="Height of the generated image. Must be a multiple of 64.")
    width: Optional[int] = Field(512, description="Width of the generated image. Must be a multiple of 64.")

    @validator('height', 'width')
    def must_be_multiple_of_64(cls, v):
        if v % 64 != 0:
            raise ValueError('must be a multiple of 64')
        return v 