from fastapi import APIRouter, Depends, HTTPException
from schemas.user import User
from utils.token import get_current_user
from deckoviz_ai.mindscape import MindscapePrompt, MindscapePromptRequest
from schemas.art import GenerateArtRequest
from routers.generate_art import generate_art

router = APIRouter()

@router.post("/generate", tags=["Mindscape"], summary="Generate an inner landscape/mindscape painting from user's mental/emotional state")
async def generate_mindscape(
    req: MindscapePromptRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a symbolic, abstract, or metaphorical painting representing the user's inner world.
    
    This endpoint transforms the user's emotional state, thoughts, personality, internal conflicts, 
    desires, or momentary reflections into a vivid visual artwork.
    
    The user can provide input via:
    - A single descriptive prompt (e.g., "My mind feels like a stormy ocean with moments of sunlight")
    - Emotional states and mental descriptions
    - Inner conflicts and desires
    - Metaphorical descriptions of their mindscape
    """
    try:
        # Handle resolution settings
        if req.resolution:
            if req.resolution.lower() == "1080p":
                req.height = 1152  # 1152 is multiple of 64 and gives 16:9 ratio
                req.width = 2048   # Max allowed width
            elif req.resolution.lower() == "4k":
                req.height = 1152  # Keep within limits but maintain quality
                req.width = 2048
            elif req.resolution.lower() == "8k":
                req.height = 1152  # Max quality within Runware limits
                req.width = 2048
        
        # Generate the mindscape prompt using Gemini
        mindscape_service = MindscapePrompt()
        prompt = mindscape_service.generate_prompt(req)
        
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


@router.post("/generate-journey", tags=["Mindscape"], summary="Generate a multi-frame mindscape journey representing transformation or progression")
async def generate_mindscape_journey(
    req: MindscapePromptRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate multiple frames representing a mindscape journey or transformation.
    
    This endpoint creates a series of symbolic paintings showing progression, 
    transformation, or different aspects of the user's inner world.
    
    Set frames or frame_count to specify how many frames to generate (2-5 recommended).
    """
    try:
        from runware import Runware, IImageInference
        import os
        
        # Handle frame count
        frame_count = req.frames or req.frame_count or 2
        if frame_count < 1:
            frame_count = 1
        if frame_count > 5:  # Limit to prevent too many requests
            frame_count = 5
            
        # Set multiple frames for journey
        req.multiple_frames = True
        req.frame_count = frame_count
        
        # Handle resolution settings
        if req.resolution:
            if req.resolution.lower() == "1080p":
                req.height = 1152  # 1152 is multiple of 64 and gives 16:9 ratio
                req.width = 2048   # Max allowed width
            elif req.resolution.lower() == "4k":
                req.height = 1152  # Keep within limits but maintain quality
                req.width = 2048
            elif req.resolution.lower() == "8k":
                req.height = 1152  # Max quality within Runware limits
                req.width = 2048
        
        # Generate the mindscape prompt using Gemini
        mindscape_service = MindscapePrompt()
        prompt = mindscape_service.generate_prompt(req)
        
        # Initialize Runware directly for multiple images
        runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
        await runware.connect()
        
        # Create negative prompt
        neg_prompt = "blurry, low resolution, pixelated, distorted faces, missing limbs, bad anatomy, extra fingers, low detail, poorly lit, overexposed, underexposed, noisy, artifacts, watermark, cropped, low contrast, flat colors, dull, amateur, text, logos, signatures"
        
        # Generate multiple images for the journey
        request_image = IImageInference(
            positivePrompt=prompt,
            model="civitai:101055@128078",
            numberResults=frame_count,  # This generates multiple images
            negativePrompt=neg_prompt,
            height=req.height,
            width=req.width,
        )
        
        images = await runware.imageInference(requestImage=request_image)
        
        # Add journey metadata to each image
        if isinstance(images, list):
            for i, image in enumerate(images):
                if hasattr(image, '__dict__'):
                    image.__dict__['journey_frame'] = i + 1
                    image.__dict__['total_frames'] = frame_count
                    image.__dict__['journey_type'] = 'mindscape_transformation'
        
        return images
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
