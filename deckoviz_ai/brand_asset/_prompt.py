import os
import json
from typing import Optional, List
from pydantic import BaseModel, Field
from ..llm import GeminiLLM

# System prompt for brand asset creation
BRAND_ASSET_SYSTEM_PROMPT = """
You are Deckoviz_BrandAssetArtGenerator. Generate visual content, artwork, or graphics that incorporate a business's brand assets based on their text descriptions. Your primary goal is to produce a JSON object containing a list of one or more detailed image generation prompts.

Instructions:
- The user will provide brand assets as text: logo descriptions, color palettes, and the desired use case.
- Interpret the brand tone (e.g., playful, elegant, bold) from the descriptions.
- Create design prompts that fuse the brand identity with visual imagination.
- Describe the brand logo's placement as a compositional anchor or subtle element.
- Strictly use the provided brand color palette.
- Generate one or more visual prompts, suggesting creative variations.
- Output ONLY a valid JSON object like this: {"prompts": ["prompt 1 text...", "prompt 2 text..."]}. Do not add any other text, explanations, or markdown.
"""

class BrandAssetRequest(BaseModel):
    logo_description: str
    brand_palette: List[str] = Field(..., description="List of HEX color codes for the brand.")
    visual_use_case: str = Field(..., description="The intended use for the visual, e.g., 'Campaign graphic', 'Artistic ad banner'.")
    style: Optional[str] = None
    height: int = 1024
    width: int = 1024

class BrandAssetResult(BaseModel):
    prompts: List[str] = Field(description="A list of one or more image generation prompts for the brand asset.")

class BrandAssetPrompt:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required. Please set in environment variables.")
        self.llm = GeminiLLM(model_name=model_name)

    def generate_prompts(self, req: BrandAssetRequest) -> BrandAssetResult:
        """
        Generates one or more prompts for a brand asset with robust parsing.
        """
        palette_str = ", ".join(req.brand_palette)
        style = req.style or "an aesthetic, modern, and artistic visual identity"
        
        # Manually construct the prompt.
        final_prompt = (
            f"{BRAND_ASSET_SYSTEM_PROMPT}\n\n"
            f"User input:\n"
            f"Logo Description: {req.logo_description}\n"
            f"Brand Palette: {palette_str}\n"
            f"Visual Use Case: {req.visual_use_case}\n"
            f"Style: {style}\n"
        )

        # Call the LLM directly.
        raw_result = self.llm._call(final_prompt)
        
        try:
            # Attempt to parse the LLM output as JSON.
            clean_json_string = raw_result.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json_string)
            parsed_result = BrandAssetResult.model_validate(data)
        except Exception:
            # If parsing fails, assume the LLM returned a single, raw prompt string as a fallback.
            parsed_result = BrandAssetResult(prompts=[raw_result.strip()])
            
        return parsed_result 