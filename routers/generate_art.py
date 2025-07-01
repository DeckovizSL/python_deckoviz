from fastapi import APIRouter,Depends
from schemas.art import GenerateArtRequest
from runware import Runware,IImageInference
import os
from dotenv import load_dotenv
from schemas.user import User
from utils.token import get_current_user
from langchain_core.prompts import PromptTemplate
from deckoviz_ai.llm import GeminiLLM
import google.generativeai as genai

load_dotenv()

router = APIRouter()


@router.post("/")
async def generate_art(req: GenerateArtRequest,current_user: User = Depends(get_current_user)):
    try:
        # Step 1: Use Gemini API directly to generate a detailed image prompt from the user's input
        SYSTEM_PROMPT = """
You are an expert visual scene describer. Given a mood, concept, or short phrase, generate a detailed, vivid, and visually rich description suitable as a prompt for an image generation model. Use concrete visual elements, atmosphere, style, and composition cues. Output only the prompt string.
"""
        prompt_template = SYSTEM_PROMPT + "\nMood/Concept: {}\n".format(req.prompt)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt_template)
        if hasattr(response, 'text'):
            detailed_prompt = response.text.strip()
        else:
            detailed_prompt = response.parts[0].text.strip()

        # Initialize Runware
        runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
        await runware.connect()
        neg_prompt = ""
        if req.negative_prompt:
            neg_prompt = req.negative_prompt
        else:
            neg_prompt = "blurry, low resolution, pixelated, distorted faces, missing limbs, bad anatomy, extra fingers, low detail, poorly lit, overexposed, underexposed, noisy, artifacts, watermark, cropped, low contrast, flat colors, dull, amateu"
        
        request_image = IImageInference(
                positivePrompt=detailed_prompt,
                model="civitai:101055@128078",
                numberResults=1,
                negativePrompt=neg_prompt,
                height=req.height,
                width=req.width,
          )
        images = await runware.imageInference(requestImage=request_image)
        return images
    except Exception as e:
        return {"error": str(e)}




