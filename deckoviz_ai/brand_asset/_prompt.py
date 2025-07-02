import os
import json
from typing import Optional, List
from pydantic import BaseModel, Field
from ..llm import GeminiLLM
from PIL import Image
import io

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
    logo_description: Optional[str] = None
    brand_palette: Optional[List[str]] = None
    visual_use_case: str = Field(..., description="The intended use for the visual, e.g., 'Campaign graphic', 'Artistic ad banner'.")
    style: Optional[str] = None
    height: int = 1024
    width: int = 1024
    image_features: Optional[dict] = None  # New: features extracted from logo image

class BrandAssetResult(BaseModel):
    prompts: List[str] = Field(description="A list of one or more image generation prompts for the brand asset.")

class BrandAssetPrompt:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required. Please set in environment variables.")
        self.llm = GeminiLLM(model_name=model_name)

    def generate_prompts(self, req: BrandAssetRequest) -> BrandAssetResult:
        # Use LLM-extracted values if user input is missing
        palette = req.brand_palette
        if (not palette or len(palette) == 0) and req.image_features:
            palette = req.image_features.get("dominant_colors") or req.image_features.get("colors") or []
        palette_str = ", ".join(palette) if palette else ""
        style = req.style or "an aesthetic, modern, and artistic visual identity"
        desc = req.logo_description
        if not desc and req.image_features:
            desc = req.image_features.get("notable_visual_elements") or req.image_features.get("features") or ""
        design_lang = req.image_features.get("design_language") if req.image_features else ""
        details = req.image_features.get("other_relevant_details") if req.image_features else ""
        # Build a simple, direct prompt
        final_prompt = f"Create a {style} brand asset for {req.visual_use_case}. The design should use these colors: {palette_str}. Style: {design_lang}. Elements: {desc}. {details}"
        raw_result = self.llm._call(final_prompt)
        try:
            import json
            clean_json_string = raw_result.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json_string)
            parsed_result = BrandAssetResult.model_validate(data)
        except Exception:
            parsed_result = BrandAssetResult(prompts=[raw_result.strip()])
        return parsed_result

def analyze_logo_image(image_bytes: bytes) -> dict:
    """
    Use Gemini API directly to extract features from the logo image (colors, design language, etc).
    This does NOT use GeminiLLM and is self-contained for brand_asset only.
    """
    import google.generativeai as genai
    import os
    from PIL import Image
    import io
    import json
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is required. Please set in environment variables.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    image = Image.open(io.BytesIO(image_bytes))
    prompt = (
        "Analyze this logo image and return a JSON object with: "
        "1. Dominant colors (HEX), 2. Design language (e.g., minimal, geometric, playful), "
        "3. Notable visual elements (shapes, icons, text), 4. Other relevant details. "
        "Output ONLY a valid JSON object."
    )
    response = model.generate_content([prompt, image])
    result = response.text if hasattr(response, 'text') else response.parts[0].text
    try:
        clean_json_string = result.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json_string)
    except Exception:
        return {"raw": result.strip()} 