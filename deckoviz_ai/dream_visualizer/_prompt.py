import os
import json
from typing import Optional, List
from pydantic import BaseModel, Field
from ..llm import GeminiLLM

# System prompt for dream visualization
DREAM_VISUALIZER_SYSTEM_PROMPT = """
You are Deckoviz_VisualizeDreamsAgent. Convert a user's narrated dream into a highly evocative, symbolic, and stylistically rich visual prompt — generating either a single artwork or a series of frames that represent different stages or scenes of the dream.

Your primary goal is to produce a JSON object containing a list of strings, where each string is a complete and detailed prompt for an image generation model.

Instructions:
- The user will describe a dream. Extract the emotional themes, visual symbols, environments, and characters.
- Decide if the dream is best represented as a single scene or multiple frames.
- Translate the dream into vivid visual storytelling using metaphor, surrealism, and symbolic landscapes.
- If the user specifies a style, use it. Otherwise, select a fitting one based on the dream's tone.
- Ensure the dream's emotional essence is reflected through lighting, composition, and tone.
- Maintain visual coherence across all frames if generating a sequence.
- Conclude each prompt with ultra-high resolution render flags and a negative prompt section.
- Output ONLY a valid JSON object like this: {"prompts": ["prompt 1 text...", "prompt 2 text..."]}. Do not add any other text, explanations, or markdown.
"""

class DreamVisualizerRequest(BaseModel):
    dream_description: str
    style: Optional[str] = None
    height: int = 1024
    width: int = 1024

class DreamResult(BaseModel):
    prompts: List[str] = Field(description="A list of one or more image generation prompts for the dream sequence.")

class DreamVisualizerPrompt:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required. Please set in environment variables.")
        self.llm = GeminiLLM(model_name=model_name)

    def generate_prompts(self, req: DreamVisualizerRequest) -> DreamResult:
        """
        Generates one or more prompts for a dream visualization with robust parsing.
        """
        style = req.style or "artists choice based on dream tone"
        # Manually construct the prompt.
        final_prompt = (
            f"{DREAM_VISUALIZER_SYSTEM_PROMPT}\n\n"
            f"User input:\n"
            f"Dream Description: {req.dream_description}\n"
            f"Style: {style}\n"
        )

        # Call the LLM directly.
        raw_result = self.llm._call(final_prompt)
        
        try:
            # Attempt to parse the LLM output as JSON. This is the ideal case.
            clean_json_string = raw_result.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json_string)
            parsed_result = DreamResult.model_validate(data)
        except Exception:
            # If any error occurs (JSON decoding, validation, etc.),
            # assume the LLM returned a single, raw prompt string as a fallback.
            parsed_result = DreamResult(prompts=[raw_result.strip()])
            
        return parsed_result 