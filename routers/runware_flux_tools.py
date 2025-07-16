from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from deckoviz_ai.runware_flux_tools._service import RunwareFluxToolsService
from deckoviz_ai.runware_flux_tools._schemas import FluxFillRequest, FluxCannyRequest, FluxDepthRequest, FluxReduxRequest, FluxImageResponse
from deckoviz_ai.runware_flux_tools._prompt import build_flux_prompt
import base64
import logging

router = APIRouter(tags=["Runware FLUX Tools"])

service = RunwareFluxToolsService()

@router.post("/fill", response_model=FluxImageResponse)
async def flux_fill(
    prompt: str = Form(...),
    style: str = Form(None),
    image: UploadFile = File(...),
    mask: UploadFile = File(...),
    width: int = Form(1024),
    height: int = Form(1024),
    steps: int = Form(30)
):
    try:
        image_b64 = base64.b64encode(await image.read()).decode()
        mask_b64 = base64.b64encode(await mask.read()).decode()
        full_prompt = build_flux_prompt(prompt, style)
        result = await service.generate_flux_image(tool="fill", prompt=full_prompt, image_b64=image_b64, mask_b64=mask_b64, width=width, height=height, steps=steps)
        image_url = result.get("images", [{}])[0].get("imageURL") if result.get("images") else None
        return FluxImageResponse(status="success", image_url=image_url, raw_response=result)
    except Exception as e:
        return FluxImageResponse(status="error", detail=str(e))

@router.post("/canny", response_model=FluxImageResponse)
async def flux_canny(
    prompt: str = Form(...),
    style: str = Form(None),
    image: UploadFile = File(...),
    width: int = Form(1024),
    height: int = Form(1024),
    steps: int = Form(30)
):
    try:
        image_b64 = base64.b64encode(await image.read()).decode()
        full_prompt = build_flux_prompt(prompt, style)
        result = await service.generate_flux_image(tool="canny", prompt=full_prompt, image_b64=image_b64, width=width, height=height, steps=steps)
        image_url = result.get("images", [{}])[0].get("imageURL") if result.get("images") else None
        return FluxImageResponse(status="success", image_url=image_url, raw_response=result)
    except Exception as e:
        return FluxImageResponse(status="error", detail=str(e))

@router.post("/depth", response_model=FluxImageResponse)
async def flux_depth(
    prompt: str = Form(...),
    style: str = Form(None),
    image: UploadFile = File(...),
    width: int = Form(1024),
    height: int = Form(1024),
    steps: int = Form(30)
):
    try:
        image_b64 = base64.b64encode(await image.read()).decode()
        full_prompt = build_flux_prompt(prompt, style)
        result = await service.generate_flux_image(tool="depth", prompt=full_prompt, image_b64=image_b64, width=width, height=height, steps=steps)
        image_url = result.get("images", [{}])[0].get("imageURL") if result.get("images") else None
        return FluxImageResponse(status="success", image_url=image_url, raw_response=result)
    except Exception as e:
        return FluxImageResponse(status="error", detail=str(e))

@router.post("/redux", response_model=FluxImageResponse)
async def flux_redux(
    prompt: str = Form(None),
    style: str = Form(None),
    image: UploadFile = File(...),
    width: int = Form(1024),
    height: int = Form(1024),
    steps: int = Form(30)
):
    try:
        image_b64 = base64.b64encode(await image.read()).decode()
        full_prompt = build_flux_prompt(prompt, style) if prompt or style else "__BLANK__"
        result = await service.generate_flux_image(tool="redux", prompt=full_prompt, image_b64=image_b64, width=width, height=height, steps=steps)
        # Log the full raw response for debugging
        logging.warning(f"[FLUX Redux] Raw response: {result}")
        # Try to extract image URL from common locations
        image_url = None
        if isinstance(result, dict):
            if "images" in result and result["images"]:
                image_url = result["images"][0].get("imageURL")
            elif "data" in result and result["data"]:
                image_url = result["data"][0].get("imageURL")
        logging.warning(f"[FLUX Redux] Extracted image_url: {image_url}")
        return FluxImageResponse(status="success", image_url=image_url, raw_response=result)
    except Exception as e:
        logging.error(f"[FLUX Redux] Exception: {e}")
        return FluxImageResponse(status="error", detail=str(e)) 