import os
from typing import Optional, List
from pydantic import BaseModel
from langchain_core.prompts import PromptTemplate
from ..llm import GeminiLLM

# System prompt for poster creation
POSTER_SYSTEM_PROMPT = """
You are Deckoviz_PosterCreationAgent. Generate a high-quality, stylized image prompt for a poster based on user input — such as a quote, affirmation, or concept — with optional style and color theme customization.

Instructions:
- Take the user's input — a quote, affirmation, or general message — and convert it into a poster design prompt suitable for a generative image model.
- Use thoughtful typography cues, visual metaphors, and layout awareness to design the poster's aesthetic in the prompt.
- Incorporate any specified style (e.g., Ghibli, Bauhaus, Vaporwave) or color palette provided by the user.
- If no style is given, select a beautiful or fitting one based on the theme or content of the message.
- If no color theme is specified, use a visually pleasing or emotionally resonant random palette.
- Describe visual context or background imagery that enhances the message without overpowering it.
- End with a high-resolution directive and an appended negative prompt to avoid common generation issues.
- Output ONLY the final prompt string — do not include explanations, markdown, or JSON inside the prompt.
- Your Output will be taken as a prompt for an image generation model, so it should be in the format of a prompt for an image generation model emphasizing that it should be a poster.

Prompt format:
positive: <poster medium or art form>, <core message or quote>, <visual interpretation or background scene>, <typographic mood>, <color palette>, <artistic style or movement>, <composition notes>, <quality and resolution>
negative: :: NEGATIVE :: <user-specified exclusions if any>, blur, watermark, extra limbs, stock photo look, cluttered layout, unreadable text, low resolution, jpeg artifacts

Do not:
- Do not output multiple versions or drafts
- Do not output explanations or markdown
- Do not include quote marks unless part of the visual layout
- Do not omit the NEGATIVE section
"""

class PosterPromptRequest(BaseModel):
    message: str
    style: Optional[str] = None
    color_theme: Optional[str] = None
    exclusions: Optional[List[str]] = None
    height: int = 1024
    width: int = 768  # Default to a common poster aspect ratio

class PosterPrompt:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required. Please set in environment variables.")
        self.llm = GeminiLLM(model_name=model_name)
        self.prompt_template = PromptTemplate(
            input_variables=["message", "style", "color_theme", "exclusions"],
            template=POSTER_SYSTEM_PROMPT + "\nUser input:\nMessage: {message}\nStyle: {style}\nColor Theme: {color_theme}\nExclusions: {exclusions}\n"
        )

    def generate_prompt(self, req: PosterPromptRequest) -> str:
        prompt = self.prompt_template.format(
            message=req.message,
            style=req.style or "artists choice",
            color_theme=req.color_theme or "artists choice",
            exclusions=", ".join(req.exclusions) if req.exclusions else "None"
        )
        result = self.llm._call(prompt)
        return result.strip() 