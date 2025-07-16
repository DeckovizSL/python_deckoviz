import os
import uuid
import aiohttp
from typing import Optional, Dict, Any
import logging

RUNWARE_API_URL = os.getenv("RUNWARE_API_URL", "https://api.runware.ai/v1")
RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")

class RunwareFluxToolsService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or RUNWARE_API_KEY
        if not self.api_key:
            raise RuntimeError("RUNWARE_API_KEY is required. Please set in environment variables.")
        self.api_url = RUNWARE_API_URL

    async def generate_flux_image(self, *, tool: str, prompt: str, image_b64: str, mask_b64: Optional[str] = None, style: Optional[str] = None, width: int = 1024, height: int = 1024, steps: int = 30) -> Dict[str, Any]:
        """
        Generate or enhance an image using Runware FLUX Tools.
        tool: one of 'fill', 'canny', 'depth', 'redux'
        prompt: positive prompt for generation
        image_b64: base64-encoded input image
        mask_b64: base64-encoded mask image (for fill/inpainting)
        style: style string (optional, used in prompt)
        width, height: output image size
        steps: inference steps
        """
        task_uuid = str(uuid.uuid4())
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        # Model selection based on tool
        if tool == "fill":
            model = "runware:102@1"
            payload = {
                "taskType": "imageInference",
                "taskUUID": task_uuid,
                "model": model,
                "positivePrompt": prompt,
                "seedImage": image_b64,
                "maskImage": mask_b64,
                "width": width,
                "height": height,
                "steps": steps
            }
        elif tool == "canny":
            model = "runware:104@1"
            payload = {
                "taskType": "imageInference",
                "taskUUID": task_uuid,
                "model": model,
                "positivePrompt": prompt,
                "seedImage": image_b64,
                "width": width,
                "height": height,
                "steps": steps
            }
        elif tool == "depth":
            model = "runware:103@1"
            payload = {
                "taskType": "imageInference",
                "taskUUID": task_uuid,
                "model": model,
                "positivePrompt": prompt,
                "seedImage": image_b64,
                "width": width,
                "height": height,
                "steps": steps
            }
        elif tool == "redux":
            # Redux uses ipAdapters and guideImage
            model = "runware:101@1"
            ip_adapter_model = "runware:105@1"
            payload = {
                "taskType": "imageInference",
                "taskUUID": task_uuid,
                "model": model,
                "positivePrompt": prompt or "__BLANK__",
                "width": width,
                "height": height,
                "steps": steps,
                "ipAdapters": [
                    {
                        "guideImage": image_b64,
                        "model": ip_adapter_model
                    }
                ]
            }
        else:
            raise ValueError(f"Unknown FLUX tool: {tool}")

        logging.warning(f"[FLUX Service] Sending payload: {payload}")
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/image/inference", json=payload, headers=headers) as resp:
                resp_text = await resp.text()
                logging.warning(f"[FLUX Service] Raw response text: {resp_text}")
                if resp.status != 200:
                    raise RuntimeError(f"Runware FLUX API error: {resp.status} {resp_text}")
                try:
                    resp_json = await resp.json()
                except Exception as e:
                    logging.error(f"[FLUX Service] Error parsing JSON: {e}")
                    return {"error": f"Failed to parse JSON: {e}", "raw": resp_text}
                logging.warning(f"[FLUX Service] Parsed response JSON: {resp_json}")
                return resp_json 