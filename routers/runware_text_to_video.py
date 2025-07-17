from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import aiohttp
import os
import uuid
from typing import Optional, Literal
from schemas.user import User
from utils.token import get_current_user

router = APIRouter(tags=["runware-text-to-video"])

STYLE_PROMPTS = {
    "3d": "A 3D animated scene of {subject}, Pixar style, high quality, detailed lighting, smooth motion",
    "2d": "A 2D cartoon animation of {subject}, vibrant colors, hand-drawn style, smooth animation",
    "cinematic": "A cinematic shot of {subject}, dramatic lighting, film look, shallow depth of field, high resolution",
    "motion": "A dynamic action scene of {subject}, motion blur, fast camera movement, energetic, realistic lighting"
}

@router.post(
    "/generate",
    summary="Generate a video from a text prompt using Runware (Text-to-Video, with style)",
    response_description="Submission status and taskUUID for polling.",
    tags=["runware-text-to-video"],
)
async def runware_text_to_video_generate(
    subject: str = Form(..., description="Main subject or scene for the video, e.g. 'a cat playing piano', 'a robot dancing'."),
    style: Literal["3d", "2d", "cinematic", "motion"] = Form("cinematic", description="Video style: '3d', '2d', 'cinematic', or 'motion'. Default: cinematic."),
    duration: int = Form(..., description="Duration of the video in seconds. See model limits (e.g., 5-10s typical)."),
    width: Optional[int] = Form(1280, description="Width of the video. Default: 1280."),
    height: Optional[int] = Form(720, description="Height of the video. Default: 720."),
    model: Optional[str] = Form("klingai:1@1", description="Runware video model to use. Default: klingai:1@1."),
    current_user: User = Depends(get_current_user),
):
    """
    ### Runware Text-to-Video Generation (with Style)
    **Authentication required.** Only logged-in users can access this endpoint.

    Submit a video generation task using a subject and a style preset. The style controls the overall look and feel of the video via prompt engineering.

    **Supported styles:**
    - '3d': 3D animation (Pixar style)
    - '2d': 2D cartoon animation
    - 'cinematic': Cinematic/film look
    - 'motion': Dynamic action/motion video

    **Recommended Flow:**
    1. **POST** to `/runware-text-to-video/generate` with your subject, style, and parameters.
    2. Receive a `taskUUID` in the response.
    3. **POST** to `/runware-image-to-video/get-response` (same as image-to-video) with the `taskUUID` to poll for status.
    4. When status is `success`, retrieve the `videoURL` from the response.

    **Parameters:**
    - `subject`: Main subject or scene (e.g., 'a cat playing piano').
    - `style`: One of '3d', '2d', 'cinematic', 'motion'.
    - `duration`: Video duration in seconds (model-dependent, e.g., 5-10s typical).
    - `width`, `height`: Video resolution. Default: 1280x720.
    - `model`: Runware video model. Default: klingai:1@1.

    **Example Request (POSTMAN):**
    - Method: POST
    - URL: `/runware-text-to-video/generate`
    - Headers: `Authorization: Bearer <your_token>`
    - Form-data:
        - subject: "a cat playing piano"
        - style: "3d"
        - duration: 6
        - width: 1280
        - height: 720
        - model: "klingai:1@1" (optional)

    **Example Response:**
    ```json
    {
      "data": [
        { "taskType": "videoInference", "taskUUID": "..." }
      ]
    }
    ```
    Use the `taskUUID` to poll for results at `/runware-image-to-video/get-response`.
    """
    if style not in STYLE_PROMPTS:
        return JSONResponse(status_code=400, content={"status": "error", "error": f"Invalid style: {style}. Must be one of {list(STYLE_PROMPTS.keys())}."})
    positive_prompt = STYLE_PROMPTS[style].format(subject=subject)
    task_uuid = str(uuid.uuid4())
    request_obj = {
        "taskType": "videoInference",
        "taskUUID": task_uuid,
        "positivePrompt": positive_prompt,
        "model": model,
        "duration": duration,
        "width": width,
        "height": height,
        "numberResults": 1,
        "outputFormat": "mp4",
        "outputType": "URL",
        "fps": 30,
    }
    headers = {"Authorization": f"Bearer {os.getenv('RUNWARE_API_KEY')}", "Content-Type": "application/json"}
    RUNWARE_API_URL = os.getenv("RUNWARE_API_URL", "https://api.runware.ai/v1")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(RUNWARE_API_URL, headers=headers, json=[request_obj]) as resp:
                submit_result = await resp.text()
                try:
                    submit_result_json = await resp.json()
                    return JSONResponse(content=submit_result_json)
                except Exception:
                    return JSONResponse(
                        status_code=500,
                        content={
                            "status": "error",
                            "error": f"Failed to parse submission response: {submit_result}",
                            "taskUUID": task_uuid,
                        }
                    )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "taskUUID": task_uuid,
            }
        ) 