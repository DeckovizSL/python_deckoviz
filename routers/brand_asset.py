from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from schemas.user import User
from utils.token import get_current_user
from deckoviz_ai.brand_asset import BrandAssetPrompt, BrandAssetRequest, analyze_logo_image
from schemas.art import GenerateArtRequest
from routers.generate_art import generate_art
import asyncio
from typing import Optional, List
import io

router = APIRouter()

@router.post("/", tags=["Brand Asset"], summary="Generate branded artwork from a description or logo photo")
async def generate_brand_asset(
    logo_description: Optional[str] = Form(None),
    brand_palette: Optional[str] = Form(None),
    visual_use_case: str = Form(...),
    style: Optional[str] = Form(None),
    height: Optional[int] = Form(1024),
    width: Optional[int] = Form(1024),
    logo_photo: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        image_features = None
        if logo_photo is not None:
            image_bytes = await logo_photo.read()
            image_features = analyze_logo_image(image_bytes)

        print(f"DEBUG: brand_palette raw value: {brand_palette}, type: {type(brand_palette)}")
        print(f"DEBUG: logo_description raw value: {logo_description}, type: {type(logo_description)}")

        # Convert brand_palette string to list
        if brand_palette:
            brand_palette_list = [c.strip() for c in brand_palette.split(",") if c.strip()]
        else:
            brand_palette_list = None
        # Normalize logo_description
        if not logo_description:
            logo_description = None

        print(f"DEBUG: brand_palette_list: {brand_palette_list}")
        print(f"DEBUG: logo_description: {logo_description}")

        req = BrandAssetRequest(
            logo_description=logo_description,
            brand_palette=brand_palette_list,
            visual_use_case=visual_use_case,
            style=style,
            height=height if height is not None else 1024,
            width=width if width is not None else 1024,
            image_features=image_features
        )
        brand_asset_service = BrandAssetPrompt()
        asset_result = brand_asset_service.generate_prompts(req)
        art_generation_tasks = []
        for prompt in asset_result.prompts:
            art_req = GenerateArtRequest(
                prompt=prompt,
                negative_prompt=None,
                height=req.height,
                width=req.width
            )
            task = generate_art(art_req, current_user)
            art_generation_tasks.append(task)
        image_results = await asyncio.gather(*art_generation_tasks)
        return image_results
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception occurred: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) 