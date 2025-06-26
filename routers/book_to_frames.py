from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from schemas.user import User
from utils.token import get_current_user
from schemas.book_to_frames import BookToFramesRequest
from deckoviz_ai.book_to_frames import BookToFramesService
from runware import Runware, IImageInference
import os
import tempfile
from typing import List

router = APIRouter()

@router.post("/", tags=["BookToFrames"], summary="Generate frames from a book PDF and return images")
async def book_to_frames(
    req: BookToFramesRequest = Depends(),
    pdf_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        # Save uploaded PDF to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await pdf_file.read())
            tmp_path = tmp.name

        # Generate prompts for each frame
        service = BookToFramesService()
        prompts = service.generate_prompts_from_pdf(
            pdf_path=tmp_path,
            start_page=req.start_page,
            end_page=req.end_page,
            num_sections=req.num_frames
        )

        # Initialize Runware
        runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
        await runware.connect()
        neg_prompt = "blurry, low resolution, pixelated, distorted faces, missing limbs, bad anatomy, extra fingers, low detail, poorly lit, overexposed, underexposed, noisy, artifacts, watermark, cropped, low contrast, flat colors, dull, amateur"

        responses = []
        for prompt in prompts:
            request_image = IImageInference(
                positivePrompt=prompt,
                model="civitai:101055@128078",
                numberResults=1,
                negativePrompt=neg_prompt,
                height=req.height,
                width=req.width,
            )
            images = await runware.imageInference(requestImage=request_image)
            responses.append(images)

        os.remove(tmp_path)
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 