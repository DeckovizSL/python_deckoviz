import replicate
import os
import sys
from typing import Union, Optional, IO
from io import BytesIO

def image_to_video_with_replicate(
    image: Union[str, bytes, IO],
    prompt: str,
    output_dir: str = ".",
    api_token: Optional[str] = None,
    max_area: Optional[str] = None,
    fast_mode: Optional[str] = None,
    lora_scale: Optional[float] = None,
    num_frames: Optional[int] = None,
    sample_shift: Optional[int] = None,
    sample_steps: Optional[int] = None,
    frames_per_second: Optional[int] = None,
    sample_guide_scale: Optional[int] = None
) -> dict:
    """
    Generate a video from an image using the Replicate API (wavespeedai/wan-2.1-i2v-480p).
    Returns only the video_url (no download or saving).
    """
    if api_token:
        os.environ["REPLICATE_API_TOKEN"] = api_token

    def _to_file_or_url(val):
        if hasattr(val, "read"):
            return val  # file-like object
        if isinstance(val, bytes):
            return BytesIO(val)
        if isinstance(val, str):
            if val.startswith("http://") or val.startswith("https://"):
                return val
            return open(val, "rb")
        raise TypeError(f"Unsupported type for image: {type(val)}")

    input = {
        "image": _to_file_or_url(image),
        "prompt": prompt
    }
    if max_area is not None:
        input["max_area"] = max_area
    if fast_mode is not None:
        input["fast_mode"] = fast_mode
    if lora_scale is not None:
        input["lora_scale"] = lora_scale
    if num_frames is not None:
        input["num_frames"] = num_frames
    if sample_shift is not None:
        input["sample_shift"] = sample_shift
    if sample_steps is not None:
        input["sample_steps"] = sample_steps
    if frames_per_second is not None:
        input["frames_per_second"] = frames_per_second
    if sample_guide_scale is not None:
        input["sample_guide_scale"] = sample_guide_scale

    try:
        output = replicate.run(
            "wavespeedai/wan-2.1-i2v-480p",
            input=input
        )
        print(f"Replicate output: {output}", file=sys.stderr)
        video_url = None
        if isinstance(output, str) and (output.startswith("http://") or output.startswith("https://")):
            video_url = output
        elif isinstance(output, dict) and "output" in output:
            video_url = output["output"]
        elif isinstance(output, list) and output and isinstance(output[0], str) and (output[0].startswith("http://") or output[0].startswith("https://")):
            video_url = output[0]
        return {
            "video_url": str(output)
        }
    except Exception as e:
        print(f"Replicate API error: {e}", file=sys.stderr)
        return {
            "video_url": None
        } 