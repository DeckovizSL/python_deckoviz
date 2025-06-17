from fastapi import APIRouter,Depends
from schemas.art import GenerateArtRequest
from runware import Runware,IImageInference
import os
from dotenv import load_dotenv
from schemas.user import User
from utils.token import get_current_user

load_dotenv()

router = APIRouter()


@router.post("/")
async def generate_art(req: GenerateArtRequest,current_user: User = Depends(get_current_user)):
    try:
        # Initialize Runware
        runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
        await runware.connect()
        neg_prompt = ""
        if req.negative_prompt:
            neg_prompt = req.negative_prompt
        else:
            neg_prompt = "blurry, low resolution, pixelated, distorted faces, missing limbs, bad anatomy, extra fingers, low detail, poorly lit, overexposed, underexposed, noisy, artifacts, watermark, cropped, low contrast, flat colors, dull, amateu"
        
        request_image = IImageInference(
                positivePrompt=req.prompt,
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




