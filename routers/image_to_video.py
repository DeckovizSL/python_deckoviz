from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from deckoviz_ai.image_to_video._service import generate_video_from_image
from typing import Optional
import os
from utils.token import get_current_user
from schemas.user import User

router = APIRouter(tags=["image-to-video"])

@router.post("/generate")
def generate_image_to_video(
    image: Optional[UploadFile] = File(None, description="Image file to upload (optional)"),
    image_url: Optional[str] = Form(None, description="Image URL (optional)"),
    prompt: str = Form(...),
    max_area: Optional[str] = Form(None),
    fast_mode: Optional[str] = Form(None),
    lora_scale: Optional[float] = Form(None),
    num_frames: Optional[int] = Form(None),
    sample_shift: Optional[int] = Form(None),
    sample_steps: Optional[int] = Form(None),
    frames_per_second: Optional[int] = Form(None),
    sample_guide_scale: Optional[int] = Form(None),
    api_token: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    # Prefer file upload, fallback to URL
    if image is not None:
        image.file.seek(0)
        image_data = image.file.read()
    elif image_url is not None:
        image_data = image_url
    else:
        raise HTTPException(status_code=400, detail="Either image file or image_url must be provided.")
    try:
        result = generate_video_from_image(
            image=image_data,
            prompt=prompt,
            output_dir=os.getcwd(),
            api_token=api_token,
            max_area=max_area,
            fast_mode=fast_mode,
            lora_scale=lora_scale,
            num_frames=num_frames,
            sample_shift=sample_shift,
            sample_steps=sample_steps,
            frames_per_second=frames_per_second,
            sample_guide_scale=sample_guide_scale
        )
        return {
            "status": "success" if result["video_url"] else "failed",
            "video_url": result["video_url"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 