from pydantic import BaseModel
from typing import Optional 

class StyleTransferResponse(BaseModel):
    image_base64: str
    styled_image_prompt: str
    style_description: str
    processing_notes: str
    error_message: Optional[str] = None
    