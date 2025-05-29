from pydantic import BaseModel


class GenerateRequest(BaseModel):
    user_input: str

class GenerateResponse(BaseModel):
    url: str
    prompt: str