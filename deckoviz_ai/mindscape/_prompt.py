import os
from typing import Optional, List
from pydantic import BaseModel
from langchain_core.prompts import PromptTemplate
from ..llm import GeminiLLM

# System prompt for inner landscape/mindscape painting creation - optimized for simple image models
MINDSCAPE_SYSTEM_PROMPT = """
You are a visual translator that converts emotional states and mental descriptions into concrete, visual image descriptions that any image generation model can easily understand.

Your job is to translate emotions, feelings, and mental states into simple visual elements:

TRANSLATION RULES:
- Convert emotions to visual scenes, objects, and environments
- Use concrete nouns: mountains, oceans, forests, buildings, lights, shadows, paths, bridges
- Use clear visual adjectives: dark, bright, stormy, calm, broken, flowing, ascending, descending
- Avoid abstract concepts like "anxiety" or "confidence" - instead describe what these LOOK like
- Focus on landscapes, architecture, natural phenomena, and symbolic objects
- Use cinematic lighting and atmosphere descriptions

EMOTION TO VISUAL MAPPING:
- Anxiety → stormy skies, turbulent waters, jagged rocks, narrow passages, dark clouds
- Confidence → bright sunlight, tall mountains, clear paths, golden light, open spaces
- Confusion → fog, maze-like structures, multiple paths, swirling mists, fractured landscapes
- Peace → calm lakes, gentle hills, soft lighting, flowing rivers, clear skies
- Transformation → bridges, doorways, changing weather, dawn/dusk, metamorphosis in nature
- Inner conflict → split landscapes, contrasting lighting, broken structures, opposing elements

OUTPUT FORMAT:
Generate a single, clear visual description that focuses on:
1. Main landscape/environment (forest, desert, ocean, city, etc.)
2. Lighting and atmosphere (golden hour, stormy, misty, bright, shadowy)
3. Key visual elements (paths, buildings, natural features, objects)
4. Colors and mood through visuals (not emotions)
5. Composition and perspective

EXAMPLE TRANSFORMATIONS:
- "I feel anxious" → "a narrow rocky canyon with dark storm clouds overhead, jagged cliffs on both sides, turbulent river below"
- "becoming confident" → "a mountain path leading from shadowy valley up to bright summit with golden sunlight"
- "inner conflict" → "a landscape split down the middle, one half in darkness with thorny trees, other half in bright light with blooming flowers"

DO NOT use emotional words in the final output. Only describe what can be visually seen and painted.
ALWAYS end with art style and technical specifications.
"""

class MindscapePromptRequest(BaseModel):
    """Request model for mindscape/inner landscape generation"""
    # Simple format - just provide a single prompt
    prompt: Optional[str] = None
    
    # Detailed format - for more specific mindscape creation
    emotional_state: Optional[str] = None
    mental_description: Optional[str] = None
    inner_conflicts: Optional[List[str]] = None
    desires_aspirations: Optional[List[str]] = None
    current_mood: Optional[str] = None
    metaphorical_description: Optional[str] = None
    personality_traits: Optional[List[str]] = None
    
    # Style and framing options
    style: Optional[str] = None  # alias for style_preference
    style_preference: Optional[str] = None
    frames: Optional[int] = None  # alias for frame_count
    multiple_frames: Optional[bool] = False
    frame_count: Optional[int] = 1
    
    # Resolution options
    resolution: Optional[str] = "1080p"  # 1080p, 4k, 8k
    height: int = 1152  # Default to Runware-compatible landscape
    width: int = 2048   # Max allowed width for best quality

class MindscapePrompt:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required. Please set in environment variables.")
        self.llm = GeminiLLM(model_name=model_name)
        self.prompt_template = PromptTemplate(
            input_variables=[
                "emotional_state", 
                "mental_description", 
                "inner_conflicts", 
                "desires_aspirations", 
                "current_mood", 
                "metaphorical_description", 
                "personality_traits", 
                "style_preference", 
                "multiple_frames"
            ],
            template=MINDSCAPE_SYSTEM_PROMPT + "\nUser input:\nEmotional State: {emotional_state}\nMental Description: {mental_description}\nInner Conflicts: {inner_conflicts}\nDesires/Aspirations: {desires_aspirations}\nCurrent Mood: {current_mood}\nMetaphorical Description: {metaphorical_description}\nPersonality Traits: {personality_traits}\nStyle Preference: {style_preference}\nMultiple Frames: {multiple_frames}\n"
        )

    def generate_prompt(self, req: MindscapePromptRequest) -> str:
        """Generate mindscape prompt using Gemini"""
        
        # Handle resolution settings
        if req.resolution:
            if req.resolution.lower() == "1080p":
                req.height = 1152  # 1152 is multiple of 64 and gives 16:9 ratio
                req.width = 2048   # Max allowed width
            elif req.resolution.lower() == "4k":
                req.height = 1152  # Keep within limits but maintain quality
                req.width = 2048
            elif req.resolution.lower() == "8k":
                req.height = 1152  # Max quality within Runware limits
                req.width = 2048
        
        # Handle style aliases
        style_pref = req.style or req.style_preference or "surrealist"
        
        # Handle frame count aliases
        frame_count = req.frames or req.frame_count or 1
        multiple_frames = req.multiple_frames or (frame_count > 1)
        
        # Use simple prompt if provided, otherwise build from detailed fields
        if req.prompt:
            # Simple format - use the direct prompt
            user_input = f"User Description: {req.prompt}"
        else:
            # Detailed format - build from individual fields
            user_input = f"""User input:
Emotional State: {req.emotional_state or 'None'}
Mental Description: {req.mental_description or 'None'}
Inner Conflicts: {', '.join(req.inner_conflicts) if req.inner_conflicts else 'None'}
Desires/Aspirations: {', '.join(req.desires_aspirations) if req.desires_aspirations else 'None'}
Current Mood: {req.current_mood or 'None'}
Metaphorical Description: {req.metaphorical_description or 'None'}
Personality Traits: {', '.join(req.personality_traits) if req.personality_traits else 'None'}"""

        # Create the full prompt for simple visual translation
        full_prompt = f"""{MINDSCAPE_SYSTEM_PROMPT}

{user_input}
Style Preference: {style_pref}
Multiple Frames: {'Yes' if multiple_frames else 'No'}
Frame Count: {frame_count}

TASK: Translate the above emotional/mental description into a simple, concrete visual scene description that any image model can understand. Focus on landscapes, objects, lighting, and visual elements. Do not use emotional words in your output.

If multiple frames are requested, describe {frame_count} different visual scenes that show progression or transformation through concrete visual changes (like weather changing, paths leading somewhere, structures transforming, etc.).

End your description with: ", {style_pref} art style, {req.width}x{req.height} resolution, cinematic lighting"
"""
        
        # Call Gemini to generate the prompt string
        result = self.llm._call(full_prompt)
        
        # Clean up the result and ensure it's visual-focused
        result = result.strip()
        
        # Add negative prompt for better image generation
        if "NEGATIVE" not in result:
            result += " :: NEGATIVE :: blurry, low quality, text, watermark, distorted, abstract symbols, emotional words, unclear shapes, poor lighting, oversaturated"
        
        return result
