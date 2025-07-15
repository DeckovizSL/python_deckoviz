from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal

class FrameImage(BaseModel):
    inputImage: str  # UUID, URL, or base64 string
    frame: Optional[Union[str, int]] = None  # 'first', 'last', or frame number

class RunwareVideoRequest(BaseModel):
    taskType: Literal["videoInference"] = "videoInference"
    positivePrompt: str
    model: Optional[str] = None
    duration: int
    width: int
    height: int
    fps: Optional[int] = 30
    outputFormat: Optional[str] = "mp4"
    outputType: Optional[str] = "URL"
    outputQuality: Optional[int] = 95
    numberResults: Optional[int] = 1
    includeCost: Optional[bool] = False
    frameImages: List[FrameImage]
    referenceImages: Optional[List[str]] = None

class RunwareVideoResponse(BaseModel):
    status: str
    video_url: Optional[str] = None
    cost: Optional[float] = None
    error: Optional[str] = None 