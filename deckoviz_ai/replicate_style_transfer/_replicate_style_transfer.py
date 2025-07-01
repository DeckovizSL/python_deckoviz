import replicate
import os
import sys
from typing import Union, Optional


def style_transfer_with_replicate(
    image: Union[str, bytes],
    image_style: Union[str, bytes],
    output_dir: str = ".",
    api_token: str = None,
    seed: Optional[int] = None,
    prompt: Optional[str] = None,
    guidance_scale: Optional[float] = None,
    style_strength: Optional[float] = None,
    negative_prompt: Optional[str] = None,
    structure_strength: Optional[float] = None,
    num_inference_steps: Optional[int] = None
) -> list:
    """
    Perform style transfer using the Replicate API.
    Args:
        image: URL or local file path or bytes for the content image.
        image_style: URL or local file path or bytes for the style image.
        output_dir: Directory to save the output images.
        api_token: Optional. Replicate API token. If not provided, uses env var.
        seed: Optional. Random seed for reproducibility.
        prompt: Optional. Prompt for the model.
        guidance_scale: Optional. Guidance scale for the model.
        style_strength: Optional. Strength of the style transfer.
        negative_prompt: Optional. Negative prompt for the model.
        structure_strength: Optional. Structure strength for the model.
        num_inference_steps: Optional. Number of inference steps.
    Returns:
        List of output file paths.
    """
    if api_token:
        os.environ["REPLICATE_API_TOKEN"] = api_token

    def _to_file_or_url(val):
        if isinstance(val, str):
            if val.startswith("http://") or val.startswith("https://"):
                return val
            return open(val, "rb")
        return val  # assume file-like or bytes

    input = {
        "image": _to_file_or_url(image),
        "image_style": _to_file_or_url(image_style)
    }
    if seed is not None:
        input["seed"] = seed
    if prompt is not None:
        input["prompt"] = prompt
    if guidance_scale is not None:
        input["guidance_scale"] = guidance_scale
    if style_strength is not None:
        input["style_strength"] = style_strength
    if negative_prompt is not None:
        input["negative_prompt"] = negative_prompt
    if structure_strength is not None:
        input["structure_strength"] = structure_strength
    if num_inference_steps is not None:
        input["num_inference_steps"] = num_inference_steps

    try:
        output = replicate.run(
            "remodela-ai/style-transfer-i:a1f3c0ec5505720e3147d66733749909976bb86ebf5a668b634b60f9d71d4359",
            input=input
        )
        print(f"Replicate output: {output}", file=sys.stderr)
        urls = []
        for idx, item in enumerate(output):
            print(f"Output item {idx}: type={type(item)}, value={item}", file=sys.stderr)
            # If item is a FileOutput, its str() is the URL
            url = str(item)
            if url.startswith("http://") or url.startswith("https://"):
                urls.append(url)
        print(f"Returning URLs: {urls}", file=sys.stderr)
        return urls
    except Exception as e:
        print(f"Replicate API error: {e}", file=sys.stderr)
        return [] 