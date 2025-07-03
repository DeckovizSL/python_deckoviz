from ._replicate_image_to_video import image_to_video_with_replicate
from typing import Union, Optional, IO

def generate_video_from_image(
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
    Service wrapper for image-to-video generation using Replicate.
    Returns a dict with video_url only.
    """
    return image_to_video_with_replicate(
        image=image,
        prompt=prompt,
        output_dir=output_dir,
        api_token=api_token,
        max_area=max_area,
        fast_mode=fast_mode,
        lora_scale=lora_scale,
        num_frames=num_frames,
        sample_shift=sample_shift,
        sample_steps=sample_steps,
        frames_per_second=frames_per_second,
        sample_guide_scale=sample_guide_scale
    ) 