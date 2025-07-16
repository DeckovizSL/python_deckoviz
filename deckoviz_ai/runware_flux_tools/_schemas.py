from pydantic import BaseModel, Field
from typing import Optional

class FluxFillRequest(BaseModel):
    prompt: str
    image_b64: str  # base64-encoded input image
    mask_b64: str   # base64-encoded mask image
    width: int = 1024
    height: int = 1024
    steps: int = 30

class FluxCannyRequest(BaseModel):
    prompt: str
    image_b64: str  # base64-encoded canny edge map
    width: int = 1024
    height: int = 1024
    steps: int = 30

class FluxDepthRequest(BaseModel):
    prompt: str
    image_b64: str  # base64-encoded depth map
    width: int = 1024
    height: int = 1024
    steps: int = 30

class FluxReduxRequest(BaseModel):
    prompt: Optional[str] = None  # If None, will use '__BLANK__' for pure variation
    image_b64: str  # base64-encoded guide image
    width: int = 1024
    height: int = 1024
    steps: int = 30

class FluxImageResponse(BaseModel):
    status: str
    image_url: Optional[str] = None
    detail: Optional[str] = None
    raw_response: Optional[dict] = None 