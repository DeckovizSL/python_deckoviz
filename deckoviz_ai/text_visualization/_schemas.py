from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from fastapi import Form

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

class TextVisualizationRequestData:
    def __init__(
        self,
        input_type: str = Form(..., description="Input mode: 'text' or 'pdf'."),
        visualization_prompt: str = Form(..., description="The artistic instruction for the AI, e.g., 'A watercolor painting.'"),
        image_density: str = Form(..., description="Content splitting strategy. For 'text' input, must be '1_image_per_paragraph'. For 'pdf', can be '1_image_per_paragraph', '1_image_per_page', or '2_images_per_page'."),
        text: Optional[str] = Form(None, description="Required if input_type is 'text'. The raw text to visualize."),
        page_start: Optional[int] = Form(None, description="For PDF only. The page to start processing from (1-indexed)."),
        page_end: Optional[int] = Form(None, description="For PDF only. The page to end processing at (inclusive)."),
        height: Optional[int] = Form(768, description="The height of the generated images."),
        width: Optional[int] = Form(1024, description="The width of the generated images.")
    ):
        self.input_type = input_type
        self.visualization_prompt = visualization_prompt
        self.image_density = image_density
        self.text = text
        self.page_start = page_start
        self.page_end = page_end
        self.height = height
        self.width = width 