import replicate
import os
import sys
from typing import Union, Optional

def personalize_iconic_art_with_replicate(
    image: str,  # artwork URL
    face_image: Union[str, bytes],  # file path, file-like, or URL
    prompt: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    style: Optional[str] = None,
    num_inference_steps: Optional[int] = None,
    guidance_scale: Optional[float] = None,
    seed: Optional[int] = None,
    api_token: str = None
) -> list:
    if api_token:
        os.environ["REPLICATE_API_TOKEN"] = api_token

    def _to_file_or_url(val):
        if isinstance(val, str):
            if val.startswith("http://") or val.startswith("https://"):
                return val
            return open(val, "rb")
        return val  # assume file-like or bytes

    input = {
        "image": image,  # must be a URL for this model
        "face_image": _to_file_or_url(face_image)
    }
    if prompt is not None:
        input["prompt"] = prompt
    if negative_prompt is not None:
        input["negative_prompt"] = negative_prompt
    if style is not None:
        input["style"] = style
    if num_inference_steps is not None:
        input["num_inference_steps"] = num_inference_steps
    if guidance_scale is not None:
        input["guidance_scale"] = guidance_scale
    if seed is not None:
        input["seed"] = seed

    try:
        output = replicate.run(
            "zsxkib/instant-id:latest",
            input=input
        )
        print(f"Replicate output: {output}", file=sys.stderr)
        urls = []
        for idx, item in enumerate(output):
            print(f"Output item {idx}: type={type(item)}, value={item}", file=sys.stderr)
            url = str(item)
            if url.startswith("http://") or url.startswith("https://"):
                urls.append(url)
        print(f"Returning URLs: {urls}", file=sys.stderr)
        return urls
    except Exception as e:
        print(f"Replicate API error: {e}", file=sys.stderr)
        return [] 