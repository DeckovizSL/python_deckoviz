from pydantic import BaseModel
from typing import Dict, Any

class GenerateRequest(BaseModel):
    user_input: str

class GenerateResponse(BaseModel):
    url: str
    prompt: str

class MetadataGenerateRequest(BaseModel):
    image: str
    
class MetadataResponse(BaseModel):
    metadata: Dict[str, Any]