from fastapi import APIRouter,Depends
from schemas.art import GenerateArtRequest
from runware import Runware,IImageInference
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


@router.post("/")
async def generate_art(req: GenerateArtRequest = Depends()):
    try:
        # Initialize Runware
        runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
        await runware.connect()
        
        request_image = IImageInference(
                positivePrompt=req.prompt,
                model="civitai:101055@128078",
                numberResults=1,
                negativePrompt=req.negative_prompt,
                height=req.height,
                width=req.width,
          )
        images = await runware.imageInference(requestImage=request_image)
        await runware.disconnect()
        images = images["images"][0]
        return images
    except Exception as e:
        return {"error": str(e)}




