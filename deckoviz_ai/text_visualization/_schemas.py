from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class TextVisualizationInput(BaseModel):
    input_type: Literal["text", "pdf"] = Field(..., description="Type of input: 'text' or 'pdf'")
    text: Optional[str] = Field(None, description="Text input if input_type is 'text'")
    pdf_file_path: Optional[str] = Field(None, description="Path to PDF file if input_type is 'pdf'")
    visualization_prompt: str = Field(..., description="User's visualization instruction")
    image_density: Literal[
        "1_image_per_paragraph",
        "1_image_per_page",
        "2_images_per_page"
    ] = Field(..., description="How many images to generate per text chunk")
    page_start: Optional[int] = Field(None, description="Start page (1-indexed, inclusive) for PDF")
    page_end: Optional[int] = Field(None, description="End page (1-indexed, inclusive) for PDF")

class TextVisualizationOutput(BaseModel):
    prompts: List[str] = Field(..., description="List of generated prompts for image generation")
    image_urls: List[str] = Field(..., description="List of generated image URLs (one per prompt)") 