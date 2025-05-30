import base64
from google.generativeai import types
from langchain_core.tools import tool
from google import generativeai as genai
from ._schemas import ImageGenToolArgs

@tool(args_schema=ImageGenToolArgs)
async def generate_image_with_gemini_tool(styled_image_prompt: str,imagebase64:str, style_description: str) -> dict:
    """Generates an image using the Gemini API based on the provided styled prompt."""
    try:
        # Decode base64 to bytes
        image_bytes = base64.b64decode(imagebase64)
        
        # Prepare the image part
        image_part = types.Part(
            inline_data=types.Blob(mime_type="image/png", data=image_bytes)
        )
        
        # Enhanced prompt combining style and content
        enhanced_prompt = f"{styled_image_prompt}\n\nStyle: {style_description}"
        
        # Placeholder for actual Gemini API call
        # In real implementation, replace with actual Gemini image generation API
        print(f"🎨 Generating image with prompt: {enhanced_prompt[:100]}...")
        
        # Placeholder for actual Gemini API call
        response = genai.Client().models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=[styled_image_prompt, image_part],
            config=types.GenerateContentConfig(
              response_modalities=['TEXT', 'IMAGE']
            )
        )
        # Extract and convert image from response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                base64_str = base64.b64encode(part.inline_data.data).decode('utf-8')
                return {
                    "image_data_base64": base64_str,
                    "status": "success",
                    "generation_prompt": enhanced_prompt
                }

        return {
            "image_data_base64": None,
            "status": "success",
            "generation_prompt": enhanced_prompt
        }
        
    except Exception as e:
        return {"error": str(e), "status": "failure"}