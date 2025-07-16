from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Body
from fastapi.responses import JSONResponse
import aiohttp
import asyncio
import base64
import uuid
import os
from typing import List

router = APIRouter(tags=["runware-image-to-video"])

ALLOWED_RESOLUTIONS = [
    (1280, 720),  # landscape
    (720, 1280),  # portrait
    (720, 720),   # square
]

@router.post(
    "/generate",
    summary="Submit a video generation task to Runware (Image-to-Video)",
    response_description="Submission status and taskUUID for polling.",
    tags=["runware-image-to-video"],
)
async def runware_image_to_video_generate(
    image_files: List[UploadFile] = File(..., description="Image files for key frames (ordered; at least 1, typically 2 for first/last frame). Recommended: 2 images for best results."),
    positivePrompt: str = Form(..., description="Text prompt describing the video content. Be specific for best results."),
    duration: int = Form(..., description="Duration of the video in seconds. See model limits (e.g., 5-10s typical)."),
    width: int = Form(..., description="Width of the video. Allowed: 1280, 720."),
    height: int = Form(..., description="Height of the video. Allowed: 720, 1280."),
):
    """
    ### Runware Video Generation (Image-to-Video)
    Submit a video generation task using one or more images as keyframes and a text prompt.

    **Recommended Flow:**
    1. **POST** to `/runware-image-to-video/generate` with your images and prompt.
    2. Receive a `taskUUID` in the response.
    3. **POST** to `/runware-image-to-video/get-response` with the `taskUUID` to poll for status.
    4. When status is `success`, retrieve the `videoURL` from the response.

    **Parameters:**
    - `image_files`: List of images (UploadFile). Use 2 images for first/last frame anchoring.
    - `positivePrompt`: Text prompt describing the video.
    - `duration`: Video duration in seconds (model-dependent, e.g., 5-10s typical).
    - `width`, `height`: Video resolution. Allowed: 1280x720, 720x1280, 720x720.

    **Example Request (POSTMAN):**
    - Method: POST
    - URL: `/runware-image-to-video/generate`
    - Form-data:
        - image_files: [file1.png, file2.png]
        - positivePrompt: "A cat playing piano, cinematic, high quality"
        - duration: 6
        - width: 1280
        - height: 720

    **Example Response:**
    ```json
    {
      "data": [
        { "taskType": "videoInference", "taskUUID": "..." }
      ]
    }
    ```
    Use the `taskUUID` to poll for results.
    """
    # Validate resolution
    if (width, height) not in ALLOWED_RESOLUTIONS:
        raise HTTPException(
            status_code=400,
            detail="Only the following resolutions are supported: 1280x720, 720x1280, 720x720."
        )
    task_uuid = str(uuid.uuid4())
    try:
        # Read all image files as bytes and encode as base64
        images = [await f.read() for f in image_files]
        frame_images = []
        for idx, img in enumerate(images):
            image_b64 = base64.b64encode(img).decode("utf-8")
            frame_obj = {"inputImage": image_b64}
            if idx == 0:
                frame_obj["frame"] = "first"
            elif idx == len(images) - 1:
                frame_obj["frame"] = "last"
            frame_images.append(frame_obj)
        # Prepare the videoInference request with frozen values
        request_obj = {
            "taskType": "videoInference",
            "taskUUID": task_uuid,
            "positivePrompt": positivePrompt,
            "duration": duration,
            "width": width,
            "height": height,
            "frameImages": frame_images,
            "model": "klingai:1@1",
            "numberResults": 1,
            "outputFormat": "mp4",
            "outputType": "URL",
            "fps": 30,
        }
        headers = {"Authorization": f"Bearer {os.getenv('RUNWARE_API_KEY')}", "Content-Type": "application/json"}
        RUNWARE_API_URL = os.getenv("RUNWARE_API_URL", "https://api.runware.ai/v1")
        async with aiohttp.ClientSession() as session:
            async with session.post(RUNWARE_API_URL, headers=headers, json=[request_obj]) as resp:
                submit_result = await resp.text()
                try:
                    submit_result_json = await resp.json()
                    # If Runware returns a valid response, return it (should include taskUUID)
                    return JSONResponse(content=submit_result_json)
                except Exception:
                    # If Runware returns a non-JSON or error, return our own error but include taskUUID
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

@router.post(
    "/get-response",
    summary="Poll for video generation result/status (Runware)",
    response_description="Current status and, if ready, the video URL.",
    tags=["runware-image-to-video"],
)
async def runware_get_response(
    body: dict = Body(..., example={"taskUUID": "24cd5dff-cb81-4db5-8506-b72a9425f9d1"}, description="JSON body with the taskUUID you received from /generate. Use this endpoint to poll for completion.")
):
    """
    ### Poll for Video Generation Result (Runware)
    After submitting a video generation task, use this endpoint to check the status and retrieve the video URL when ready.

    **Recommended Flow:**
    1. Submit a task to `/runware-image-to-video/generate` and get a `taskUUID`.
    2. Poll this endpoint every few seconds with the `taskUUID` until status is `success`.
    3. On success, the response will include a `videoURL`.

    **Parameters:**
    - `taskUUID`: The UUID you received from the `/generate` endpoint.

    **Example Request (POSTMAN):**
    - Method: POST
    - URL: `/runware-image-to-video/get-response`
    - Body (raw, JSON):
      ```json
      { "taskUUID": "24cd5dff-cb81-4db5-8506-b72a9425f9d1" }
      ```

    **Example Response (Success):**
    ```json
    {
      "data": [
        {
          "taskType": "videoInference",
          "taskUUID": "24cd5dff-cb81-4db5-8506-b72a9425f9d1",
          "status": "success",
          "videoUUID": "b7db282d-2943-4f12-992f-77df3ad3ec71",
          "videoURL": "https://im.runware.ai/video/ws/0.5/vi/b7db282d-2943-4f12-992f-77df3ad3ec71.mp4",
          "cost": 0.18
        }
      ]
    }
    ```
    **Example Response (Pending):**
    ```json
    {
      "data": [
        {
          "taskType": "videoInference",
          "taskUUID": "24cd5dff-cb81-4db5-8506-b72a9425f9d1",
          "status": "pending"
        }
      ]
    }
    ```
    """
    taskUUID = body.get("taskUUID")
    if not taskUUID:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Missing taskUUID in request body."})
    RUNWARE_API_URL = os.getenv("RUNWARE_API_URL", "https://api.runware.ai/v1")
    RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")
    headers = {"Authorization": f"Bearer {RUNWARE_API_KEY}", "Content-Type": "application/json"}
    poll_obj = {"taskType": "getResponse", "taskUUID": taskUUID}
    async with aiohttp.ClientSession() as session:
        async with session.post(RUNWARE_API_URL, headers=headers, json=[poll_obj]) as poll_resp:
            poll_text = await poll_resp.text()
            try:
                poll_result = await poll_resp.json()
            except Exception as e:
                return JSONResponse(status_code=500, content={"status": "error", "error": f"Failed to parse response: {poll_text}"})
            return JSONResponse(content=poll_result) 