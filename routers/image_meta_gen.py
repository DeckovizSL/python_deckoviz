from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, HttpUrl
from schemas.user import User
from utils.token import get_current_user
from deckoviz_ai.image_meta_gen._generator import ImageMetaGenerator

router = APIRouter()

class ImageUrlRequest(BaseModel):
    url: HttpUrl

def get_generator():
    """Dependency injector for the ImageMetaGenerator."""
    return ImageMetaGenerator()

@router.post("/generate-from-upload", summary="Generate metadata from an uploaded image")
async def generate_from_upload(
    image: UploadFile = File(...),
    generator: ImageMetaGenerator = Depends(get_generator),
    current_user: User = Depends(get_current_user)
):
    try:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Image file is empty.")
        
        metadata = generator.generate_from_bytes(image_bytes)
        return {"metadata": metadata}
    except Exception as e:
        print(f"Error in /generate-from-upload: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.post("/generate-from-url", summary="Generate metadata from an image URL")
async def generate_from_url(
    request: ImageUrlRequest,
    generator: ImageMetaGenerator = Depends(get_generator),
    current_user: User = Depends(get_current_user)
):
    try:
        metadata = generator.generate_from_url(str(request.url))
        return {"metadata": metadata}
    except Exception as e:
        print(f"Error in /generate-from-url: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}") 