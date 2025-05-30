
from pydantic import BaseModel, Field
from typing import Optional, List
from ._enums import StyleCategory
from typing import TypedDict

# Enhanced Image Generation Tool
class ImageGenToolArgs(BaseModel):
    styled_image_prompt: str = Field(description="The prompt for image generation.")
    imagebase64: str = Field(description="The image to apply style on..")
    style_description: str = Field(description="Description of the style to apply.")

class StyleTransferRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image")
    preset_style: Optional[StyleCategory] = Field(None, description="Predefined style category")
    custom_style_description: Optional[str] = Field(None, description="Custom style description")
    intensity: float = Field(0.7, description="Style transfer intensity (0.1-1.0)")
    preserve_content: bool = Field(True, description="Whether to preserve original content structure")

class StyleAnalysis(BaseModel):
    image_description: str = Field(..., description="Description of the input image")
    recommended_techniques: List[str] = Field(..., description="Recommended artistic techniques")
    color_palette: List[str] = Field(..., description="Suggested color palette")
    composition_notes: str = Field(..., description="Notes about composition")

class StyleTransferResult(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    styled_image_prompt: str = Field(..., description="Generated prompt for image creation")
    style_description: str = Field(..., description="Description of applied style")
    processing_notes: str = Field(..., description="Notes about the processing")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class ImageGenerationResult(BaseModel):
    success: bool = Field(..., description="Whether image generation was successful")
    image_data_base64: Optional[str] = Field(None, description="Generated image as base64")
    generation_prompt: str = Field(..., description="Final prompt used for generation")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class FinalResult(BaseModel):
    success: bool = Field(..., description="Overall operation success")
    original_image_analysis: Optional[StyleAnalysis] = Field(None, description="Analysis of original image")
    style_transfer_result: Optional[StyleTransferResult] = Field(None, description="Style transfer output")
    generated_image_result: Optional[ImageGenerationResult] = Field(None, description="Image generation output")
    processing_time: float = Field(..., description="Total processing time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")


# Enhanced state for multi-agent workflow
class MultiAgentState(TypedDict):
    request: StyleTransferRequest
    image_analysis: Optional[StyleAnalysis]
    style_result: Optional[StyleTransferResult]
    image_generation_result: Optional[ImageGenerationResult]
    final_result: Optional[FinalResult]
    error: Optional[str]
    current_step: str
    processing_start_time: float