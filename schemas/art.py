from pydantic import BaseModel


class GenerateArtRequest(BaseModel):
    prompt: str
    negative_prompt: str
    height: int
    width: int