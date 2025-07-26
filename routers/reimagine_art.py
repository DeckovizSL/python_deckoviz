from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import base64
import os
from typing import Optional
from runware import Runware, IImageInference
from utils.token import get_current_user
from schemas.user import User

router = APIRouter(tags=["reimagine-art"])

@router.post(
    "/reimagine",
    summary="Reimagine an uploaded photo in a custom art style (Runware)",
    response_description="Status and image URL of the reimagined artwork.",
    tags=["reimagine-art"],
)
async def reimagine_art(
    image: UploadFile = File(..., description="Input image to reimagine in a new art style."),
    style: str = Form(..., description="Art style to apply, e.g. 'anime', 'cartoon', 'impressionist', etc."),
    height: Optional[int] = Form(768, description="Height of the output image. Default: 1344."),
    width: Optional[int] = Form(1344, description="Width of the output image. Default: 768."),
    current_user: User = Depends(get_current_user)
):
    """
    ### Reimagine a Photo in a Custom Art Style (Runware)
    Upload a photo and specify an art style. The image will be reimagined using the Runware model `runware:101@1`.

    **How it works:**
    - The prompt is automatically composed as: `a painting in the style {style}`.
    - The uploaded image is used as the seed image for the transformation.
    - You can optionally specify output height and width (defaults: 1344x768).

    **Example Request (POSTMAN):**
    - Method: POST
    - URL: `/reimagine-art/reimagine`
    - Form-data:
        - image: [your file]
        - style: "anime"
        - height: 1344 (optional)
        - width: 768 (optional)

    **Example Response:**
    ```json
    {
      "data": [
        {
          "taskType": "imageInference",
          "taskUUID": "...",
          "status": "success",
          "imageUUID": "...",
          "imageURL": "https://im.runware.ai/image/ii/xxxx.jpg",
          "cost": 0.0013
        }
      ]
    }
    ```
    """
    try:
        image_bytes = await image.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        positive_prompt = f"a painting in the style {style}, faithful to the original"
        runware = Runware(api_key=os.getenv("RUNWARE_API_KEY"))
        await runware.connect()
        request_image = IImageInference(
            positivePrompt=positive_prompt,
            model="runware:101@1",
            numberResults=1,
            height=height,
            width=width,
            seedImage=image_b64,
            outputFormat="JPEG",
            steps=28,
            CFGScale=3.5,
            scheduler="FlowMatchEulerDiscreteScheduler",
            strength=0.8,
            includeCost=True,
            outputType="URL",
        )
        result = await runware.imageInference(requestImage=request_image)
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
            }
        ) 