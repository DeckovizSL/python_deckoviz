import os
import uuid
import aiohttp
import asyncio
import base64
import time
from typing import List, Dict, Any

RUNWARE_API_URL = os.getenv("RUNWARE_API_URL", "https://api.runware.ai/v1")
RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")

async def generate_video_from_images(
    images: List[bytes],
    video_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handles the full video generation flow with robust logging and polling:
    1. Encodes images as base64 and embeds them in the videoInference request.
    2. Submits a videoInference task.
    3. Polls for the result and returns the video URL.
    """
    # 1. Encode images as base64 and build frameImages
    frame_images = []
    for idx, img in enumerate(images):
        image_b64 = base64.b64encode(img).decode("utf-8")
        frame_obj = {"inputImage": image_b64}
        if idx == 0:
            frame_obj["frame"] = "first"
        elif idx == len(images) - 1:
            frame_obj["frame"] = "last"
        frame_images.append(frame_obj)

    # 2. Prepare the videoInference request with frozen values
    task_uuid = str(uuid.uuid4())
    request_obj = {
        **video_params,
        "taskType": "videoInference",
        "taskUUID": task_uuid,
        "frameImages": frame_images,
        "model": "klingai:1@1",
        "numberResults": 1,
        "outputFormat": "mp4",
        "outputType": "URL",
        "fps": 30,
    }
    request_obj.pop("outputQuality", None)
    headers = {"Authorization": f"Bearer {RUNWARE_API_KEY}", "Content-Type": "application/json"}

    print(f"[Runware] Submitting videoInference task: {request_obj}")
    async with aiohttp.ClientSession() as session:
        # 3. Submit the videoInference task
        async with session.post(RUNWARE_API_URL, headers=headers, json=[request_obj]) as resp:
            submit_result = await resp.text()
            print(f"[Runware] Submission response: {submit_result}")
            if resp.status != 200:
                return {"status": "error", "error": f"Failed to submit video task: {resp.status} {submit_result}"}
            submit_result_json = None
            try:
                submit_result_json = await resp.json()
            except Exception as e:
                print(f"[Runware] Error parsing submission JSON: {e}")
                return {"status": "error", "error": f"Failed to parse submission response: {submit_result}"}
            if "errors" in submit_result_json and submit_result_json["errors"]:
                return {"status": "error", "error": submit_result_json["errors"]}

        # 4. Poll for result using getResponse
        poll_obj = {"taskType": "getResponse", "taskUUID": task_uuid}
        poll_interval = 2
        max_interval = 15
        max_wait_seconds = 3600  # 1 hour
        start_time = time.time()
        attempt = 0
        while True:
            await asyncio.sleep(poll_interval)
            attempt += 1
            elapsed = time.time() - start_time
            print(f"[Runware] Polling attempt {attempt}, interval {poll_interval}s, elapsed {elapsed:.1f}s: {poll_obj}")
            async with session.post(RUNWARE_API_URL, headers=headers, json=[poll_obj]) as poll_resp:
                poll_text = await poll_resp.text()
                print(f"[Runware] Poll response: {poll_text}")
                try:
                    poll_result = await poll_resp.json()
                except Exception as e:
                    print(f"[Runware] Error parsing poll JSON: {e}")
                    continue
                data = poll_result.get("data", [])
                errors = poll_result.get("errors", [])
                if errors:
                    error_statuses = [err.get("status") for err in errors]
                    if any(s == "error" for s in error_statuses):
                        return {"status": "error", "error": errors}
                if data:
                    status = data[0].get("status")
                    video_url = data[0].get("videoURL")
                    if status == "success" and video_url and video_url.endswith(".mp4"):
                        print(f"[Runware] Video generation successful: {video_url}")
                        return {
                            "status": "success",
                            "video_url": video_url,
                            "cost": data[0].get("cost"),
                        }
                    elif status == "success" and video_url:
                        return {"status": "error", "error": "Output is not in MP4 format."}
                    elif status == "pending":
                        print(f"[Runware] Status pending, will continue polling.")
                        pass  # keep polling
                    elif status == "error":
                        return {"status": "error", "error": data[0].get("message", "Unknown error")}
            poll_interval = min(poll_interval * 2, max_interval)
            if elapsed > max_wait_seconds:
                print(f"[Runware] Timeout waiting for video generation after {elapsed/60:.1f} minutes.")
                return {"status": "error", "error": "Timeout waiting for video generation (1 hour limit)."} 