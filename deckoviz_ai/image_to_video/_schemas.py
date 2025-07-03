from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Union

class ImageToVideoRequest(BaseModel):
    image: Union[HttpUrl, str] = Field(..., description="URL or local path to the input image")
    prompt: str = Field(..., description="Text prompt describing the video")
    max_area: Optional[str] = Field(None, description="Max area, e.g., '832x480'")
    fast_mode: Optional[str] = Field(None, description="Fast mode, e.g., 'Balanced'")
    lora_scale: Optional[float] = Field(None, description="LoRA scale")
    num_frames: Optional[int] = Field(None, description="Number of frames")
    sample_shift: Optional[int] = Field(None, description="Sample shift")
    sample_steps: Optional[int] = Field(None, description="Sample steps")
    frames_per_second: Optional[int] = Field(None, description="Frames per second")
    sample_guide_scale: Optional[int] = Field(None, description="Sample guide scale")
    api_token: Optional[str] = Field(None, description="Replicate API token (optional)") 