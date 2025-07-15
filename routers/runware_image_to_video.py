from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Body
from fastapi.responses import JSONResponse
import aiohttp
import asyncio
import base64
import uuid
import os

router = APIRouter(tags=["runware-image-to-video"])

ALLOWED_RESOLUTIONS = [
    (1280, 720),  # landscape
    (720, 1280),  # portrait
    (720, 720),   # square
]

@router.post("/generate")
async def runware_image_to_video_generate(
    image_files: list[UploadFile] = File(..., description="Image files for key frames (ordered)"),
    positivePrompt: str = Form(...),
    duration: int = Form(...),
    width: int = Form(...),
    height: int = Form(...),
    # fps is frozen to 30 in backend, so not exposed
):
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

@router.post("/get-response")
async def runware_get_response(body: dict = Body(...)):
    """Poll Runware for the status/result of a video inference task. Accepts taskUUID in the JSON body."""
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