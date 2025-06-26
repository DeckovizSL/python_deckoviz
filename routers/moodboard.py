from fastapi import APIRouter, Depends
from schemas.user import User
from utils.token import get_current_user
from deckoviz_ai.moodboard import MoodboardPrompt, MoodboardPromptRequest
from schemas.art import GenerateArtRequest
from routers.generate_art import generate_art
from fastapi import HTTPException

router = APIRouter()

@router.post("/", tags=["Moodboard"], summary="Generate a moodboard/vision board image from user input")
async def generate_moodboard(
    req: MoodboardPromptRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # Generate the moodboard prompt using Gemini
        moodboard_service = MoodboardPrompt()
        prompt = moodboard_service.generate_prompt(req)
        # Compose the art generation request
        art_req = GenerateArtRequest(
            prompt=prompt,
            negative_prompt=None,  # The prompt already includes negative block
            height=req.height,
            width=req.width
        )
        # Call the generate_art endpoint logic directly
        return await generate_art(art_req, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))