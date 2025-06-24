from fastapi import APIRouter, Depends, HTTPException
from schemas.user import User
from utils.token import get_current_user
from deckoviz_ai.poster import PosterPrompt, PosterPromptRequest
from schemas.art import GenerateArtRequest
from routers.generate_art import generate_art

router = APIRouter()

@router.post("/", tags=["Poster"], summary="Generate a poster image from user input")
async def generate_poster(
    req: PosterPromptRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Generate the poster prompt using Gemini
        poster_service = PosterPrompt()
        prompt = poster_service.generate_prompt(req)

        # 2. Compose the art generation request
        art_req = GenerateArtRequest(
            prompt=prompt,
            negative_prompt=None,  # The prompt already includes a negative block
            height=req.height,
            width=req.width
        )

        # 3. Call the generate_art endpoint logic directly
        return await generate_art(art_req, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 