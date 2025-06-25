from fastapi import APIRouter, Depends, HTTPException
from schemas.user import User
from utils.token import get_current_user
from deckoviz_ai.brand_asset import BrandAssetPrompt, BrandAssetRequest
from schemas.art import GenerateArtRequest
from routers.generate_art import generate_art
import asyncio

router = APIRouter()

@router.post("/", tags=["Brand Asset"], summary="Generate branded artwork from a description")
async def generate_brand_asset(
    req: BrandAssetRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Generate one or more prompts for the brand asset
        brand_asset_service = BrandAssetPrompt()
        asset_result = brand_asset_service.generate_prompts(req)

        # 2. Create art generation tasks for each prompt
        art_generation_tasks = []
        for prompt in asset_result.prompts:
            art_req = GenerateArtRequest(
                prompt=prompt,
                negative_prompt=None,  # The prompt already includes a negative block
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