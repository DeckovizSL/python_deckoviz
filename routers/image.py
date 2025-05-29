from fastapi import APIRouter, HTTPException
import os
from schemas.image import GenerateRequest, GenerateResponse
from  genai.personal_painter import process_emotion_and_generate_art, PersonalPainter
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="")


@router.post("/create-art", response_model=GenerateResponse)
async def generate_image(req: GenerateRequest):
    # Initialize Personal Painter
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="STABILITY_API_KEY is not set")
    painter = PersonalPainter(api_key=api_key)

    # Generate art and get image bytes
    result = await process_emotion_and_generate_art(painter, req.user_input)
    art = result.get("art", {})
    image_bytes = art.get("image_bytes")
    filename = art.get("filename")
    prompt = art.get("prompt")
    if not image_bytes or not filename:
        raise HTTPException(status_code=400, detail="Image generation failed")

    # Upload bytes directly to GCS
    url = upload_bytes_to_gcs(image_bytes, filename, "personal_painter")
    return GenerateResponse(url=url, prompt=prompt)
