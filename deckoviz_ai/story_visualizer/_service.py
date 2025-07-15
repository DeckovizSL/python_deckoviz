import os
import json
from typing import Dict, Any, Optional
from ..llm import GeminiLLM
from ._prompt import STORY_VISUALIZER_SYSTEM_PROMPT
from runware import Runware, IImageInference

class StoryVisualizerService:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.llm = GeminiLLM(model_name=model_name)

    async def process_story_segment(self, text: str, previous_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process the last 20 seconds of story text and generate a visualization prompt and image.
        Optionally use previous_context for continuity.
        """
        # Step 1: Build the LLM prompt
        context_str = f"\nPrevious context: {json.dumps(previous_context)}" if previous_context else ""
        llm_prompt = f"{STORY_VISUALIZER_SYSTEM_PROMPT}\n{text}{context_str}"

        # Step 2: Get the enhanced prompt from LLM
        try:
            enhanced_prompt = self.llm._call(llm_prompt)
        except Exception as e:
            enhanced_prompt = text  # fallback to raw text

        # Step 3: Generate image using Runware
        runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
        await runware.connect()
        neg_prompt = "abstract patterns, random shapes, meaningless designs, geometric patterns, swirls, spirals, kaleidoscope, mandala, fractal, blurry, low resolution, pixelated, distorted, deformed, bad anatomy, poorly drawn, amateur, sketchy, rough, unfinished, low detail, flat lighting, overexposed, underexposed, noisy, grainy, artifacts, watermark, signature, text, letters, words, cropped, borders, frame, low contrast, washed out colors, dull, boring, generic, cliché, bad composition, cluttered, messy, chaotic, unclear subject, no focal point, confusing"
        request_image = IImageInference(
            positivePrompt=enhanced_prompt,
            model="civitai:101055@128078",
            numberResults=1,
            negativePrompt=neg_prompt,
            height=768,
            width=1536,
        )
        try:
            images = await runware.imageInference(requestImage=request_image)
            print(f"[DEBUG] Runware imageInference response: {images}")
            if images and hasattr(images[0], 'imageURL'):
                image_url = images[0].imageURL
            else:
                print(f"[DEBUG] No imageURL found in images[0]: {getattr(images[0], '__dict__', images[0]) if images else images}")
                image_url = ""
        except Exception as e:
            print(f"[DEBUG] Exception during imageInference: {e}")
            image_url = ""
        return {"prompt": enhanced_prompt, "image_url": image_url} 