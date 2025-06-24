from fastapi import APIRouter, Depends, HTTPException
from schemas.user import User
from utils.token import get_current_user
from deckoviz_ai.dream_visualizer import DreamVisualizerPrompt, DreamVisualizerRequest
from schemas.art import GenerateArtRequest
from routers.generate_art import generate_art
import asyncio

router = APIRouter()

@router.post("/", tags=["Dream Visualizer"], summary="Generate a dream sequence from a description")
async def generate_dream_sequence(
    req: DreamVisualizerRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Generate one or more prompts for the dream
        dream_service = DreamVisualizerPrompt()
        dream_result = dream_service.generate_prompts(req)

        # 2. Create art generation tasks for each prompt
        art_generation_tasks = []
        for prompt in dream_result.prompts:
            art_req = GenerateArtRequest(
                prompt=prompt,
                negative_prompt=None,  # Negative prompt is already in the generated prompt
                height=req.height,
                width=req.width
            )
            task = generate_art(art_req, current_user)
            art_generation_tasks.append(task)

        # 3. Execute all art generation tasks concurrently
        image_results = await asyncio.gather(*art_generation_tasks)
        
        return image_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 