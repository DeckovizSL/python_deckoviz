import os
import io
import json
import requests
from typing import Dict, Any
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class ImageMetaGenerator:
    """
    A service to generate metadata for images using Google Gemini.
    Built from scratch to be simple and robust.
    """

    def __init__(self, api_key: str = None, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required. Please set it in your environment variables.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.prompt = """
Analyze the provided image and generate detailed, accurate metadata.
The output must be a single, raw JSON object containing the following fields:
- "title": A concise, descriptive title for the image.
- "description": A detailed one-paragraph description of the image content, including objects, setting, and style.
- "tags": A list of at least 10 relevant keywords and tags (as a JSON array of strings).
- "mood_tags": A JSON array of 3-5 keywords describing the emotional tones and feelings of the image (e.g., ["Joyful", "Vibrant", "Energetic"], ["Calm", "Serene", "Peaceful"], ["Mysterious", "Dark", "Ominous"]).

Do not include markdown formatting like ```json or any other text outside of the JSON object.
"""

    def _get_image_bytes_from_url(self, url: str) -> bytes:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        return response.content

    def _prepare_image_for_gemini(self, image_bytes: bytes) -> Image.Image:
        image = Image.open(io.BytesIO(image_bytes))
        return image
    
    def _clean_json_response(self, raw_response: str) -> Dict[str, Any]:
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:].strip()
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3].strip()
        
        return json.loads(clean_response)

    def generate_from_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        image = self._prepare_image_for_gemini(image_bytes)
        response = self.model.generate_content([self.prompt, image])
        
        raw_text = response.text if hasattr(response, 'text') else response.parts[0].text
        
        return self._clean_json_response(raw_text)

    def generate_from_url(self, url: str) -> Dict[str, Any]:
        image_bytes = self._get_image_bytes_from_url(url)
        return self.generate_from_bytes(image_bytes) 