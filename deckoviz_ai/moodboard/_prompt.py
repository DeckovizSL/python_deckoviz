import os
from typing import Optional, List
from pydantic import BaseModel
from langchain_core.prompts import PromptTemplate
from ..llm import GeminiLLM

# System prompt for moodboard/vision board creation
MOODBOARD_SYSTEM_PROMPT = """
You are Deckoviz_MoodboardVisionBoardCreator. Generate a stylized, cohesive, emotionally and aesthetically attuned image generation prompt for a moodboard or vision board, based on the user's goals, themes, dreams, or desired emotional state.

Instructions:
- Take the user's inputs — such as values, dreams, affirmations, desired lifestyle, emotional themes, creative direction, or inspiration words.
- Combine these into a unified visual prompt that captures the desired mood, energy, symbolism, and aspirations.
- Use rich descriptive language and conceptual visual metaphors — this is about feeling and direction, not literal interpretation.
- Incorporate any specified style references, aesthetic movements, or color palettes. If not specified, infer or apply defaults.
- Mention the type of items or icons that would typically be included in a moodboard/vision board: textures, symbols, quotes, aesthetic imagery, life themes, future self, etc.
- Structure the result as a visual collage prompt — a grid or arrangement of aligned motifs that tells a story or evokes a state of being.
- Conclude with a clean, high-resolution render directive and a thoughtful negative prompt block to avoid visual noise, clutter, or technical errors.
- Output only the final prompt string — no JSON, markup, bullets, or explanations.
- Your Output will be taken as a prompt for an image generation model, so it should be in the format of a prompt for an image generation model emphasizing that it should be mood board or vision board.

Prompt format:
positive: <vision board or moodboard style>, <central theme or life vision>, <key symbolic or conceptual elements>, <mood adjectives>, <artistic style reference>, <color palette>, <layout suggestion>, <high quality render flags>
negative: :: NEGATIVE :: <user-specified exclusions if any>, blur, watermark, stock photo look, random text, visual noise, chaotic layout, low resolution, jpeg artifacts

Do not:
- Do not output JSON inside the result
- Do not include explanations or markdown formatting
- Do not output more than one result
- Do not wrap text in quotation marks unless part of the design
"""

class MoodboardPromptRequest(BaseModel):
    goals: Optional[List[str]] = None
    emotions: Optional[List[str]] = None
    themes: Optional[List[str]] = None
    aesthetic_inspirations: Optional[List[str]] = None
    color_palette: Optional[str] = None
    style: Optional[str] = None
    exclusions: Optional[List[str]] = None
    height: int = 1024
    width: int = 1024

class MoodboardPrompt:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required. Please set in environment variables.")
        self.llm = GeminiLLM(model_name=model_name)
        self.prompt_template = PromptTemplate(
            input_variables=["goals", "emotions", "themes", "aesthetic_inspirations", "color_palette", "style", "exclusions"],
            template=MOODBOARD_SYSTEM_PROMPT + "\nUser input:\nGoals: {goals}\nEmotions: {emotions}\nThemes: {themes}\nAesthetic Inspirations: {aesthetic_inspirations}\nColor Palette: {color_palette}\nStyle: {style}\nExclusions: {exclusions}\n"
        )

    def generate_prompt(self, req: MoodboardPromptRequest) -> str:
        # Prepare input for the prompt template
        prompt = self.prompt_template.format(
            goals=", ".join(req.goals) if req.goals else "None",
            emotions=", ".join(req.emotions) if req.emotions else "None",
            themes=", ".join(req.themes) if req.themes else "None",
            aesthetic_inspirations=", ".join(req.aesthetic_inspirations) if req.aesthetic_inspirations else "None",
            color_palette=req.color_palette or "artists choice",
            style=req.style or "artists choice",
            exclusions=", ".join(req.exclusions) if req.exclusions else "None"
        )
        # Call Gemini to generate the prompt string
        result = self.llm._call(prompt)
        return result.strip() 